import networkx as nx
import pickle
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import osmnx as ox
import os
import pandas as pd
from pyparsing import NotAny

from decision_tree_MR import decision_tree_rule

coords_dict_path = f'pkl{os.sep}coords_dict.pkl'
with open(coords_dict_path, "rb") as file:
    coords_dict = pickle.load(file)

coords_dict_path = f'pkl{os.sep}MR_info.pkl'
with open(coords_dict_path, "rb") as file:
    MR_info = pickle.load(file)

coords_dict_path = f'pkl{os.sep}topology_dict.pkl'
with open(coords_dict_path, "rb") as file:
    topology_dict = pickle.load(file)

topology_MR = {}
MR_coords_dict={}
MR_coords_dict[0] = coords_dict[0]

processing_time_considered = True

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
    if processing_time_considered:
        travel_time_depot_to = (
                topology_dict.get(
                    (0, MR_info_value_1["des_point_index"]), 0
                )
                / 60
                / 1000
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
        if MR_info_key_1 != MR_info_key_2:  # 避免自环
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

            if processing_time_considered:
                if MR_info_value_1["left_or_right"] == "right":
                    travel_time = (
                            topology_dict.get(
                                (MR_info_value_1["des_point_index"], MR_info_value_2["ori_point_index"]), 0
                            )
                            / 60
                            / 1000
                    )
                elif MR_info_value_1["left_or_right"] == "left":
                    travel_time = (
                            topology_dict.get(
                                (MR_info_value_2["ori_point_index"], MR_info_value_1["des_point_index"]), 0
                            )
                            / 60
                            / 1000
                    )
                else:
                    travel_time = None

            topology_MR[(MR_info_key_1, MR_info_key_2)] = travel_time

MR_info_path = f'pkl{os.sep}MR_info.pkl'
topology_MR_path = f'pkl{os.sep}topology_MR_data.pkl'
MR_coords_dict_path = f'pkl{os.sep}MR_coords_dict.pkl'

with open(MR_info_path, 'wb') as file:
    pickle.dump(MR_info, file)

with open(MR_coords_dict_path, 'wb') as file:
    pickle.dump(MR_coords_dict, file)

df_topology_MR = pd.DataFrame(list(topology_MR.items()), columns=['Node Pair', 'Distance'])

output_file = f'xlsx{os.sep}topology_MR_data.xlsx'
df_topology_MR.to_excel(output_file, index=False)