import pandas as pd
import numpy as np

"""
Problem Description:

Filter the road segment data from the given Excel file based on specified conditions and calculate performance metrics and summary values from the filtered results. The detailed requirements are as follows:

Filter Criteria:
- Filter the rows that satisfy the following conditions:
  - The Route Number equals the specified `line_name`.
  - The Starting Milepost is greater than or equal to `start_kp`.
  - The Ending Milepost is less than or equal to `end_kp`.

File 1:
- Save the complete filtered results (including all columns) as File 1.
- Also, convert the File 1 data into a list of dictionaries for further processing or display.

File 2:
- Based on the filtered results, generate statistical results according to the following rules:
  For the following indicators: Damage Rate (DR), PCI, IRI, RQI, RD, RDI, WR, PWI, PB, PBI, PQI:
    - Compute the minimum value for each column (ignoring 0 and NaN values).
  For Evaluation Grade:
    - Convert the grade into a numeric representation (Excellent > Good > Average > Poor) and take the minimum value (i.e. highest priority). If all values are NaN, return None.
  For the following columns (see the `sum_cols` list below): Converted Damaged Area, Total Damaged Area, Minor Alligator Cracking, Moderate Alligator Cracking, Severe Alligator Cracking, etc.:
    - Compute the sum for each column, ignoring NaN and empty values.
  For all other unspecified columns:
    - Retain the data from the first row of the filtered results.
- Save the result as File 2, and convert it into a dictionary where:
  - The keys are the values from the "Indicator" column (e.g. Damage Rate (DR), PCI, etc.).
  - The values are the corresponding data from the "Value" column.

Return:
- file1_dict: The File 1 data as a list of dictionaries, with each row represented as a dictionary.
- file2_dict: The File 2 data as a dictionary, with the "Indicator" as the key and the "Value" as the value.
"""

def MatchSegmentsAndPerformanceMetrics(file_path, line_name, start_kp, end_kp):

    # Read the Excel file from the first sheet
    detect_indices = pd.read_excel(file_path, sheet_name=0)

    # Filter rows using the specified conditions:
    # - Route Number matches line_name
    # - Ending Milepost is greater than or equal to start_kp
    # - Starting Milepost is less than or equal to end_kp
    filtered_data = detect_indices[
        (detect_indices['Route Number'] == line_name) &
        (detect_indices['Ending Milepost'] >= start_kp) &
        (detect_indices['Starting Milepost'] <= end_kp)
    ]

    # If no rows match the criteria, find the row with the closest Starting Milepost to start_kp
    if filtered_data.empty:
        print("No matching rows found, searching for the closest matching row...")
        filtered_indices = detect_indices[detect_indices['Route Number'] == line_name]

        if not filtered_indices.empty:
            closest_idx = (abs(filtered_indices['Starting Milepost'] - start_kp)).idxmin()
            filtered_data = filtered_indices.loc[[closest_idx]]
        else:
            filtered_data = pd.DataFrame()

    # Define the list of performance indicator columns for which we will compute the minimum value.
    evaluation_cols = ['Damage Rate (DR)', 'PCI', 'IRI', 'RQI', 'RD', 'RDI', 'WR', 'PWI', 'PB', 'PBI', 'PQI']

    # Define the list of columns for which the sum needs to be calculated.
    sum_cols = [
        'Converted Damaged Area', 'Total Damaged Area', 'Minor Alligator Cracking', 'Moderate Alligator Cracking', 'Severe Alligator Cracking',
        'Minor Block Cracking', 'Severe Block Cracking', 'Minor Longitudinal Cracking', 'Severe Longitudinal Cracking',
        'Minor Transverse Cracking', 'Severe Transverse Cracking', 'Minor Potholes', 'Severe Potholes',
        'Minor Loose Material', 'Severe Loose Material', 'Minor Settlement', 'Severe Settlement',
        'Minor Rutting', 'Severe Rutting', 'Minor Waviness/Bulging', 'Severe Waviness/Bulging',
        'Seepage Oil', 'Patch', 'Block Patch', 'Strip Patch'
    ]

    # Create a copy of the filtered data
    filtered_data = filtered_data.copy()

    # Convert the specified columns to numeric data types (ignoring conversion errors by setting them to NaN)
    filtered_data.loc[:, evaluation_cols + sum_cols] = filtered_data[evaluation_cols + sum_cols].apply(pd.to_numeric,
                                                                                                       errors='coerce')
    # Compute the minimum values for each performance indicator (ignoring zeros and NaN values)
    min_values = filtered_data[evaluation_cols].replace(0, np.nan).min()

    # Map the Evaluation Grade to a numeric value for comparison.
    # The scale is: Excellent < Good < Average < Poor (lower number indicates higher priority).
    grade_mapping = {'Excellent': 1, 'Good': 2, 'Average': 3, 'Poor': 4}

    filtered_data['Evaluation Grade Numeric'] = filtered_data['Evaluation Grade'].map(grade_mapping)
    min_grade = filtered_data['Evaluation Grade Numeric'].min()
    min_grade_str = (filtered_data.loc[filtered_data['Evaluation Grade Numeric'] == min_grade, 'Evaluation Grade']
                     .iloc[0] if not np.isnan(min_grade) else None)

    # Compute the sum for each of the columns specified in sum_cols, ignoring NaN values.
    sum_values = filtered_data[sum_cols].sum()

    # Identify the remaining columns that are not included in evaluation or sum calculations.
    other_cols = [col for col in filtered_data.columns
                  if col not in evaluation_cols + sum_cols + ['Evaluation Grade', 'Evaluation Grade Numeric']]
    other_data = filtered_data[other_cols].iloc[0].to_dict() if not filtered_data.empty else {}

    # Create File 2 data as a DataFrame with two columns: Indicator and Value.
    file2_data = pd.DataFrame({
        'Indicator': evaluation_cols + ['Evaluation Grade'] + sum_cols + list(other_cols),
        'Value': list(min_values) + [min_grade_str] + list(sum_values) + [other_data.get(col, None) for col in other_cols]
    })

    # Convert File 1 data to a list of dictionaries and File 2 data to a dictionary.
    file1_dict = filtered_data.to_dict(orient='records')
    file2_dict = dict(zip(file2_data['Indicator'], file2_data['Value']))

    return file1_dict, file2_dict
