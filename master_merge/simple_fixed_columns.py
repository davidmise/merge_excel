import pandas as pd
import os
from pathlib import Path

def extract_truck_columns(excel_files, output_file="truck_master.xlsx"):
    """
    Extract only truck-related columns from Excel files
    """
    all_data = []
    
    # Define columns we want to look for
    target_columns = {
        'truck': ['truck', 'truck_no', 'truck_number', 'truck#', 'trk', 'unit', 'vehicle'],
        'location': ['location', 'gps', 'position', 'current location', 'at'],
        'status': ['status', 'condition', 'state'],
        'remarks': ['remarks', 'note', 'comment', 'observation', 'comments']
    }
    
    for file_path in excel_files:
        try:
            xls = pd.ExcelFile(file_path)
            
            for sheet_name in xls.sheet_names:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # Create a record for this sheet
                    record = {'source_file': Path(file_path).name, 'source_sheet': sheet_name}
                    
                    # Look for each target column
                    for col_type, col_names in target_columns.items():
                        found = False
                        for col in df.columns:
                            col_lower = str(col).lower()
                            for target in col_names:
                                if target in col_lower:
                                    record[col_type] = df[col].iloc[0] if len(df) > 0 else ''
                                    found = True
                                    break
                            if found:
                                break
                    
                    if 'truck' in record:  # Only add if we found a truck
                        all_data.append(record)
                        
                except:
                    continue
                    
        except:
            continue
    
    # Create final dataframe
    if all_data:
        result_df = pd.DataFrame(all_data)
        result_df.columns = ['truck_number', 'location', 'status', 'remarks', 'source_file', 'source_sheet']
        result_df.to_excel(output_file, index=False)
        print(f"Created {output_file} with {len(result_df)} records")
        return result_df
    
    return None

# Usage
files = ["tracking_report1.xlsx", "tracking_report2.xlsx"]
result = extract_truck_columns(files)