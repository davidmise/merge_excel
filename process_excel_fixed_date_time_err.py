import pandas as pd
import json
import os
from datetime import datetime, date
import numpy as np

# List of files that failed previously
FAILED_FILES = [
    '2026-1-8 GT OCEAN BC RAEDA.xlsx',
    '2026.01.09 HML TO DAR TRACKING  BRILLIANT REPORT.xlsx',
    'GT OCEAN_MV ACTION.xlsx',
    'OFFLOADING & MINES SUMMARY REPORT ON  17TH JAN  2026..xlsx',
    'Poseidon_Export Tracking Report_. 19-12-2025.xlsx',
    'Terry copy.xlsx'
]

def convert_to_serializable(obj):
    """Convert non-serializable objects to strings"""
    if isinstance(obj, (datetime, date, pd.Timestamp)):
        return obj.isoformat()
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    else:
        try:
            json.dumps(obj)
            return obj
        except (TypeError, OverflowError):
            return str(obj)

def process_failed_files():
    """Process only the files that failed previously"""
    
    folder_path = os.getcwd()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = os.path.join(folder_path, f"excel_json_output_failed_files_{timestamp}")
    os.makedirs(output_folder, exist_ok=True)
    
    print("=" * 60)
    print("PROCESSING FAILED FILES ONLY")
    print("=" * 60)
    print(f"Current folder: {folder_path}")
    print(f"Output folder: {output_folder}\n")
    
    successful = 0
    failed = 0
    
    for filename in FAILED_FILES:
        if not os.path.exists(filename):
            print(f"⚠️  File not found: {filename}")
            continue
            
        print(f"\nProcessing: {filename}")
        file_path = os.path.join(folder_path, filename)
        
        try:
            # Read Excel file
            excel_file = pd.ExcelFile(file_path)
            
            file_data = {
                "filename": filename,
                "file_size": os.path.getsize(file_path),
                "last_modified": datetime.fromtimestamp(
                    os.path.getmtime(file_path)
                ).isoformat(),
                "total_sheets": len(excel_file.sheet_names),
                "sheets": {}
            }
            
            sheet_count = 0
            for sheet_name in excel_file.sheet_names:
                try:
                    # Read sheet
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # Convert column names to strings (fix for datetime headers)
                    df.columns = df.columns.astype(str)
                    
                    # Get column info
                    columns = []
                    for col in df.columns:
                        columns.append({
                            "name": str(col),
                            "dtype": str(df[col].dtype),
                            "non_null_count": int(df[col].count())
                        })
                    
                    # Get sample data and convert to serializable format
                    sample_data = []
                    for _, row in df.head(3).iterrows():
                        row_dict = {}
                        for col, value in row.items():
                            row_dict[str(col)] = convert_to_serializable(value)
                        sample_data.append(row_dict)
                    
                    file_data["sheets"][sheet_name] = {
                        "total_rows": len(df),
                        "total_columns": len(df.columns),
                        "columns": columns,
                        "sample_data_first_3_rows": sample_data
                    }
                    
                    sheet_count += 1
                    print(f"  ✓ Sheet: {sheet_name} ({len(df.columns)} cols, {len(df)} rows)")
                    
                except Exception as e:
                    print(f"  ✗ Error in sheet '{sheet_name}': {str(e)}")
                    file_data["sheets"][sheet_name] = {"error": str(e)}
            
            # Save JSON file
            json_filename = filename.replace(' ', '_').replace('.', '_') + '_info.json'
            json_path = os.path.join(output_folder, json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(file_data, f, indent=2, default=convert_to_serializable)
            
            print(f"  ✅ Saved: {json_filename} ({sheet_count} sheets)")
            successful += 1
            
        except Exception as e:
            print(f"  ❌ Error processing file: {str(e)}")
            failed += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Files processed: {successful + failed}")
    print(f"✅ Successfully processed: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Output folder: {output_folder}")
    
    if successful > 0:
        print("\nYou can now combine these with your previous results:")
        print(f"1. Previous results: excel_json_output_20260224_124018")
        print(f"2. New results: {output_folder}")

if __name__ == "__main__":
    process_failed_files()