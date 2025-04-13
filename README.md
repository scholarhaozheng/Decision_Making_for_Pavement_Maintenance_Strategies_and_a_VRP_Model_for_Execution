## Project Overview

This project is designed for processing, analyzing, and visualizing highway maintenance and repair (MR) task data.

---

## Repository Structure

- **generating_topology.py**  
  Generates the network topology from provided coordinates, milestones, and road network data. It computes task-to-task travel times and saves the resulting topology dictionary.

- **MR_package.py**  
  Serves as the main integration package that calls the milestone interpolation, data processing, decision tree, and batch topology computation scripts.

- **environment.yml**  
  A Conda environment configuration file that lists the necessary dependencies (e.g., NetworkX, osmnx, pandas, matplotlib, etc.) to ensure the project runs smoothly.

- **decision_tree_MR.py**  
  Implements a decision tree-based recommendation system that evaluates various pavement indices (PCI, RQI, RDI, SRI) alongside other parameters (road category, traffic load, pavement distress) to output maintenance recommendations.

- **processing_mission_data_and_decision_tree.py**  
  Processes data from multiple sources, such as milestone coordinates, basic route information, traffic data, and procedure requirements. It then calls the decision tree module to process maintenance tasks and outputs a comprehensive MR plan.

- **interpolate_milestones.py**  
  Interpolates and locates milestone points along the road network by reading sample Excel files (provided as examples) and using road network data obtained via OSMnx. The script generates coordinate data files and visual maps.

- **processing_mission_data.py**  
  Parses highway inspection task data, extracts and groups segment information, matches performance indices, and outputs task dictionaries for further analysis.

- **Match_Segments_And_Performance_Metrics.py**  
  Filters road segment data based on specific criteria and computes various performance metrics, including minimum values, sums, and summary statistics from the filtered results.

- **get_topology_batch_dict.py**  
  Uses OSMnx and NetworkX to compute shortest paths and distances between task points. It outputs a subgraph, a set of paths, and a mapping dictionary that relates point pair indices to their shortest path distances (saved as pickle files).

---

## Data Files and Example Formats

All the data tables (Excel files, shapefiles, text files, etc.) included in the repository are provided strictly as examples. These example files illustrate the required structure and format. They serve to demonstrate:

- The fields that each input table must contain.
- The required data types and formatting for every field.
- How to correctly fill the example data so that you can construct your own input files using these templates.

Please note that all provided tables are merely examples. When applying the project to actual data, ensure that your new files match the example formats to allow the scripts to correctly parse and process the data.

---

## Getting Started

1. **Set Up the Environment**  
   Ensure you have Conda installed. Then, run the following commands to create and activate the project environment:  
   ```
   conda env create -f environment.yml
   conda activate osm_env
   ```

2. **Prepare the Data Files**  
   - Place the sample data files in the designated directories (e.g., `xlsx`, `milestone_line_xlsx`, `shp_data`, `pkl`, `txt`).  
   - When using your own data, model the file formats after the provided examples. Make sure the field names and structures remain consistent.

3. **Run the Scripts**  
   Run `MR_package.py` to process the task data.
