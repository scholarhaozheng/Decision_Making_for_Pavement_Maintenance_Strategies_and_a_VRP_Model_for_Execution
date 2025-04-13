import itertools
import math
import pickle
import os
import matplotlib.colors as mcolors
from concurrent.futures import ThreadPoolExecutor
import osmnx as ox
import networkx as nx
from functools import lru_cache
from geopy.distance import geodesic
from tqdm import tqdm

"""
Input files:
    - shp_data/fuzhou_graphml.graphml
          Fuzhou region's OSM road network graph (GraphML format).
    - pkl/flattened_data.pkl
          A pickle file containing starting point and destination point data, where each point includes the minimum starting latitude-longitude, maximum destination latitude-longitude, and corresponding point index information.

Output files:
    - pkl/subgraph.pkl
          Subgraph extracted based on the computed shortest path relationships (pickle format).
    - pkl/paths_set.pkl
          A list of all computed paths (including new node information) (pickle format).
    - pkl/topology_dict.pkl
          A mapping dictionary of point pair indices to the corresponding shortest path lengths (pickle format).
    - pkl/coords_dict.pkl
          Coordinate information for all involved points (pickle format).

Dependencies:
    - itertools, math, pickle, os
    - matplotlib.colors
    - concurrent.futures (ThreadPoolExecutor)
    - osmnx, networkx
    - functools (lru_cache)
    - geopy.distance (geodesic)
    - tqdm

Function description:
    This script is mainly used to process the road network graph and related point data of the Fuzhou region, performing the following operations:
    1. Load the Fuzhou region's OSM road network data (GraphML format) and point data (flattened_data in pickle format).
    2. Construct a simplified directed graph (G_simple), handling duplicate edges (keeping the one with the shortest length) and self-loop edges.
    3. Using the start and end point information in the point data, compute the nearest network node for each point and determine whether a new node needs to be added (if the distance is greater than a specified threshold).
    4. For all combinations of point pairs (including between points and distribution centers), compute the shortest path and its length on the road network, and store the results in a topology dictionary.
    5. Based on the computed edge relationships, extract a subgraph and save the subgraph, the computed paths set, the topology dictionary, and the node coordinate information as pickle files for subsequent analysis or visualization.

Usage:
    Provided that the aforementioned dependency libraries are installed and the input file paths are correct, simply run this script to complete data processing, shortest path computation, and result saving.
    During execution, the script will output processing progress and related information, and finally generate multiple result files in the specified 'pkl' directory.

Notes:
    - The script uses a caching mechanism for the nearest node and shortest path calculations to improve efficiency.
    - When adding new nodes, if the actual distance between a point and the reference node exceeds the preset threshold (default is 100 meters), a new node is added to the graph and connected to the reference node.
    - Please ensure that the input files exist and are in the correct format; otherwise, the script may report errors or produce incomplete results."""

def haversine(lat1, lon1, lat2, lon2):
    R = 6371393
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@lru_cache(maxsize=None)
def get_shortest_path(graph, start, end, weight="length"):
    try:
        path = nx.shortest_path(graph, start, end, weight=weight)
        length = nx.path_weight(graph, path, weight=weight)
        return path, length
    except nx.NetworkXNoPath:
        return [], float('inf')

def add_node_if_far(graph, lat, lon, reference_node, max_distance=100):
    reference_coords = (graph.nodes[reference_node]['y'], graph.nodes[reference_node]['x'])
    target_coords = (lat, lon)
    distance = geodesic(target_coords, reference_coords).meters

    if distance > max_distance:
        new_node_id = max(graph.nodes) + 1
        graph.add_node(new_node_id, y=lat, x=lon)
        graph.add_edge(new_node_id, reference_node, length=distance)
        graph.add_edge(reference_node, new_node_id, length=distance)
        return new_node_id, new_node_id
    else:
        return None, reference_node

nearest_node_cache = {}
def get_nearest_node(graph, lon, lat):
    key = (lon, lat)
    if key not in nearest_node_cache:
        nearest_node_cache[key] = ox.nearest_nodes(graph, X=lon, Y=lat)
    return nearest_node_cache[key]

def process_point_pair(args):
    point_1, point_2, G_simple, depot_index, nearest_node_depot = args

    origin_node_1 = ox.nearest_nodes(G_simple, point_1['min_ori_longitude'], point_1['min_ori_latitude'])
    destination_node_1 = ox.nearest_nodes(G_simple, point_1['max_des_longitude'], point_1['max_des_latitude'])

    _, origin_node_1 = add_node_if_far(G_simple, point_1['min_ori_latitude'], point_1['min_ori_longitude'], origin_node_1)
    _, destination_node_1 = add_node_if_far(G_simple, point_1['max_des_latitude'], point_1['max_des_longitude'], destination_node_1)

    origin_node_2 = ox.nearest_nodes(G_simple, point_2['min_ori_longitude'], point_2['min_ori_latitude'])
    destination_node_2 = ox.nearest_nodes(G_simple, point_2['max_des_longitude'], point_2['max_des_latitude'])

    _, origin_node_2 = add_node_if_far(G_simple, point_2['min_ori_latitude'], point_2['min_ori_longitude'], origin_node_2)
    _, destination_node_2 = add_node_if_far(G_simple, point_2['max_des_latitude'], point_2['max_des_longitude'], destination_node_2)

    new_nodes = {origin_node_1, destination_node_1, origin_node_2, destination_node_2}

    coords={}
    coords[point_1['ori_point_index']] = [G_simple.nodes[origin_node_1]['x'], G_simple.nodes[origin_node_1]['y']]
    coords[point_1['des_point_index']] = [G_simple.nodes[destination_node_1]['x'], G_simple.nodes[origin_node_1]['y']]
    coords[point_2['ori_point_index']] = [G_simple.nodes[origin_node_2]['x'], G_simple.nodes[origin_node_2]['y']]
    coords[point_2['des_point_index']] = [G_simple.nodes[destination_node_2]['x'], G_simple.nodes[origin_node_2]['y']]

    new_pairs = [
        (point_1['ori_point_index'], point_2['ori_point_index'], origin_node_1, origin_node_2),
        (point_1['ori_point_index'], point_2['des_point_index'], origin_node_1, destination_node_2),
        (point_1['des_point_index'], point_2['ori_point_index'], destination_node_1, origin_node_2),
        (point_1['des_point_index'], point_2['des_point_index'], destination_node_1, destination_node_2),

        (depot_index, point_1['ori_point_index'], nearest_node_depot, origin_node_1),
        (point_1['ori_point_index'], depot_index, origin_node_1, nearest_node_depot),
        (depot_index, point_1['des_point_index'], nearest_node_depot, destination_node_1),
        (point_1['des_point_index'], depot_index, destination_node_1, nearest_node_depot),

        (depot_index, point_2['ori_point_index'], nearest_node_depot, origin_node_2),
        (point_2['ori_point_index'], depot_index, origin_node_2, nearest_node_depot),
        (depot_index, point_2['des_point_index'], nearest_node_depot, destination_node_2),
        (point_2['des_point_index'], depot_index, destination_node_2, nearest_node_depot),
    ]

    return new_nodes, new_pairs, coords

def main():
    global G_simple
    all_nodes = set()
    node_pairs = set()
    topology_dict = {}
    paths_set = {}
    coords_dict = {}

    graph = ox.io.load_graphml(f"shp_data{os.sep}fuzhou_graphml.graphml")
    with open(f'pkl{os.sep}flattened_data.pkl', 'rb') as f:
        flattened_data = pickle.load(f)

    G_simple = nx.DiGraph()
    for u, v, data in graph.edges(data=True):
        if G_simple.has_edge(u, v):
            if data['length'] < G_simple[u][v]['length']:
                G_simple.remove_edge(u, v)
                G_simple.add_edge(u, v, **data)
        else:
            G_simple.add_edge(u, v, **data)

    for node, data in graph.nodes(data=True):
        G_simple.add_node(node, **data)

    G_simple.remove_edges_from(nx.selfloop_edges(G_simple))
    G_simple.graph['crs'] = 'EPSG:4326'

    depot_lat, depot_lon = 27.95609, 116.3416259999999
    depot_index = 0
    nearest_node_depot = ox.nearest_nodes(G_simple, depot_lon, depot_lat)
    all_nodes.add(nearest_node_depot)

    coords_dict[depot_index] = [G_simple.nodes[nearest_node_depot]['x'], G_simple.nodes[nearest_node_depot]['y']]

    point_pairs = [(point_1, point_2, G_simple, depot_index, nearest_node_depot) for point_1 in flattened_data for point_2 in flattened_data]

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(tqdm(executor.map(process_point_pair, point_pairs), total=len(point_pairs), desc="计算点对最近节点"))

    for new_nodes, new_pairs, coords in results:
        all_nodes.update(new_nodes)
        for new_pair in new_pairs:
            key = (new_pair[0], new_pair[1])
            paths_set[key] = {
                'origin_node': new_pair[2],
                'destination_node': new_pair[3],
                'path': None,
                'length': None,
            }
        for key_coords, value_coords in coords.items():
            coords_dict[key_coords] = value_coords

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(tqdm(executor.map(lambda key: get_shortest_path(G_simple, paths_set[key]['origin_node'], paths_set[key]['destination_node']), list(paths_set.keys())), total=len(paths_set), desc="计算最短路径"))

    for (index_1, index_2), (path, path_length) in zip(paths_set.keys(), results):
        topology_dict[(index_1, index_2)] = path_length
        paths_set[(index_1, index_2)]['path'] = path
        paths_set[(index_1, index_2)]['length'] = path_length

    output_path = f"pkl{os.sep}G_simple.pkl"
    with open(output_path, 'wb') as f:
        pickle.dump(G_simple, f)

    for index_pairs, path_info in paths_set.items():
        path = path_info["path"]
        if len(path) == 1:
            continue
        else:
            for i, node in enumerate(path[:-1]):
                node_pairs.add((node, path[i + 1]))

    subgraph = G_simple.edge_subgraph((u, v) for (u, v) in node_pairs).copy()
    output_path = f"pkl{os.sep}subgraph.pkl"
    with open(output_path, 'wb') as f:
        pickle.dump(subgraph, f)

    paths_set_path = f'pkl{os.sep}paths_set.pkl'
    with open(paths_set_path, 'wb') as f:
        pickle.dump(paths_set, f)

    topology_dict_path = f'pkl{os.sep}topology_dict1.pkl'
    with open(topology_dict_path, 'wb') as f:
        pickle.dump(topology_dict, f)

    coords_dict_path = f'pkl{os.sep}coords_dict1.pkl'
    with open(coords_dict_path, 'wb') as f:
        pickle.dump(coords_dict, f)

if __name__ == '__main__':
    main()
