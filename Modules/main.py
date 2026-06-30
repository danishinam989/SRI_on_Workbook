#!/usr/bin/env python3
"""
Excel to JSON Converter for MC Domain Weights - Final Version
Converts MC_Domain_Weights.xlsx to structured JSON format
Handles all edge cases robustly
"""

import pandas as pd
import json
import numpy as np

def clean_value(val):
    """Clean and normalize values"""
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        if np.isnan(val):
            return None
        return int(val) if val == int(val) else float(val)
    val_str = str(val).strip()
    # Check if it's a string representation of a number
    try:
        num_val = float(val_str)
        return int(num_val) if num_val == int(num_val) else num_val
    except:
        return val_str

def parse_excel_to_json(excel_file_path, output_json_path):
    """
    Parse Excel file and convert to JSON format
    
    Args:
        excel_file_path: Path to input Excel file
        output_json_path: Path to output JSON file
    """
    
    # Read the Excel file without header
    df = pd.read_excel(excel_file_path, sheet_name='Table 1', header=None)
    
    result = {}
    service_number = 1
    
    i = 0
    while i < len(df):
        row = df.iloc[i]
        
        # Check if this is a service code row (starts with 'code' in column 1)
        if clean_value(row[1]) == 'code':
            # Next row should contain the actual code and service information
            if i + 1 < len(df):
                service_row = df.iloc[i + 1]
                code = clean_value(service_row[1])
                service_name = clean_value(service_row[2])
                
                # Check if there's service group info
                service_group = None
                if len(service_row) > 4:
                    sg_label = clean_value(service_row[3])
                    if sg_label == 'Service group:':
                        service_group = clean_value(service_row[4])
                
                print(f"Processing service: {code} - {service_name}")
                
                # Skip ahead to find "Functionality levels" row
                i += 2
                found_func_levels = False
                while i < len(df) and i < i + 10:  # Search within next 10 rows
                    check_row = df.iloc[i]
                    if clean_value(check_row[1]) == 'Functionality levels':
                        found_func_levels = True
                        break
                    i += 1
                
                if not found_func_levels:
                    print(f"  Warning: Could not find 'Functionality levels' for {code}")
                    continue
                
                # Next row should be the impact header row
                if i + 1 < len(df):
                    impact_header_row = df.iloc[i + 1]
                    
                    # Get impact criteria names from columns 3-9
                    impact_criteria = []
                    for col_idx in range(3, 10):
                        if col_idx < len(impact_header_row):
                            impact_name = clean_value(impact_header_row[col_idx])
                            if impact_name and impact_name != 'IMPACTS':
                                impact_criteria.append(impact_name)
                    
                    print(f"  Impact criteria: {impact_criteria}")
                    
                    # Now parse functionality levels
                    i += 2  # Move to first level row
                    
                    functionality_levels = {}
                    impact_scores = {}
                    
                    # Initialize impact scores structure
                    for impact in impact_criteria:
                        impact_scores[impact] = {}
                    
                    # Read levels (level 0 through level 4)
                    level_count = 0
                    while i < len(df) and level_count < 10:  # Max 10 iterations for safety
                        level_row = df.iloc[i]
                        level_label = clean_value(level_row[1])
                        
                        # Check if this is a level row
                        if level_label and isinstance(level_label, str) and level_label.startswith('level'):
                            # Extract level number
                            level_num_str = level_label.replace('level', '').strip()
                            try:
                                level_num = int(level_num_str)
                            except:
                                i += 1
                                continue
                            
                            level_desc = clean_value(level_row[2])
                            
                            # Check if level description is "0" which means end of levels
                            if level_desc == 0 or level_desc == '0':
                                print(f"  Found end marker at level {level_num}")
                                i += 1
                                break
                            
                            # Get impact scores for this level
                            has_scores = False
                            for idx, impact in enumerate(impact_criteria):
                                score_col = 3 + idx
                                if score_col < len(level_row):
                                    score = clean_value(level_row[score_col])
                                    if score is not None:
                                        impact_scores[impact][f"level_{level_num}"] = score
                                        has_scores = True
                            
                            # Add functionality level description
                            if level_desc:
                                functionality_levels[f"level_{level_num}"] = level_desc
                                print(f"  Added level {level_num}: {level_desc[:50]}...")
                            elif has_scores:
                                # Level has scores but no description - use placeholder
                                functionality_levels[f"level_{level_num}"] = f"Level {level_num}"
                                print(f"  Added level {level_num} with placeholder description")
                            
                            level_count += 1
                            i += 1
                        else:
                            # No more level rows
                            break
                    
                    # Create the service entry
                    if code and service_name:
                        entry = {
                            "code": code,
                            "service": service_name,
                            "functionality_levels": functionality_levels,
                            "impact_scores": impact_scores
                        }
                        
                        if service_group:
                            entry["service_group"] = service_group
                        
                        result[str(service_number)] = entry
                        service_number += 1
                        print(f"  Successfully added service {code}\n")
                else:
                    i += 1
            else:
                i += 1
        else:
            i += 1
    
    # Write to JSON file
    with open(output_json_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(result, jsonfile, indent=4, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"Successfully converted {len(result)} services from Excel to JSON")
    print(f"Output saved to: {output_json_path}")
    print(f"{'='*60}")
    
    return result

if __name__ == "__main__":
    excel_input = "path/to/weight_excel.xlsx"
    json_output = "path/to/json_output.json"
    
    try:
        parse_excel_to_json(excel_input, json_output)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
