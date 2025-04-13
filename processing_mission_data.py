import os
import re
import pandas as pd
import pickle

from Match_Segments_And_Performance_Metrics import MatchSegmentsAndPerformanceMetrics

"""
Inputs:
    - xlsx/mission_edit.xlsx
        Contains the basic information of the tasks and the segment road condition descriptions, with fields:
        "Sequence Number", "Subproject", "Line", "Start Station", "End Station",
        "Implementation Mileage", "Technical Level", "Pavement Width", "Pavement Type", "Segment Condition", "Treatment Plan".

    - milestone_line_xlsx/milestones_coordinates.xlsx
        Mileage station coordinate data file.

    - xlsx/Detailed Testing Indicators of the City Highway Management Department.xlsx
        Detection indicator data file, used to match performance indicators for each segment.

Outputs:
    - pkl/road_MR_missions.pkl
        Saves the original task data and its detailed segment information as a pickle file.

    - pkl/new_road_MR_missions.pkl
        Saves the dictionary of mission data after grouping and matching detection indicators as a pickle file.

Description:
    This script is used to process highway detection task data, parse the task and segment condition information from Excel files,
    and match the task segments with detection indicator data. Finally, it generates two dictionaries of processed data
    and saves them as pickle files. The main functions include:
      1. Reading the task data (mission_edit.xlsx), cleaning it, and reconstructing the DataFrame structure.
      2. Reading the mileage station coordinate data (milestones_coordinates.xlsx).
      3. Parsing the “Segment Condition” description, extracting left and right side pavement condition information 
         (e.g., mild, moderate, severe cracking, etc.).
      4. Building a dictionary (road_MR_missions) based on the task data to store detailed information for each segment of each task.
      5. Grouping the segment data by left and right side conditions and calculating the total implementation mileage,
         as well as the starting and ending station numbers for each group.
      6. Calling the external module Match_Segments_And_Performance_Metrics for each segment to match detection indicator data.
      7. Finally, saving both the original data dictionary and the grouped data dictionary as pickle files.

Dependencies:
    - pandas: Used for reading Excel files, data processing, and DataFrame operations.
    - os, re: Used for file path operations and regular expression processing.
    - pickle: Used for serializing data dictionaries to files.
    - tqdm: Used to display a progress bar while processing tasks.
    - collections.defaultdict: Used for grouped data storage.
    - Match_Segments_And_Performance_Metrics (custom module):
        Used to match task segments and detection indicator data based on specified line and station range.

Usage:
    1. Ensure all input file paths are correct and that the corresponding files exist in the specified folders.
    2. Run this script. It will automatically process the data and generate two pickle files in the `pkl` folder.
    3. You can modify file paths or other parameters as needed to adapt to different data formats or requirements.

Notes:
    - Please ensure that the format of the Excel files matches the expected field names. Otherwise, you may need to adjust
      the field names or the data processing logic in the script.
    - The parsing of segment conditions relies on specific keywords (e.g., “mild”, “moderate”, “severe”, etc.) and condition
      type descriptions, so the input data must conform to this specification.
    - The external module Match_Segments_And_Performance_Metrics should be properly installed or placed in the project
      directory to ensure that its functions can be called normally.
"""

mission_path = f'xlsx{os.sep}mission_edit.xlsx'
mission_data = pd.read_excel(mission_path, sheet_name=0)

mission_data = mission_data.dropna(how='all')
mission_data.columns = mission_data.iloc[0]
mission_data = mission_data[1:].reset_index(drop=True)
mission_data.columns = [
    'Sequence Number', 'Subproject', 'Line', 'Start Station', 'End Station',
    'Implementation Mileage', 'Technical Level', 'Pavement Width', 'Pavement Type',
    'Segment Condition', 'Treatment Plan'
]

milestones_coordinates_path = f"milestone_line_xlsx{os.sep}milestones_coordinates.xlsx"
milestones_coordinates = pd.read_excel(milestones_coordinates_path, sheet_name=0)

detect_index_path = f'xlsx{os.sep}Detailed Testing Indicators of the City Highway Management Department.xlsx'

road_MR_missions = {}

def parse_condi_discribe(ori_dic=None, condi_discribe=None):
    patterns = ["mild", "moderate", "severe"]
    targets = [
        "alligator cracking", "cracks", "block cracking", "longitudinal cracks",
        "transverse cracks", "both transverse and longitudinal cracks", "rutting",
        "settlement", "corrugation", "bulging", "potholes", "raveling", "bleeding"
    ]
    regex = re.compile(rf"({'|'.join(patterns)})\s*([^{'|'.join(targets)}]*?)\s*({'|'.join(targets)})")

    if ori_dic is not None:
        condi_detail = ori_dic
    else:
        condi_detail = {}

    if pd.notna(condi_discribe):
        if "left side" in condi_discribe:
            matches = regex.findall(condi_discribe.split("left side", 1)[-1])
            condi_detail["left"] = [(match[0], match[-1]) for match in matches]
        if "right side" in condi_discribe:
            matches = regex.findall(condi_discribe.split("right side", 1)[-1])
            condi_detail["right"] = [(match[0], match[-1]) for match in matches]
        if "both sides" in condi_discribe or ("left side" not in condi_discribe and "right side" not in condi_discribe):
            matches = regex.findall(
                condi_discribe.split("both sides", 1)[-1] if "both sides" in condi_discribe else condi_discribe
            )
            condi_detail["left"] = [(match[0], match[-1]) for match in matches]
            condi_detail["right"] = [(match[0], match[-1]) for match in matches]

    return condi_detail

current_key = None
details_counter = 1

for _, row in mission_data.iterrows():
    if pd.notna(row['Sequence Number']) and pd.notna(row['Subproject']):
        current_key = int(row['Sequence Number'])
        road_MR_missions[current_key] = {
            "sub_mission": row['Subproject'],
            "MR_distance": row['Implementation Mileage'],
            "overall_condition": row['Technical Level'],
            "details": {}
        }
        details_counter = 1

    elif current_key is not None and pd.isna(row['Sequence Number']) and pd.isna(row['Subproject']):
        if pd.isna(row['Start Station']):
            detail["condi_discribe2"] = row['Segment Condition']
            detail["condi_detail"] = parse_condi_discribe(
                ori_dic=detail["condi_detail"],
                condi_discribe=row['Segment Condition']
            )
            if pd.isna(detail["MR_plan"]):
                for i in range(_, -1, -1):
                    if pd.notna(mission_data.loc[i, "Treatment Plan"]):
                        detail["MR_plan"] = mission_data.loc[i, "Treatment Plan"]
                        break
            details_counter -= 1
            road_MR_missions[current_key]["details"][details_counter] = detail
            details_counter += 1
        else:
            detail = {
                "ori_milestone": row['Start Station'],
                "des_milestone": row['End Station'],
                "MR_distance": row['Implementation Mileage'],
                "tech_grade": row['Technical Level'],
                "road_width": row['Pavement Width'],
                "road_type": row['Pavement Type'],
                "condi_discribe": row['Segment Condition'],
                "MR_plan": row['Treatment Plan'],
                "condi_detail": parse_condi_discribe(condi_discribe=row['Segment Condition'])
            }
            if pd.isna(detail["MR_plan"]):
                for i in range(_, -1, -1):
                    if pd.notna(mission_data.loc[i, "Treatment Plan"]):
                        detail["MR_plan"] = mission_data.loc[i, "Treatment Plan"]
                        break
            detail["indices"] = 1
            road_MR_missions[current_key]["details"][details_counter] = detail
            road_MR_missions[current_key]["line_name"] = row['Line']

            details_counter += 1

from collections import defaultdict
import pandas as pd

new_road_MR_missions = {}

def group_details_by_condition(details):
    grouped = defaultdict(list)

    for detail_key, detail_value in details.items():
        for condi_key, condi_value in detail_value['condi_detail'].items():
            detail_value["sub_index"] = detail_key
            grouped[condi_key].append(detail_value)

    filtered_grouped = {}
    for condi, items in grouped.items():
        items = sorted(items, key=lambda x: x['ori_milestone'])

        subgroups = []
        current_group = [items[0]]
        for i in range(1, len(items)):
            if abs(items[i]['ori_milestone'] - current_group[0]['ori_milestone']) < 4:
                current_group.append(items[i])
            else:
                subgroups.append(current_group)
                current_group = [items[i]]
        subgroups.append(current_group)

        filtered_grouped[condi] = [
            {
                "group_details": subgroup,
                "total_MR_distance": sum(detail["MR_distance"] for detail in subgroup),
                "min_ori_milestone": min(detail["ori_milestone"] for detail in subgroup),
                "max_des_milestone": max(detail["des_milestone"] for detail in subgroup),
            }
            for subgroup in subgroups
        ]
    return filtered_grouped

from tqdm import tqdm
for index_key, missions_value in tqdm(road_MR_missions.items(), desc="Processing Missions", unit="mission"):
    if "details" in missions_value:
        filtered_details = group_details_by_condition(missions_value["details"])
        for side_key, multiple_groups_value in tqdm(filtered_details.items(),
                                                    desc=f"Processing Details for {index_key}",
                                                    leave=False, unit="side"):
            for group_value in multiple_groups_value:
                for mission_details in group_value["group_details"]:
                    file1_dict, file2_dict = MatchSegmentsAndPerformanceMetrics(
                        file_path=detect_index_path,
                        line_name=missions_value['line_name'],
                        start_kp=mission_details['ori_milestone'],
                        end_kp=mission_details['des_milestone']
                    )
                    mission_details["index_details"] = file2_dict
        if filtered_details:
            new_road_MR_missions[index_key] = {
                "sub_mission": missions_value["sub_mission"],
                "overall_condition": missions_value["overall_condition"],
                "MR_distance": missions_value["MR_distance"],
                "line_name": missions_value["line_name"],
                "grouped_details": filtered_details
            }

import pickle

road_MR_missions_output_path = f'pkl{os.sep}road_MR_missions.pkl'
with open(road_MR_missions_output_path, 'wb') as f:
    pickle.dump(road_MR_missions, f)
print(f"Dictionary has been saved to the file: {road_MR_missions_output_path}")

new_road_MR_missions_output_path = f'pkl{os.sep}new_road_MR_missions.pkl'
with open(new_road_MR_missions_output_path, 'wb') as f:
    pickle.dump(new_road_MR_missions, f)
print(f"Dictionary has been saved to the file: {new_road_MR_missions_output_path}")
