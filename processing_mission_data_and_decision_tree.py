import networkx as nx
import pickle
import matplotlib.pyplot as plt
import numpy as np
import osmnx as ox
import os
import pandas as pd
from pyparsing import NotAny

from decision_tree_MR import decision_tree_rule

"""
Input Files:
    1. Milestone Coordinates File:
         - Path: milestone_line_xlsx{os.sep}milestones_coordinates.xlsx
         - Content: Contains the geographic coordinates (longitude and latitude) and other related data for each milestone.
    2. Basic Route Information File:
         - Path: xlsx{os.sep}2023_Road_Route_Basic_Information_Detail_Table.xlsx
         - Content: Contains basic information such as the route number and starting/ending milestone values.
    3. Task Grouping Details Data:
         - Path: pkl{os.sep}new_road_MR_missions.pkl
         - Content: Contains the grouping and sectional details for each maintenance and repair (MR) task.
    4. Traffic Load Data File:
         - Path: xlsx{os.sep}20240515_Observatory_Station_Annual_National_Road_Survey_Data.xlsx
         - Content: Contains annual traffic flow data from observation stations, which is used to calculate traffic loads.
    5. Construction Procedure Requirements File:
         - Path: xlsx{os.sep}Need_what_procedure.xlsx
         - Content: Contains information on different construction procedures, including the related operations and processing efficiencies.
    6. Damage Type Mapping File:
         - Path: xlsx{os.sep}Damage_and_Type_Mapping.xlsx
         - Content: Used to map the original damage types to predefined pavement distress types.
    7. Topological and Coordinate Data:
         - Paths: pkl{os.sep}topology_dict.pkl and pkl{os.sep}coords_dict.pkl
         - Content: The first file stores the topological distance information between nodes, and the second stores the corresponding coordinate data.

Output Files:
    1. Flattened Task Data:
         - Pickle File: pkl{os.sep}flattened_data.pkl
         - Excel File: xlsx{os.sep}grouped_road_MR_missions.xlsx
         - Content: Integrated detailed information for each maintenance and repair task.
    2. Updated Task Grouping Data:
         - Pickle File: pkl{os.sep}road_MR_missions_all.pkl
    3. Task Information (MR_info):
         - Pickle File: pkl{os.sep}MR_info.pkl
         - Content: Stores the basic information for each maintenance and repair task (determined based on the route and construction plan).
    4. Task Topological Relationships (topology_MR):
         - Pickle File: pkl{os.sep}topology_MR.pkl
         - Excel File: xlsx{os.sep}topology_data.xlsx
         - Content: Stores the travel time/distance information between tasks as well as the transportation time to the work sites.
    5. Task Coordinates Dictionary:
         - Pickle File: pkl{os.sep}MR_coords_dict.pkl
         - Content: Stores the geographic coordinates (longitude and latitude) for each task point.

Description:
    This file is used to process road maintenance and repair (MR) task data. Its core functions include:
      - Reading raw data from multiple Excel and pickle files — including milestone coordinates, basic route information,
        traffic load data, construction procedure requirements, task grouping details, as well as topological and coordinate data.
      - Generating the optimal maintenance and repair plan for each task section based on preset decision tree rules
        (invoked via the decision_tree_MR module) and calculating the corresponding processing time.
      - Integrating and flattening the task data to build the task information (MR_info), task topological relationships (topology_MR),
        and task coordinates dictionary (MR_coords_dict).
      - Saving the results as both Excel and pickle files for subsequent analysis, scheduling optimization, and visualization.

Dependencies:
    - networkx
    - pickle
    - matplotlib
    - numpy
    - osmnx
    - os
    - pandas
    - pyparsing
    - decision_tree_MR (custom decision tree rules module)

Notes:
    - Before running, ensure that all input file paths, file names, and sheet names are correct.
    - Some data processing logic (such as for traffic load and construction procedures) might need adjustments based on actual requirements.
    - The generated pickle and Excel files provide a data foundation for subsequent analysis, scheduling optimization, and visualization.
    - Ensure that all required third-party libraries are installed and compatible with the current Python version.

================================================================================
"""

milestones_coordinates_path = f"milestone_line_xlsx{os.sep}milestones_coordinates.xlsx"
line_num_file_path = f'xlsx{os.sep}Road_Route_Basic_Information_Detail_Table.xlsx'
traffic_load_file_path = f'xlsx{os.sep}Observatory_Station_Annual_National_Road_Survey_Data.xlsx'
Needed_procedure_file = f'xlsx{os.sep}Need_what_procedure.xlsx'

milestones_coordinates = pd.read_excel(milestones_coordinates_path, sheet_name=0)
file_path = f"pkl{os.sep}new_road_MR_missions.pkl"
print_or_not = False
with open(file_path, 'rb') as file:
    new_road_MR_missions = pickle.load(file)


def process_traffic_load_data(traffic_load_file_path):
    traffic_load_data = pd.read_excel(traffic_load_file_path, sheet_name='DATA')
    traffic_load_data['line_name'] = traffic_load_data['Observation_Station_ID'].str[:4]
    traffic_load_dict = {}

    for _, row in traffic_load_data.iterrows():
        line_name_key = row['line_name']
        station_number = row['Observation_Station_ID']
        year = row['Year']

        if line_name_key not in traffic_load_dict:
            traffic_load_dict[line_name_key] = {}

        if station_number not in traffic_load_dict[line_name_key]:
            traffic_load_dict[line_name_key][station_number] = {}
            traffic_load_dict[line_name_key][station_number]["each_year"] = {}

        traffic_load_dict[line_name_key][station_number]["each_year"][year] = row.to_dict()

    for line_name_key, line_data in traffic_load_dict.items():
        for station_number, year_data in line_data.items():
            traffic_load = 0
            for year, row_data in year_data["each_year"].items():
                flow_value = (
                                     row_data.get('Large_Bus_Flow', 0) +
                                     row_data.get('Medium_Truck_Flow', 0) +
                                     row_data.get('Large_Truck_Flow', 0) +
                                     row_data.get('Extra_Large_Truck_Flow', 0) +
                                     row_data.get('Container_Flow', 0)
                             ) * 365 / 1000000

                row_data['Annual_Traffic_Load'] = flow_value
                traffic_load += flow_value

            year_data["traffic_load"] = traffic_load
            year_data["milestone"] = year_data["each_year"][year]["Station_Milestone"]

    return traffic_load_dict


traffic_load_dict = process_traffic_load_data(traffic_load_file_path)
flattened_data = []
group_index = 1
point_index = 1
for sub_mission_key, sub_mission_value in new_road_MR_missions.items():
    for left_or_right, groups in sub_mission_value["grouped_details"].items():
        for group in groups:
            target_row_min_ori = milestones_coordinates[
                milestones_coordinates['Kilometer'] == group["min_ori_milestone"]]
            min_ori_longitude = target_row_min_ori['longitude'].values[0]
            min_ori_latitude = target_row_min_ori['latitude'].values[0]
            ori_point_index = point_index
            point_index = point_index + 1

            target_row_max_des = milestones_coordinates[
                milestones_coordinates['Kilometer'] == group["max_des_milestone"]]
            max_des_longitude = target_row_max_des['longitude'].values[0]
            max_des_latitude = target_row_max_des['latitude'].values[0]
            des_point_index = point_index
            point_index = point_index + 1

            best_MR_suggestions_list = []

            for sections in group["group_details"]:
                line_num_data = pd.read_excel(line_num_file_path, header=3)
                line_num_data['Start_Milestone'] = pd.to_numeric(line_num_data[6], errors='coerce')
                line_num_data['End_Milestone'] = pd.to_numeric(line_num_data[7], errors='coerce')
                line_num_data['Route_Number'] = line_num_data[1]
                matching_line_num_row = line_num_data[
                    (line_num_data['Route_Number'] == sub_mission_value["line_name"]) &
                    (line_num_data['Start_Milestone'] <= sections["ori_milestone"]) &
                    (line_num_data['End_Milestone'] >= sections["des_milestone"])
                    ]
                if matching_line_num_row.empty:
                    df_routes_filtered = line_num_data[
                        line_num_data['Route_Number'] == sub_mission_value["line_name"]].copy()
                    df_routes_filtered['distance'] = abs(
                        df_routes_filtered['Start_Milestone'] - sections["ori_milestone"])
                    nearest_row = df_routes_filtered.sort_values('distance').iloc[0]
                    sections["line_num"] = nearest_row.to_dict()[12]
                else:
                    sections["line_num"] = matching_line_num_row.iloc[0].to_dict()[12]
                EXIST_OR_NOT = False
                closest_section = None
                closest_distance = float('inf')

                for section_key, traffic_load_section_value in traffic_load_dict[
                    sub_mission_value["line_name"]].items():
                    if ((traffic_load_section_value["milestone"] >= sections["ori_milestone"]) and
                            (traffic_load_section_value["milestone"] <= sections["des_milestone"])):
                        EXIST_OR_NOT = True
                        sections["traffic_load"] = traffic_load_section_value["traffic_load"]
                        break

                    distance = abs(traffic_load_section_value["milestone"] - sections["ori_milestone"])
                    if distance < closest_distance:
                        closest_distance = distance
                        closest_section = traffic_load_section_value

                if not EXIST_OR_NOT and closest_section:
                    sections["traffic_load"] = closest_section["traffic_load"]

                PCI = sections["index_details"]["PCI"]
                RQI = sections["index_details"]["RQI"]
                RDI = sections["index_details"]["RDI"]
                SRI = 90
                road_type = sections['tech_grade']
                if sections["tech_grade"] == "Expressway":
                    design_use_year = 15
                elif sections["tech_grade"] == "Grade 1":
                    design_use_year = 15
                elif sections["tech_grade"] == "Grade 2":
                    design_use_year = 12
                elif sections["tech_grade"] == "Grade 3":
                    design_use_year = 10
                elif sections["tech_grade"] == "Grade 4":
                    design_use_year = 8

                Traffic_Load = sections['traffic_load'] * design_use_year
                if Traffic_Load >= 50:
                    Traffic_Load_Type = "Extremely Heavy"
                elif 19 < Traffic_Load < 50:
                    Traffic_Load_Type = "Very Heavy"
                elif 8 < Traffic_Load < 19:
                    Traffic_Load_Type = "Heavy"
                elif 4 < Traffic_Load < 8:
                    Traffic_Load_Type = "Medium"
                elif Traffic_Load < 4:
                    Traffic_Load_Type = "Light"

                for key_section, value_section in sections['condi_detail'].items():
                    if value_section:
                        damage_severity = value_section[0][0]
                        damage_type = value_section[0][1]
                    else:
                        print("value_section is empty!")
                        continue

                    damage_type_mapping_file = f'xlsx{os.sep}Damage_and_Type_Mapping.xlsx'
                    damage_type_mapping_df = pd.read_excel(damage_type_mapping_file, sheet_name='Sheet1')
                    if damage_type != "Alligator Cracking":
                        if damage_severity[0] == "Medium":
                            damage_severity = "Heavy"
                    if damage_type == "Cracks":
                        damage_type = "Block Cracking"
                    Pavement_Distress_Types = damage_type_mapping_df.loc[
                        damage_type_mapping_df.iloc[:, 0] == damage_type,
                        damage_type_mapping_df.columns[1]
                    ]

                    if len(Pavement_Distress_Types.values) > 0:
                        Pavement_Distress_Type = Pavement_Distress_Types.values[0]
                    else:
                        Pavement_Distress_Type = "Block Cracking"

                    if pd.isna(RDI):
                        RDI = 90
                    if pd.isna(PCI):
                        PCI = 90
                    if pd.isna(RQI):
                        RQI = 90
                    if pd.isna(SRI):
                        SRI = 90

                    best_MR_suggestions = decision_tree_rule(PCI, RQI, RDI, SRI, road_type, Traffic_Load_Type,
                                                             Pavement_Distress_Type, damage_type, damage_severity[0],
                                                             print_or_not)

                    best_MR_suggestions_list.append(best_MR_suggestions[0])

                if len(best_MR_suggestions_list) == 0:
                    continue

                min_MR_tuple = min(best_MR_suggestions_list, key=lambda x: x[2])

            Needed_procedure_df = pd.read_excel(Needed_procedure_file)
            if isinstance(min_MR_tuple[0], tuple):
                search_string = min_MR_tuple[0][1]
            else:
                search_string = min_MR_tuple[0]
            matching_procedure_row = Needed_procedure_df[
                Needed_procedure_df.iloc[:, 0]
                .astype(str)
                .str.contains(search_string, na=False, case=False, regex=False)
            ]

            columns_to_extract = [
                "Paving", "Rolling", "Pothole_Repair", "Spraying",
                "Crushed_Stone_Spreading", "Construction", "Milling", "Other_Operations"
            ]
            filtered_columns = matching_procedure_row[columns_to_extract]
            processing_time = 2
            for col in filtered_columns.columns:
                valid_values = filtered_columns[col].dropna()
                if not valid_values.empty:
                    processing_time += group["total_MR_distance"] / valid_values.astype(float).sum()
            if min_MR_tuple[3] == "No preprocessing required":
                processing_time += 0
            else:
                processing_time += 2

            flattened_data.append({
                "main_key": sub_mission_key,
                "group_index": group_index,
                "line_name": sub_mission_value['line_name'],
                "left_or_right": left_or_right,
                "ori_point_index": ori_point_index,
                "min_ori_milestone": group["min_ori_milestone"],
                "min_ori_longitude": min_ori_longitude,
                "min_ori_latitude": min_ori_latitude,
                "des_point_index": des_point_index,
                "max_des_milestone": group["max_des_milestone"],
                "max_des_longitude": max_des_longitude,
                "max_des_latitude": max_des_latitude,
                "total_MR_distance": group["total_MR_distance"],
                "line_num": sections["line_num"],
                "MR_method": min_MR_tuple[0],
                "pre_processing": min_MR_tuple[3],
                "processing_time": processing_time
            })

            group_index = group_index + 1

output_file = f'pkl{os.sep}road_MR_missions_all.pkl'
with open(output_file, 'wb') as f:
    pickle.dump(new_road_MR_missions, f)

output_file = f'pkl{os.sep}flattened_data.pkl'
with open(output_file, 'wb') as f:
    pickle.dump(flattened_data, f)

grouped_road_MR_data = pd.DataFrame(flattened_data)
grouped_road_MR_missions_path = f'xlsx{os.sep}grouped_road_MR_missions.xlsx'
grouped_road_MR_data.to_excel(grouped_road_MR_missions_path, index=False)

print(f"Grouped mission_data saved to: {grouped_road_MR_missions_path}")

topology_dict_path = f'pkl{os.sep}topology_dict.pkl'
with open(topology_dict_path, 'rb') as file:
    topology_dict = pickle.load(file)

coords_dict_path = f'pkl{os.sep}coords_dict.pkl'
with open(coords_dict_path, "rb") as file:
    coords_dict = pickle.load(file)

MR_info = {}
topology_MR = {}
starting_index = 1
current_index = starting_index

for _, row in grouped_road_MR_data.iterrows():
    if row['line_num'] == 2:
        MR_info[current_index] = row.to_dict()
        current_index += 1
    elif row['line_num'] == 4:
        MR_info[current_index] = row.to_dict()
        current_index += 1
        MR_info[current_index] = row.to_dict()
        current_index += 1

MR_coords_dict = {}
MR_coords_dict[0] = coords_dict[0]
for MR_info_key_1, MR_info_value_1 in MR_info.items():
    MR_coords_dict[MR_info_key_1] = [MR_info_value_1["min_ori_longitude"], MR_info_value_1["min_ori_latitude"]]
    travel_time_depot_to = (
            topology_dict.get(
                (0, MR_info_value_1["des_point_index"]), 0
            )
            / 60
            / 1000
            + MR_info_value_1["processing_time"]
    )
    topology_MR[(0, MR_info_key_1)] = travel_time_depot_to

    travel_time_to_depot = (
            topology_dict.get(
                (MR_info_value_1["des_point_index"], 0), 0
            )
            / 60
            / 1000
    )
    topology_MR[(MR_info_key_1, 0)] = travel_time_to_depot
    for MR_info_key_2, MR_info_value_2 in MR_info.items():
        if MR_info_key_1 != MR_info_key_2:
            if MR_info_value_1["left_or_right"] == "right":
                travel_time = (
                        topology_dict.get(
                            (MR_info_value_1["des_point_index"], MR_info_value_2["ori_point_index"]), 0
                        )
                        / 60
                        / 1000
                        + MR_info_value_2["processing_time"]
                )
            elif MR_info_value_1["left_or_right"] == "left":
                travel_time = (
                        topology_dict.get(
                            (MR_info_value_2["ori_point_index"], MR_info_value_1["des_point_index"]), 0
                        )
                        / 60
                        / 1000
                        + MR_info_value_1["processing_time"]
                )
            else:
                travel_time = None
            topology_MR[(MR_info_key_1, MR_info_key_2)] = travel_time

MR_info_path = f'pkl{os.sep}MR_info.pkl'
topology_MR_path = f'pkl{os.sep}topology_MR.pkl'
MR_coords_dict_path = f'pkl{os.sep}MR_coords_dict.pkl'

with open(MR_info_path, 'wb') as file:
    pickle.dump(MR_info, file)

with open(topology_MR_path, 'wb') as file:
    pickle.dump(topology_MR, file)

with open(MR_coords_dict_path, 'wb') as file:
    pickle.dump(MR_coords_dict, file)

df_topology_MR = pd.DataFrame(list(topology_MR.items()), columns=['Node Pair', 'Distance'])

output_file = f'xlsx{os.sep}topology_data.xlsx'
df_topology_MR.to_excel(output_file, index=False)
