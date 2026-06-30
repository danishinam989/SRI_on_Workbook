import pandas as pd
import json

def parse_excel_to_json(excel_file):
    """
    Parse the Non-Residential Impact Weighting Factors Excel file
    into a structured JSON format.
    """
    # Read the Excel file without headers
    df = pd.read_excel(excel_file, sheet_name='Table 1', header=None)
    
    # Initialize the result structure
    result = {
        "title": df.iloc[0, 0],  # First row, first column
        "climate_zones": {}
    }
    
    # Impact categories (from the headers)
    impact_categories = [
        "Energy efficiency",
        "Energy flexibility and storage",
        "Comfort",
        "Convenience",
        "Health, well-being and accessibility",
        "Maintenance and fault prediction",
        "Information to occupants"
    ]
    
    # Domain names (the 9 categories)
    domain_names = [
        "Heating",
        "Domestic hot water",
        "Cooling",
        "Ventilation",
        "Lighting",
        "Electricity",
        "Dynamic building envelope",
        "Electric vehicle charging",
        "Monitoring and control"
    ]
    
    # Parse the data
    i = 2  # Start from row 2 (skip title and empty row)
    
    while i < len(df):
        # Check if this row contains a climate zone name
        if pd.notna(df.iloc[i, 0]) and df.iloc[i, 0] not in ["IMPACT WEIGHTINGS", "1.00"]:
            climate_zone = df.iloc[i, 0]
            
            # Initialize climate zone structure
            result["climate_zones"][climate_zone] = {
                "domain_weightings": {},
                "impact_weightings": {}
            }
            
            # Parse domain weightings (next 9 rows)
            for j, domain in enumerate(domain_names):
                domain_row = i + 1 + j
                result["climate_zones"][climate_zone]["domain_weightings"][domain] = {}
                
                # Get values for each impact category (columns 1-7)
                for k, category in enumerate(impact_categories):
                    value = df.iloc[domain_row, k + 1]
                    # Convert to float, handle 0 values
                    if pd.isna(value):
                        value = 0.0
                    else:
                        value = float(value)
                    result["climate_zones"][climate_zone]["domain_weightings"][domain][category] = value
            
            # Find the IMPACT WEIGHTINGS row
            impact_row = i + 1 + len(domain_names) + 2  # Skip domains + validation row + header
            
            # Parse impact weightings (next row after headers)
            for k, category in enumerate(impact_categories):
                value = df.iloc[impact_row + 1, k + 1]
                if pd.isna(value):
                    value = 0.0
                else:
                    value = float(value)
                result["climate_zones"][climate_zone]["impact_weightings"][category] = value
            
            # Move to next climate zone (skip past impact weightings and empty rows)
            i = impact_row + 5  # Move past impact weightings and empty rows
        else:
            i += 1
    
    return result


# Main execution
if __name__ == "__main__":
    # Input file
    excel_file = 'Non-Residential Impact Weighting Factors.xlsx'
    
    # Parse the Excel file
    print("Parsing Excel file...")
    result = parse_excel_to_json(excel_file)
    
    # Save to JSON file
    output_file = 'non_residential_impact_weighting_factors.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
    
    print(f"✓ Successfully converted to JSON!")
    print(f"✓ Output saved as: {output_file}")
    print(f"✓ Climate zones found: {list(result['climate_zones'].keys())}")
    print(f"✓ Total climate zones: {len(result['climate_zones'])}")
    
    # Display sample output
    print("\n=== SAMPLE OUTPUT ===")
    first_zone = list(result['climate_zones'].keys())[0]
    print(f"\nClimate Zone: {first_zone}")
    print(f"\nDomain Weightings (Heating):")
    print(json.dumps(result['climate_zones'][first_zone]['domain_weightings']['Heating'], indent=2))
    print(f"\nImpact Weightings:")
    print(json.dumps(result['climate_zones'][first_zone]['impact_weightings'], indent=2))
