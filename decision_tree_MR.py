import os
import pandas as pd
from pandas.io.xml import preprocess_data

"""
External input file:
    Excel file path: xlsx/Road_Surface_Preprocessing.xlsx
    Sheet name: Road_Surface_Preprocessing
    File requirements:
        - Contains a "Classification" column representing the type of pavement distress (e.g., cracking, rutting, etc.).
        - Contains a "Distress Severity" column representing the severity of the distress (e.g., Light, Moderate, Severe).
        - Contains additional columns, each named after a maintenance technique (e.g., "Fog Sealing", "Micro-Surfacing", "Overlay", etc.). 
          The cell content indicates whether preprocessing is required for that technique under different distress types and severities:
          "✓" means no preprocessing is required; "△" means preprocessing is optional; other values indicate that preprocessing is needed or no recommendation is provided.
Output result:
    Returns a list where each element is a tuple in the following format:
        (Maintenance Technique Name, (Score1, Score2, Score3), Cost, Preprocessing Recommendation Text)
    Explanation:
        - Maintenance Technique Name: The recommended technique name. It can be a simple string or a tuple 
          (if a tuple, the first element is the technique name and the second element is a detailed description).
        - Score: A triple representing the cumulative scores of each decision indicator.
        - Cost: The cost associated with the maintenance technique (numeric).
        - Preprocessing Recommendation Text: Based on the loaded Excel data and matching of distress type/severity,
          common values include "No preprocessing required", "Preprocessing optional", or "Preprocessing needed".

Input parameters:
    PCI:                 Pavement Condition Index (overall pavement surface condition).
    RQI:                 Ride Quality Index.
    RDI:                 Rut Depth Index.
    SRI:                 Surface Roughness Index.
    road_type:           Road category, e.g., "Highway", "First Class", "Second Class", "Third Class", "Fourth Class".
    Traffic_Load:        Traffic load category, e.g., "Heavy", "Moderate", "Light".
    Pavement_Distress_Types:
                         The type of pavement distress. Can be provided as a single string or as a tuple 
                         (e.g., "Mottled Surface" or ("Skid Resistance Loss", "Pavement Seepage")).
    damage_type:         Distress type, e.g., "Cracking".
    damage_severity:     Distress severity, e.g., "Light", "Moderate", "Severe".
    print_or_not:        Boolean value indicating whether to print detailed process information (True or False).

File description:
    This file implements a decision tree-based recommendation system for pavement maintenance techniques 
    using various pavement indices (PCI, RQI, RDI, SRI) and other conditions (road category, traffic load, pavement distress type, distress severity).
    Based on the given indices and parameters, the program scores each technique, combines the preprocessing data 
    with the technique cost, and outputs the optimal maintenance recommendation.

Usage example:
    # Define input parameters
    PCI = 80
    RQI = 90
    RDI = 80
    SRI = 90
    road_type = "Fourth Class"
    Traffic_Load = "Heavy"
    Pavement_Distress_Types = ("Skid Resistance Loss", "Pavement Seepage")
    damage_type = "Cracking"
    damage_severity = "Light"
    print_or_not = True

    # Call the decision tree function to get maintenance recommendations
    best_MR_suggestions = decision_tree_rule(
        PCI, RQI, RDI, SRI,
        road_type, Traffic_Load,
        Pavement_Distress_Types, damage_type,
        damage_severity, print_or_not
    )

    # Sample output:
    # [
    #     ("Fog Sealing", (1, 1, 1), 9.8, "No preprocessing required")
    # ]
"""

def load_excel(file_path, sheet_name):
    return pd.read_excel(file_path, sheet_name=sheet_name)

def decision_tree_rule(PCI, RQI, RDI, SRI, road_type, Traffic_Load,
                       Pavement_Distress_Types, damage_type, damage_severity, print_or_not):
    manager = SuggestionsManager(print_or_not)
    # The first score indicates whether the method is suitable for the road category,
    # the second indicates whether the method is appropriate for the traffic load,
    # the third indicates whether the method is applicable for the type of distress.
    PCI = int(PCI)
    RQI = int(RQI)
    RDI = int(RDI)
    SRI = int(SRI)

    if road_type == 'Highway':
        if PCI >= 93 and RDI >= 93 and SRI >= 80 and \
                (Pavement_Distress_Types == "Mottled Surface" or "Pavement Seepage" or "Asphalt Aging"):
            if (Traffic_Load == "Moderate" or Traffic_Load == "Light"):
                manager.add_suggestion("Fog Sealing", value1=1, value2=1, value3=1)
            else:
                manager.add_suggestion("Fog Sealing", value1=1, value2=0, value3=1)
        if PCI >= 90 and RDI >= 90 and \
                (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            manager.add_suggestion(("Micro-Surfacing", "Micro-Surfacing"), value1=1, value2=1, value3=1)
        if PCI >= 90 and 60 <= RDI < 90 and \
                (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            manager.add_suggestion(("Micro-Surfacing", "Micro-Surfacing (fill ruts before sealing)"), value1=1, value2=1, value3=1)
        if PCI >= 85 and RDI >= 85 and \
                (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            manager.add_suggestion(("Composite Sealing", "Stone/Fiber Sealing plus Micro-Surfacing"), value1=1, value2=1, value3=1)
        if PCI >= 88 and RDI >= 85 and \
                (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            if (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion"):
                manager.add_suggestion("Ultra-Thin Overlay", value1=1, value2=1, value3=1)
            elif (Pavement_Distress_Types == "Asphalt Aging"):
                manager.add_suggestion("Ultra-Thin Overlay", value1=1, value2=1, value3=0)
        if PCI >= 85 and RDI >= 80 and \
                (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging" or "Pavement Unevenness"):
            if (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion"):
                manager.add_suggestion("Thin Overlay", value1=1, value2=1, value3=1)
            elif (Pavement_Distress_Types == "Asphalt Aging" or "Pavement Unevenness"):
                manager.add_suggestion("Thin Overlay", value1=1, value2=1, value3=0)
        if PCI >= 80 and \
                (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging" or "Pavement Unevenness"):
            manager.add_suggestion("Overlay", value1=1, value2=1, value3=1)
        if PCI >= 83 and RDI >= 80:
            if (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion"):
                manager.add_suggestion("Sealing Overlay", value1=1, value2=1, value3=1)
            elif (Pavement_Distress_Types == "Asphalt Aging" or "Pavement Unevenness"):
                manager.add_suggestion("Sealing Overlay", value1=1, value2=1, value3=0)
        if PCI >= 85 and RDI >= 75:
            if (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Abrasion" or "Asphalt Aging"):
                manager.add_suggestion("In-situ Thermal Regeneration", value1=1, value2=1, value3=1)
            elif (Pavement_Distress_Types == "Pavement Seepage" or "Pavement Unevenness"):
                manager.add_suggestion("In-situ Thermal Regeneration", value1=1, value2=1, value3=0)
        else:
            manager.add_suggestion("Structural Rehabilitation", value1=1, value2=1, value3=1)

    elif road_type == 'First Class':
        if PCI >= 90 and RDI >= 90 and SRI >= 80 and \
                (Pavement_Distress_Types == "Mottled Surface" or "Pavement Seepage" or "Asphalt Aging"):
            if (Traffic_Load == "Moderate" or Traffic_Load == "Light"):
                manager.add_suggestion("Fog Sealing", value1=1, value2=1, value3=1)
            else:
                manager.add_suggestion("Fog Sealing", value1=1, value2=0, value3=1)
        if PCI >= 85 and RDI >= 90 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            manager.add_suggestion(("Micro-Surfacing", "Micro-Surfacing"), value1=1, value2=1, value3=1)
        if PCI >= 85 and 60 <= RDI < 90 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            manager.add_suggestion(("Micro-Surfacing", "Micro-Surfacing (fill ruts before sealing)"), value1=1, value2=1, value3=1)
        if PCI >= 80 and RDI >= 80 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            manager.add_suggestion(("Composite Sealing", "Stone/Fiber Sealing plus Micro-Surfacing"), value1=1, value2=1, value3=1)
        if PCI >= 80 and RDI >= 80 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging" or "Pavement Unevenness"):
            if (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion"):
                manager.add_suggestion("Thin Overlay", value1=1, value2=1, value3=1)
            elif (Pavement_Distress_Types == "Asphalt Aging" or "Pavement Unevenness"):
                manager.add_suggestion("Thin Overlay", value1=1, value2=1, value3=0)
        if PCI >= 83 and RDI >= 80 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            if (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion"):
                manager.add_suggestion("Ultra-Thin Overlay", value1=1, value2=1, value3=1)
            elif (Pavement_Distress_Types == "Asphalt Aging"):
                manager.add_suggestion("Ultra-Thin Overlay", value1=1, value2=1, value3=0)
        if PCI >= 75 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging" or "Pavement Unevenness"):
            manager.add_suggestion("Overlay", value1=1, value2=1, value3=1)
        if PCI >= 80 and RDI >= 80:
            if (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion"):
                manager.add_suggestion("Sealing Overlay", value1=1, value2=1, value3=1)
            elif (Pavement_Distress_Types == "Asphalt Aging" or "Pavement Unevenness"):
                manager.add_suggestion("Sealing Overlay", value1=1, value2=1, value3=0)
        if PCI >= 80 and RDI >= 70:
            if (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Abrasion" or "Asphalt Aging"):
                manager.add_suggestion("In-situ Thermal Regeneration", value1=1, value2=1, value3=1)
            elif (Pavement_Distress_Types == "Pavement Seepage" or "Pavement Unevenness"):
                manager.add_suggestion("In-situ Thermal Regeneration", value1=1, value2=1, value3=0)
        else:
            manager.add_suggestion("Structural Rehabilitation", value1=1, value2=1, value3=1)

    elif road_type == 'Second Class':
        if PCI >= 90 and RDI >= 90 and SRI >= 80 and \
                (Pavement_Distress_Types == "Mottled Surface" or "Pavement Seepage" or "Asphalt Aging"):
            if (Traffic_Load == "Moderate" or Traffic_Load == "Light"):
                manager.add_suggestion("Fog Sealing", value1=1, value2=1, value3=1)
            else:
                manager.add_suggestion("Fog Sealing", value1=1, value2=0, value3=1)
        if PCI >= 82 and RDI >= 82 and \
                (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            if (Traffic_Load == "Moderate" or Traffic_Load == "Light"):
                manager.add_suggestion("Stone-Fiber Sealing", value1=1, value2=1, value3=1)
            else:
                manager.add_suggestion("Stone-Fiber Sealing", value1=1, value2=0, value3=1)
        if PCI >= 85 and RDI >= 85 and \
                (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging") and \
                (Traffic_Load == "Heavy" or Traffic_Load == "Moderate" or Traffic_Load == "Light"):
            if (Traffic_Load == "Moderate" or Traffic_Load == "Light"):
                manager.add_suggestion("Slurry Sealing", value1=1, value2=1, value3=1)
            else:
                manager.add_suggestion("Slurry Sealing", value1=1, value2=1, value3=0)
        if PCI >= 85 and RDI >= 90 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            manager.add_suggestion(("Micro-Surfacing", "Micro-Surfacing"), value1=1, value2=1, value3=1)
        if PCI >= 85 and 60 <= RDI < 90 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            manager.add_suggestion(("Micro-Surfacing", "Micro-Surfacing (fill ruts before sealing)"), value1=1, value2=1, value3=1)
        if PCI >= 80 and RDI >= 80 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            if Traffic_Load == "Heavy" or Traffic_Load == "Moderate" or Traffic_Load == "Light":
                manager.add_suggestion(("Composite Sealing", "Stone Sealing plus Slurry Sealing"), value1=1, value2=1, value3=1)
            else:
                manager.add_suggestion(("Composite Sealing", "Stone Sealing or Fiber Sealing plus Micro-Surfacing"), value1=1, value2=1, value3=1)
        if PCI >= 80 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging" or "Pavement Unevenness"):
            if (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion"):
                manager.add_suggestion("Thin Overlay", value1=1, value2=1, value3=1)
            elif (Pavement_Distress_Types == "Asphalt Aging" or "Pavement Unevenness"):
                manager.add_suggestion("Thin Overlay", value1=1, value2=1, value3=0)
        if PCI >= 83 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            if (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion"):
                manager.add_suggestion("Ultra-Thin Overlay", value1=0, value2=1, value3=1)
            elif (Pavement_Distress_Types == "Asphalt Aging"):
                manager.add_suggestion("Ultra-Thin Overlay", value1=0, value2=1, value3=0)
        if PCI >= 75 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging" or "Pavement Unevenness"):
            manager.add_suggestion("Overlay", value1=1, value2=1, value3=1)
        if PCI >= 80:
            if (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion"):
                manager.add_suggestion("Sealing Overlay", value1=1, value2=1, value3=1)
            elif (Pavement_Distress_Types == "Asphalt Aging" or "Pavement Unevenness"):
                manager.add_suggestion("Sealing Overlay", value1=1, value2=1, value3=0)
        if PCI >= 80 and RDI >= 70:
            if (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Abrasion" or "Asphalt Aging"):
                manager.add_suggestion("In-situ Thermal Regeneration", value1=1, value2=1, value3=1)
            elif (Pavement_Distress_Types == "Pavement Seepage" or "Pavement Unevenness"):
                manager.add_suggestion("In-situ Thermal Regeneration", value1=1, value2=1, value3=0)
        else:
            manager.add_suggestion("Structural Rehabilitation", value1=1, value2=1, value3=1)

    elif road_type == 'Third Class':
        if PCI >= 85 and RDI >= 85 and \
                (Pavement_Distress_Types == "Mottled Surface" or "Pavement Seepage" or "Asphalt Aging"):
            if (Traffic_Load == "Moderate" or Traffic_Load == "Light"):
                manager.add_suggestion("Fog Sealing", value1=1, value2=1, value3=1)
            else:
                manager.add_suggestion("Fog Sealing", value1=1, value2=0, value3=1)
        if PCI >= 80 and RDI >= 80 and \
                (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            if (Traffic_Load == "Moderate" or Traffic_Load == "Light"):
                manager.add_suggestion("Stone-Fiber Sealing", value1=1, value2=1, value3=1)
            else:
                manager.add_suggestion("Stone-Fiber Sealing", value1=1, value2=0, value3=1)
        if PCI >= 80 and RDI >= 80 and \
                (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging") and \
                (Traffic_Load == "Heavy" or Traffic_Load == "Moderate" or Traffic_Load == "Light"):
            if (Traffic_Load == "Moderate" or Traffic_Load == "Light"):
                manager.add_suggestion("Slurry Sealing", value1=1, value2=1, value3=1)
            else:
                manager.add_suggestion("Slurry Sealing", value1=1, value2=1, value3=0)
        if PCI >= 80 and RDI >= 90 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            manager.add_suggestion(("Micro-Surfacing", "Micro-Surfacing"), value1=0, value2=1, value3=1)
        if PCI >= 80 and 60 <= RDI < 90 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            manager.add_suggestion(("Micro-Surfacing", "Micro-Surfacing (fill ruts before sealing)"), value1=0, value2=1, value3=1)
        if PCI >= 75 and RDI >= 75 and \
                (Traffic_Load == "Heavy" or Traffic_Load == "Moderate" or Traffic_Load == "Light") and \
                (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            manager.add_suggestion(("Composite Sealing", "Stone Sealing plus Slurry Sealing"), value1=1, value2=1, value3=1)
        if PCI >= 80 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging" or "Pavement Unevenness"):
            if (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion"):
                manager.add_suggestion("Thin Overlay", value1=1, value2=1, value3=1)
            elif (Pavement_Distress_Types == "Asphalt Aging" or "Pavement Unevenness"):
                manager.add_suggestion("Thin Overlay", value1=1, value2=1, value3=0)
        if PCI >= 80 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            if (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion"):
                manager.add_suggestion("Ultra-Thin Overlay", value1=0, value2=1, value3=1)
            elif (Pavement_Distress_Types == "Asphalt Aging"):
                manager.add_suggestion("Ultra-Thin Overlay", value1=0, value2=1, value3=0)
        if PCI >= 70 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging" or "Pavement Unevenness"):
            manager.add_suggestion("Overlay", value1=1, value2=1, value3=1)
        if PCI >= 80:
            if (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion"):
                manager.add_suggestion("Sealing Overlay", value1=1, value2=1, value3=1)
            elif (Pavement_Distress_Types == "Asphalt Aging" or "Pavement Unevenness"):
                manager.add_suggestion("Sealing Overlay", value1=1, value2=1, value3=0)
        else:
            manager.add_suggestion("Structural Rehabilitation", value1=1, value2=1, value3=1)

    elif road_type == 'Fourth Class':
        if PCI >= 85 and RDI >= 85 and \
                (Pavement_Distress_Types == "Mottled Surface" or "Pavement Seepage" or "Asphalt Aging"):
            if (Traffic_Load == "Moderate" or Traffic_Load == "Light"):
                manager.add_suggestion("Fog Sealing", value1=1, value2=1, value3=1)
            else:
                manager.add_suggestion("Fog Sealing", value1=1, value2=0, value3=1)
        if PCI >= 80 and 60 <= RDI < 90 and \
                (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            if (Traffic_Load == "Moderate" or Traffic_Load == "Light"):
                manager.add_suggestion("Stone-Fiber Sealing", value1=1, value2=1, value3=1)
            else:
                manager.add_suggestion("Stone-Fiber Sealing", value1=1, value2=0, value3=1)
        if PCI >= 80 and RDI >= 80 and \
                (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging") and \
                (Traffic_Load == "Heavy" or Traffic_Load == "Moderate" or Traffic_Load == "Light"):
            if (Traffic_Load == "Moderate" or Traffic_Load == "Light"):
                manager.add_suggestion("Slurry Sealing", value1=1, value2=1, value3=1)
            else:
                manager.add_suggestion("Slurry Sealing", value1=1, value2=1, value3=0)
        if PCI >= 80 and RDI >= 90 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            manager.add_suggestion(("Micro-Surfacing", "Micro-Surfacing"), value1=0, value2=1, value3=1)
        if PCI >= 80 and 60 <= RDI < 90 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            manager.add_suggestion(("Micro-Surfacing", "Micro-Surfacing (fill ruts before sealing)"), value1=0, value2=1, value3=1)
        if PCI >= 75 and RDI >= 75 and \
                (Traffic_Load == "Heavy" or Traffic_Load == "Moderate" or Traffic_Load == "Light") and \
                (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            manager.add_suggestion(("Composite Sealing", "Stone Sealing plus Slurry Sealing"), value1=1, value2=1, value3=1)
        if PCI >= 80 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging" or "Pavement Unevenness"):
            if (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion"):
                manager.add_suggestion("Thin Overlay", value1=1, value2=1, value3=1)
            elif (Pavement_Distress_Types == "Asphalt Aging" or "Pavement Unevenness"):
                manager.add_suggestion("Thin Overlay", value1=1, value2=1, value3=0)
        if PCI >= 80 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging"):
            if (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion"):
                manager.add_suggestion("Ultra-Thin Overlay", value1=0, value2=1, value3=1)
            elif (Pavement_Distress_Types == "Asphalt Aging"):
                manager.add_suggestion("Ultra-Thin Overlay", value1=0, value2=1, value3=0)
        if PCI >= 70 and \
            (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion" or "Asphalt Aging" or "Pavement Unevenness"):
            manager.add_suggestion("Overlay", value1=1, value2=1, value3=1)
        if PCI >= 80:
            if (Pavement_Distress_Types == "Skid Resistance Loss" or "Pavement Seepage" or "Pavement Abrasion"):
                manager.add_suggestion("Sealing Overlay", value1=1, value2=1, value3=1)
            elif (Pavement_Distress_Types == "Asphalt Aging" or "Pavement Unevenness"):
                manager.add_suggestion("Sealing Overlay", value1=1, value2=1, value3=0)
        else:
            manager.add_suggestion("Structural Rehabilitation", value1=1, value2=1, value3=1)
    else:
        manager.add_suggestion("Invalid road type or insufficient data", value1=1, value2=1, value3=1)

    # Input the costs for each maintenance technique
    manager.input_costs({
        "Fog Sealing": 9.8,
        "Stone-Fiber Sealing": 40,
        "Slurry Sealing": 30,
        "Micro-Surfacing": 22.5,
        "Composite Sealing": 30,
        "Thin Overlay": 63.37,
        "Ultra-Thin Overlay": 50,
        "Sealing Overlay": 55,
        "In-situ Thermal Regeneration": 60,
        "Overlay": 70,
        "Structural Rehabilitation": 75
    })

    file_path = f'xlsx{os.sep}Road_Surface_Preprocessing.xlsx'
    sheet_name = 'Road_Surface_Preprocessing'
    manager.load_preprocessings(file_path, sheet_name)
    best_MR_suggestions = manager.compare_MR_suggestions()
    for i, maintenance_technique_package in enumerate(best_MR_suggestions):
        maintenance_technique = maintenance_technique_package[0]
        if isinstance(maintenance_technique, tuple):
            maintenance_technique = maintenance_technique[0]
        recommendation = manager.get_maintenance_recommendation(damage_type, damage_severity, maintenance_technique)
        if recommendation == "✓":
            recommendation_text = "No preprocessing required"
        elif recommendation == "△":
            recommendation_text = "Preprocessing optional"
        else:
            recommendation_text = "Preprocessing needed"
        best_MR_suggestions[i] = best_MR_suggestions[i] + (recommendation_text,)
        if print_or_not:
            print(f"Recommendation for {damage_type} ({damage_severity}) with {maintenance_technique}: {recommendation}")

    return best_MR_suggestions

class SuggestionsManager:
    def __init__(self, print_or_not):
        self.MR_suggestions = []
        self.costs = {}
        self.preprocessing_data = None
        self.print_or_not = print_or_not

    def add_suggestion(self, name, value1=None, value2=None, value3=None):
        value1 = value1 if value1 is not None else 0
        value2 = value2 if value2 is not None else 0
        value3 = value3 if value3 is not None else 0
        self.MR_suggestions.append((name, (value1, value2, value3)))

    def update_suggestion(self, name, position, new_value):
        if position < 0 or position > 2:
            raise ValueError("The 'position' parameter must be 0, 1, or 2")
        for i, (elem_name, values) in enumerate(self.MR_suggestions):
            if elem_name == name:
                new_values = list(values)
                new_values[position] = new_value
                self.MR_suggestions[i] = (elem_name, tuple(new_values))
                return
        raise ValueError(f"Name '{name}' not found")

    def load_preprocessings(self, file_path, sheet_name):
        preprocessing_data = load_excel(file_path, sheet_name)
        self.preprocessing_data = preprocessing_data

    def input_costs(self, cost_dict):
        for name, cost in cost_dict.items():
            if name not in [s[0] for s in self.MR_suggestions]:
                self.costs[name] = cost
            self.costs[name] = cost

    def compare_MR_suggestions(self):
        if not self.MR_suggestions:
            if self.print_or_not:
                print("No suggestions available currently!")
            return
        if self.print_or_not:
            print("Current suggestions list:")
        max_sum = float('-inf')
        best_MR_suggestions = []
        for name, values in self.MR_suggestions:
            value_sum = sum(values)
            name_simplified = name
            if isinstance(name, tuple):
                name_simplified = name[0]
            cost = self.costs.get(name_simplified, float('inf'))
            if isinstance(name, tuple):
                name_simplified = name[0]
                if self.print_or_not:
                    print(f"  Name: {name_simplified} -- {name[1]}, Values: {values}, Sum: {value_sum}, Cost: {cost}")
            else:
                if self.print_or_not:
                    print(f"  Name: {name}, Values: {values}, Sum: {value_sum}, Cost: {cost}")

            if value_sum > max_sum:
                max_sum = value_sum
                best_MR_suggestions = [(name, values, cost)]
            elif value_sum == max_sum:
                best_MR_suggestions.append((name, values, cost))

        best_MR_suggestions.sort(key=lambda x: x[2])

        if self.print_or_not:
            print("\nBest suggestions with the highest cumulative score are:")
        for best_MR_suggestion in best_MR_suggestions:
            best_name, best_values, best_cost = best_MR_suggestion
            if self.print_or_not:
                if isinstance(best_name, tuple):
                    print(f"  Name: {best_name[0]} -- {best_name[1]}, Values: {best_values}, Sum: {sum(best_values)}, Cost: {best_cost}")
                else:
                    print(f"  Name: {best_name}, Values: {best_values}, Sum: {sum(best_values)}, Cost: {best_cost}")

        return best_MR_suggestions

    def get_maintenance_recommendation(self, damage_type, damage_severity, maintenance_technique):
        df = self.preprocessing_data
        # Match the rows based on the distress type and severity. The column names have been translated:
        type_rows = df[df['Classification'] == damage_type]
        severity_rows = type_rows[type_rows['Distress Severity'] == damage_severity]

        if severity_rows.empty:
            return None

        if maintenance_technique in df.columns:
            return severity_rows[maintenance_technique].values[0]

        return None
