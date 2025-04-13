import os

import pandas as pd
from shapely.geometry import Point, LineString, MultiLineString
import numpy as np
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import math
import geopandas as gpd
from matplotlib import pyplot as plt
import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt

"""
Input Files:
    • shp_data/National Roads.shp
        - The original national highways data file, which contains information such as the highway name (NAME) and number (ref).
    • milestone_line_xlsx/milestone_{line_name}.xlsx
        - The Excel file containing milestone information. In each file, the first column represents the milestone (in kilometers) used to guide the interpolation and calculation of milestone point locations along the road.
    • Online Data Acquisition
        - Download Fuzhou’s road network data using OSMnx from OpenStreetMap (an internet connection is required).

Files Serving as Both Input and Output:
    • shp_data/fuzhou_national_roads.shp
        - Saved by the filter_road() function, it contains the filtered national road network data for the Fuzhou area. Subsequent functions (such as locate_milestones()) will re-read this file for further processing.
    • National Highway Segment Files and Sorted Files:
        - For example, fuzhou_G206_roads.shp, fuzhou_G236_roads.shp, fuzhou_G320_roads.shp, etc.
          In later processing, sorted files will be generated (for example, G206_sorted.shp, G236_sorted.shp, etc.),
          and these files, once generated, will be used as input data for subsequent milestone positioning and mapping.
    • Milestone Point Data Files:
        - For example, G206_milestones.shp, G236_milestones.shp, G238_milestones.shp, G316_milestones.shp, G322_milestones.shp, G528_milestones.shp.
          These files are generated based on the milestone (kilometer marker) values from the Excel files and the sorted road data.
          They are saved as output and will also be read in later map rendering procedures.

Output Files:
    • shp_data/fuzhou_graphml_all.graphml
        - The graph data file of Fuzhou’s road network downloaded from OSMnx (GraphML format).
    • txt/National Roads.txt
        - A text file that stores all the unique national highway names (NAME field) extracted from shp_data/国道.shp.
    • txt/unique_refs.txt
        - A text file containing unique 'ref' values generated during national highway data filtering.
    • Various Shapefile Files in the shp_data Directory:
        - National highway segment files (such as fuzhou_G206_roads.shp, fuzhou_G236_roads.shp, etc.) and their processed sorted files (e.g., G206_sorted.shp, G236_sorted.shp, etc.).
        - Milestone point data files (e.g., G206_milestones.shp, 1_G206_milestones.shp, etc.), which are generated based on different project numbers and national highway names.
    • Visualization Output Images:
        - shp_data/milestones_and_lines.png
            - A composite map image displaying the national highway routes and milestone points.
        - png/Fuzhou National Roads with Milestone.pdf
            - A comprehensive map showing Fuzhou’s national highways along with all milestone points; it can be used for further analysis or presentation.
    • milestone_line_xlsx/milestones_coordinates.xlsx
        - An Excel file that exports the coordinate information of all milestone points (including source, kilometer marker, longitude, and latitude) for subsequent data analysis and record-keeping.

Description:
    This file is used for the processing and visualization of Fuzhou (Jiangxi Province) national highway data. Its main functions include downloading, filtering, interpolating milestone points along the roads, sorting and merging road segments, and finally generating maps.
    The program reads the original input data, generates intermediate results, and saves them as new files. Some files are used as both input and output in later processing (e.g., re-reading processed files).

Main Functions:
    1. Download Fuzhou’s Road Network via OSMnx:
       - Downloads Fuzhou’s road network data from OpenStreetMap using OSMnx and saves it as a GraphML file.
    2. Extract and Filter National Highway Data:
       - Reads the original national highway data and extracts highway names and numbers for filtering and processing.
    3. Convert Half-Width Characters to Full-Width:
       - Converts characters from half-width to full-width for Chinese labels.
    4. Interpolate and Locate Milestone Points:
       - Uses geographic coordinate calculations for distance and azimuth, combined with the kilometer markers from the Excel files, to interpolate and locate milestone points along the road routes.
    5. Sort and (if needed) Merge Road Segments:
       - Sorts road segments by the latitude of the starting point and, if necessary, merges them, to facilitate accurate milestone positioning and subsequent analysis.
    6. Map Generation:
       - Generates maps displaying the national highways and milestone points, and exports an Excel file containing milestone coordinate information.

Processing Workflow:
    1. save_fuzhou_graphml():
       - Uses OSMnx to download Fuzhou’s road network and saves it as shp_data/fuzhou_graphml_all.graphml.
    2. national_roads_allocation(line_name):
       - Extracts national highway names from shp_data/国道.shp and saves the unique names to txt/国道线路.txt for reference and further processing.
    3. filter_road(line_name):
       - When Get_national is True, uses the road data downloaded by OSMnx to generate shp_data/fuzhou_national_roads.shp (output).
         When Get_national is False, reads this file as input to generate specific national highway segment files (e.g., fuzhou_G206_roads.shp).
    4. locate_milestones(line_name, project_index):
       - Reads milestone information from milestone_line_xlsx/milestone_{line_name}.xlsx as input, and in conjunction with the sorted national highway segment data (e.g., G206_sorted.shp), generates milestone point files (e.g., G206_milestones.shp).
         These files are saved as output and will be used as input in later mapping stages.
    5. plot_milestones_and_lines(line_name, project_index):
       - Reads the sorted national highway data and milestone point data, then generates and saves a composite map image (shp_data/milestones_and_lines.png) displaying both.
    6. visualizing_National_Roads_with_Milestone(lines_or_projects):
       - Integrates the national road network (shp_data/fuzhou_national_roads.shp) with multiple project milestone datasets,
         draws a comprehensive map, saves it as png/Fuzhou National Roads with Milestone.pdf, and exports all milestone coordinates to milestone_line_xlsx/milestones_coordinates.xlsx.

Dependencies:
    - Python Libraries: os, pandas, numpy, matplotlib, shapely, geopy, math, geopandas, osmnx
    - Input files must be placed in the corresponding directories: shp_data, txt, milestone_line_xlsx.
"""


def save_fuzhou_graphml():
    place_name = "Fuzhou, Jiangxi, China"
    G = ox.graph_from_place(place_name, network_type='drive')
    G = ox.graph_from_place(place_name)
    ox.save_graphml(G, filepath=f"shp_data{os.sep}fuzhou_graphml_all.graphml")
    """graph = ox.graph_from_place(place_name, network_type='all')"""

def filter_refs(ref):
    if isinstance(ref, str):
        ref_parts = ref.split(";")
        return "G206" in ref_parts or set(["G316", "G206"]).issubset(ref_parts)
    return False

def halfwidth_to_fullwidth(text):
    result = []
    for char in text:
        if 33 <= ord(char) <= 126:
            result.append(chr(ord(char) + 0xFEE0))
        else:
            result.append(char)
    return ''.join(result)

def national_roads_allocation(line_name):
    national_roads = gpd.read_file(f"shp_data{os.sep}National Roads.shp")
    print(national_roads.columns)
    unique_refs = national_roads['NAME'].dropna().unique()
    unique_refs = sorted(unique_refs)
    output_file = f"txt{os.sep}National Roads.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("Unique 'ref' Values in National Roads\n")
        f.write("=" * 50 + "\n")
        for ref in unique_refs:
            f.write(f"{ref}\n")


    fullwidth_line_name = halfwidth_to_fullwidth(line_name)
    selected_roads = national_roads[national_roads['NAME'] == f"{halfwidth_to_fullwidth(line_name)}国道"]
    fig, ax = plt.subplots(figsize=(10, 8))
    national_roads.plot(ax=ax, color='lightgrey', linewidth=0.5, label='All Roads')
    selected_roads.plot(ax=ax, color='red', linewidth=2, label='Selected Road')
    plt.legend()
    plt.title(f"{line_name}国道和所有国道分布", fontsize=16)
    plt.show()


def filter_road(line_name):
    Get_national = False
    if Get_national:
        place_name = "Fuzhou, Jiangxi, China"
        graph = ox.graph_from_place(place_name, network_type='all')
        nodes, edges = ox.graph_to_gdfs(graph)
        national_roads = edges[edges['highway'].isin(['trunk', 'primary'])]
        print(national_roads.dtypes)
        for col in national_roads.columns:
            if national_roads[col].apply(lambda x: isinstance(x, list)).any():
                national_roads[col] = national_roads[col].apply(lambda x: str(x) if isinstance(x, list) else x)
        national_roads.to_file(f"shp_data{os.sep}fuzhou_national_roads.shp")
        unique_refs = national_roads['ref'].dropna().unique()
        unique_refs = sorted(unique_refs)
        output_file = f"txt{os.sep}unique_refs.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("Unique 'ref' Values in National Roads\n")
            f.write("=" * 50 + "\n")
            for ref in unique_refs:
                f.write(f"{ref}\n")
        print(f"Unique 'ref' values have been saved to {output_file}")
        print("Here are the unique 'ref' values:")
        print(unique_refs)
    else:
        national_roads = gpd.read_file(f"shp_data{os.sep}fuzhou_national_roads.shp")
        if line_name=="G206":
            filtered_roads = national_roads[national_roads['ref'].apply(filter_refs)]
            output_file = f"shp_data{os.sep}filtered_roads_G206_and_G316-G206.shp"
            filtered_roads.to_file(output_file)
            print(f"Filtered roads have been saved to {output_file}")
            fig, ax = plt.subplots(figsize=(50, 40))
            filtered_roads.plot(ax=ax, linewidth=2, color='blue', alpha=0.5, label=f'Filtered Roads {line_name}')
            national_roads.plot(ax=ax, linewidth=1, color='gray', alpha=0.5, label='National Roads (Background)')
            ax.set_title("Filtered Roads on National Roads Background (Fuzhou, Jiangxi)", fontsize=16)
            ax.legend()
            plt.show()
        elif line_name=="none":
            nan_roads = national_roads[national_roads['ref'].isna()]
            nan_roads.to_file(f"shp_data{os.sep}fuzhou_nan_roads.shp")
            nan_roads_gdf = gpd.read_file(f"shp_data{os.sep}fuzhou_nan_roads.shp")
            fig, ax = plt.subplots(figsize=(12, 12))
            nan_roads.plot(ax=ax, linewidth=2, color='blue', alpha=0.7, label=f'Filtered Roads {line_name}')
            national_roads.plot(ax=ax, linewidth=1, color='gray', alpha=0.5, label='National Roads (Background)')
            nan_roads_gdf.plot(ax=ax, linewidth=3, color='green', alpha=0.7, label='NaN Roads')
        else:
            selected_roads = national_roads[national_roads['ref'] == line_name]
            selected_roads.to_file(f"shp_data{os.sep}fuzhou_{line_name}_roads.shp")
            national_roads_gdf = gpd.read_file(f"shp_data{os.sep}fuzhou_national_roads.shp")
            selected_roads_gdf = gpd.read_file(f"fuzhou_{line_name}_roads.shp")

            fig, ax = plt.subplots(figsize=(12, 12))
            national_roads_gdf.plot(ax=ax, linewidth=2, color='red', alpha=0.7, label='National Roads')
            selected_roads_gdf.plot(ax=ax, linewidth=3, color='blue', alpha=0.7, label=f'{line_name} Road')

            #nan_roads = national_roads[national_roads['ref'].isna()]
            #nan_roads.to_file(f"shp_data{os.sep}fuzhou_nan_roads.shp")
            #nan_roads = gpd.read_file(f"shp_data{os.sep}fuzhou_nan_roads.shp")
            #nan_roads.plot(ax=ax, linewidth=2, color='green', alpha=0.7, label=f'Filtered Roads {line_name}')

            """selected_roads2 = national_roads[national_roads['ref'] == "G320"]
            selected_roads2.to_file(f"shp_data{os.sep}fuzhou_G320_roads.shp")
            selected_roads2.plot(ax=ax, linewidth=3, color='green', alpha=0.7, label=f'G320 Road')"""

            ax.set_title(f"National Roads, {line_name} in Fuzhou, Jiangxi", fontsize=16)
            ax.legend()
            plt.show()

def haversine(lat1, lon1, lat2, lon2):
    R = 6371393
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def destination_point(lat1, lon1, distance, bearing):
    R = 6371393
    delta = distance / R
    theta = math.radians(bearing)
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)

    lat2 = math.asin(math.sin(lat1) * math.cos(delta) + math.cos(lat1) * math.sin(delta) * math.cos(theta))
    lon2 = lon1 + math.atan2(math.sin(theta) * math.sin(delta) * math.cos(lat1),
                             math.cos(delta) - math.sin(lat1) * math.sin(lat2))

    return math.degrees(lat2), math.degrees(lon2)

def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1, lat2 = map(math.radians, [lat1, lat2])
    delta_lon = math.radians(lon2 - lon1)
    x = math.sin(delta_lon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360

def interpolate_milestones(total_distance, line, distance_km):
    milestones = []
    total_distance_new = total_distance
    for i in range(len(line.coords) - 1):
        start_point = Point(line.coords[i])
        end_point = Point(line.coords[i+1])
        segment_distance = geodesic((start_point.y, start_point.x), (end_point.y, end_point.x)).kilometers
        total_distance_new += segment_distance

    distance_contains_in_route = total_distance
    for i in range(len(line.coords) - 1):
        start_point = Point(line.coords[i])
        end_point = Point(line.coords[i + 1])
        segment_distance = geodesic((start_point.y, start_point.x), (end_point.y, end_point.x)).kilometers
        distance_contains_in_route += segment_distance
        distance_km_flag = False
        segment_distance = haversine(start_point.y, start_point.x, end_point.y, end_point.x)/1000
        bearing = calculate_bearing(start_point.y, start_point.x, end_point.y, end_point.x)

        if distance_contains_in_route >= distance_km and not distance_km_flag:
            distance_to_start =  distance_km - distance_contains_in_route + segment_distance
            start_lat, start_lon = destination_point(start_point.y, start_point.x, distance_to_start, bearing)
            distance_km_flag = True

    if distance_km_flag:
        milestones.append((distance_km, (start_lat, start_lon)))

    return distance_km_flag, total_distance_new, milestones

def sort_lines_by_latitude(gdf):
    sorted_lines = []
    for _, row in gdf.iterrows():
        line = row.geometry
        if isinstance(line, LineString):
            start_lat = line.coords[0][1]
            end_lat = line.coords[-1][1]
            if start_lat>end_lat:
                sorted_lines.append((line, start_lat, end_lat))
            elif start_lat<end_lat:
                sorted_lines.append((line, end_lat, start_lat))
        elif isinstance(line, MultiLineString):
            for l in line:
                start_lat = l.coords[0][1]
                end_lat = l.coords[-1][1]
                sorted_lines.append((l, start_lat, end_lat))

    sorted_lines.sort(key=lambda x: x[1], reverse=True)

    sorted_geometry = [line[0] for line in sorted_lines]
    sorted_gdf = gpd.GeoDataFrame(geometry=sorted_geometry, crs=gdf.crs)
    return sorted_gdf


def merging_lines(gdf_main, gdf_sub):
    distance_list = []
    lat_sorted_lines = []
    start_lon = 0
    end_lon = 0
    for _, row in gdf_main.iterrows():
        line = row.geometry
        if start_lon==0:
            start_lon = line.coords[0][0]
            end_lon = line.coords[-1][0]
            start_lat = line.coords[0][1]
            end_lat = line.coords[-1][1]
            last_start_lon = start_lon
            last_end_lon = end_lon
            last_start_lat = start_lat
            last_end_lat = end_lat
        else:
            last_start_lon = start_lon
            last_end_lon = end_lon
            last_start_lat = start_lat
            last_end_lat = end_lat
            start_lon = line.coords[0][0]
            end_lon = line.coords[-1][0]
            start_lat = line.coords[0][1]
            end_lat = line.coords[-1][1]

        distances = [
            abs(last_start_lon - start_lon),
            abs(last_end_lon - end_lon),
            abs(last_start_lon - end_lon),
            abs(last_end_lon - start_lon)
        ]

        min_distance = min(distances)
        min_index = distances.index(min_distance)
        lon_pairs = [((last_start_lon, last_start_lat), (start_lon, start_lat)),
            ((last_end_lon, last_end_lat), (end_lon, end_lat)),
            ((last_start_lon, last_start_lat), (end_lon, end_lat)),
            ((last_end_lon, last_end_lat), (start_lon, start_lat))]

        if min_distance>0.05:
            distance_list.append({
                'min_distance': min_distance,
                'geometry': Point(lon_pairs[min_index][0])
            })

            distance_list.append({
                'min_distance': min_distance,
                'geometry': Point(lon_pairs[min_index][1])
            })

        lat_sorted_lines.append((line, start_lat, end_lat))

    G320_roads_gdf = gpd.read_file(f"shp_data{os.sep}fuzhou_G236_roads.shp")
    G236_roads_gdf = gpd.read_file(f"shp_data{os.sep}fuzhou_G320_roads.shp")
    distance_list.sort(key=lambda x: x['min_distance'], reverse=True)

    distance_list_gdf = gpd.GeoDataFrame(distance_list, crs=G320_roads_gdf.crs)

    fig, ax = plt.subplots(figsize=(40, 30))
    G320_roads_gdf.plot(ax=ax, color='blue', linewidth=10, figsize=(40, 30), label="Lines")
    G236_roads_gdf.plot(ax=ax, color='green', linewidth=10, figsize=(40, 30), label="Lines")

    x = distance_list_gdf.geometry.x
    y = distance_list_gdf.geometry.y
    ax.scatter(x, y, color='red', s=500, label='Milestone Points', zorder=5)

    plt.legend()
    plt.title("Lines and Points")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.grid()
    plt.show()

    for _, row in gdf_sub.iterrows():
        line = row.geometry
        start_lon = line.coords[0][0]
        end_lon = line.coords[-1][0]
        start_lat = line.coords[0][1]
        end_lat = line.coords[-1][1]
        if distance_list[1]["geometry"].x < start_lon < distance_list[0]["geometry"].x:
            lat_sorted_lines.append((line, start_lat, end_lat))

    lat_sorted_lines.sort(key=lambda x: x[1], reverse=True)

    sorted_geometry = [line[0] for line in lat_sorted_lines]
    sorted_gdf = gpd.GeoDataFrame(geometry=sorted_geometry, crs=gdf_main.crs)
    return sorted_gdf


def locate_milestones(line_name, project_index):
    if project_index==False:
        milestone_df = pd.read_excel(f"milestone_line_xlsx{os.sep}milestone_{line_name}.xlsx", header=None)
    else:
        milestone_df = pd.read_excel(f"milestone_line_xlsx{os.sep}{project_index}_{line_name}.xlsx", header=None)

    if line_name=="G206":
        gdf = gpd.read_file(f"shp_data{os.sep}filtered_roads_G206_and_G316-G206.shp")
        gdf_sorted = sort_lines_by_latitude(gdf)
        gdf_sorted.to_file(f"shp_data{os.sep}{line_name}_sorted.shp")
    elif line_name=="G236":
        gdf = gpd.read_file(f"shp_data{os.sep}fuzhou_G236_roads.shp")
        gdf_sorted = sort_lines_by_latitude(gdf)
        gdf_sorted.to_file(f"shp_data{os.sep}{line_name}_sorted.shp")
    else:
        gdf = gpd.read_file(f"shp_data{os.sep}fuzhou_{line_name}_roads.shp")
        gdf_sorted = sort_lines_by_latitude(gdf)
        gdf_sorted.to_file(f"shp_data{os.sep}{line_name}_sorted.shp")

    milestone_points = []
    for _, row in milestone_df.iterrows():
        distance_km = row.iloc[0]
        if line_name=="G206":
            total_distance = 1635
        elif line_name=="G236":
            total_distance = 447
        elif line_name=="G238":
            total_distance = 117
        elif line_name=="G316":
            total_distance = 467
        elif line_name=="G322":
            total_distance = 572
        elif line_name=="G528":
            total_distance = 694
        for _, line_row in gdf_sorted.iterrows():
            geometry = line_row.geometry
            distance_km_flag, total_distance_new, milestones = interpolate_milestones(total_distance, geometry, distance_km)
            total_distance = total_distance_new
            if distance_km_flag:
                break
        for km, point in milestones:
            milestone_points.append({
                'Kilometer': km,
                'geometry': Point(point[1], point[0])
            })
    milestone_gdf = gpd.GeoDataFrame(milestone_points, crs=gdf.crs)

    if project_index==False:
        milestone_gdf.to_file(f"shp_data{os.sep}{line_name}_milestones.shp")
    else:
        milestone_gdf.to_file(f"shp_data{os.sep}{project_index}_{line_name}_milestones.shp")


def plot_milestones_and_lines(line_name, project_index):
    gdf_sorted = gpd.read_file(f"shp_data{os.sep}{line_name}_sorted.shp")
    if project_index==False:
        milestone_gdf = gpd.read_file(f"shp_data{os.sep}{line_name}_milestones.shp")
    else:
        milestone_gdf = gpd.read_file(f"shp_data{os.sep}{project_index}_{line_name}_milestones.shp")

    fig, ax = plt.subplots(figsize=(25, 20))
    gdf_sorted.plot(ax=ax, color='blue', linewidth=5, label=f'{line_name} Road Line')

    x = milestone_gdf.geometry.x
    y = milestone_gdf.geometry.y
    ax.scatter(x, y, color='red', s=250, label='Milestone Points', zorder=5)
    plt.legend()
    plt.title(f"{line_name} milestones_and_lines_project{project_index}")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()


import os
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pandas as pd


def visualizing_National_Roads_with_Milestone(lines_or_projects):
    national_roads = gpd.read_file(f"shp_data{os.sep}fuzhou_national_roads.shp")

    if lines_or_projects == "lines":
        milestone_files = [
            f"shp_data{os.sep}G528_milestones.shp",
            f"shp_data{os.sep}G206_milestones.shp",
            f"shp_data{os.sep}G238_milestones.shp",
            f"shp_data{os.sep}G316_milestones.shp",
            f"shp_data{os.sep}G322_milestones.shp"
        ]
    else:
        milestone_files = [
            f"shp_data{os.sep}1_G206_milestones.shp",
            f"shp_data{os.sep}2_G206_milestones.shp",
            f"shp_data{os.sep}3_G206_milestones.shp",
            f"shp_data{os.sep}4_G206_milestones.shp",
            f"shp_data{os.sep}5_G206_milestones.shp",
            f"shp_data{os.sep}6_G236_milestones.shp",
            f"shp_data{os.sep}7_G236_milestones.shp",
            f"shp_data{os.sep}8_G238_milestones.shp",
            f"shp_data{os.sep}9_G238_milestones.shp",
            f"shp_data{os.sep}10_G316_milestones.shp",
            f"shp_data{os.sep}11_G316_milestones.shp",
            f"shp_data{os.sep}12_G316_milestones.shp",
            f"shp_data{os.sep}13_G322_milestones.shp",
            f"shp_data{os.sep}14_G322_milestones.shp",
            f"shp_data{os.sep}15_G322_milestones.shp",
            f"shp_data{os.sep}16_G528_milestones.shp"
        ]


    milestones_gdfs = []

    for path in milestone_files:
        gdf = gpd.read_file(path)
        gdf['source'] = os.path.basename(path).replace("_milestones", "").split('.')[0]
        milestones_gdfs.append(gdf)

    milestones_merged = gpd.GeoDataFrame(pd.concat(milestones_gdfs, ignore_index=True))

    import matplotlib.colors as mcolors
    import numpy as np

    all_colors = list(mcolors.XKCD_COLORS.values())

    def is_dark_color(rgb):
        r, g, b = mcolors.to_rgb(rgb)
        brightness = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return brightness < 0.85

    def color_distance(c1, c2):
        r1, g1, b1 = mcolors.to_rgb(c1)
        r2, g2, b2 = mcolors.to_rgb(c2)
        return np.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)

    def select_distinct_colors(colors, min_distance=0.43):
        selected_colors = []
        for color in colors:
            if all(color_distance(color, c) > min_distance for c in selected_colors):
                selected_colors.append(color)
        return selected_colors

    dark_colors = [color for color in all_colors if is_dark_color(color)]
    distinct_dark_colors = select_distinct_colors(dark_colors, min_distance=0.43)

    color_map = {source: distinct_dark_colors[i % len(distinct_dark_colors)] for i, source in enumerate(milestones_merged['source'].unique())}

    fig, ax = plt.subplots(figsize=(16, 10))

    national_roads.plot(ax=ax, color='lightgray', linewidth=1, label='Trunk')

    for source, group in milestones_merged.groupby('source'):
        group.plot(ax=ax, color=color_map[source], markersize=20, label=source)

    legend = plt.legend(title="Milestone Groups", loc=3, ncol=2, prop = {'size':8})
    legend.set_title("Milestone Groups")

    plt.title("Fuzhou National Roads with Milestones")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.grid(True)
    plt.show()

    fig.savefig(f"png{os.sep}Fuzhou National Roads with Milestone.pdf", dpi=600)

    milestones_merged['Kilometer'] = milestones_merged['Kilometer']
    milestones_merged['longitude'] = milestones_merged.geometry.x
    milestones_merged['latitude'] = milestones_merged.geometry.y

    export_data = milestones_merged[['source', 'Kilometer', 'longitude', 'latitude']]

    export_data.to_excel(f"milestone_line_xlsx{os.sep}milestones_coordinates.xlsx", index=False)

    print("Coordinates exported to 'milestones_coordinates.xlsx'.")


for project_index, line_name in (('1', 'G206'),('2', 'G206'),('3', 'G206'),('4', 'G206'),('5', 'G206')
                                ,('6', 'G236'),('7', 'G236'),('8', 'G238'),('9', 'G238'),('10', 'G316')
                                ,('11', 'G316'),('12', 'G316'),('13', 'G322'),('14', 'G322'),('15', 'G322')
                                ,('16', 'G528')):

    #national_roads_allocation(line_name)
    #filter_road(line_name)
    #locate_milestones(line_name,project_index)
    plot_milestones_and_lines(line_name, project_index)

# visualizing_National_Roads_with_Milestone("projects")

