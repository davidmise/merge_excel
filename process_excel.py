import pandas as pd
import json
import os
from datetime import datetime

def process_excel_files():
    """
    Process all Excel files in the current folder
    """
    
    # Use current directory
    folder_path = os.getcwd()
    
    # Create output folder with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = os.path.join(folder_path, f"excel_json_output_{timestamp}")
    os.makedirs(output_folder, exist_ok=True)
    
    # Get all Excel files
    excel_files = [f for f in os.listdir(folder_path) 
                   if f.endswith(('.xlsx', '.xls', '.xlsm'))]
    
    if not excel_files:
        print("No Excel files found in the current folder.")
        return
    
    print(f"Current folder: {folder_path}")
    print(f"Found {len(excel_files)} Excel file(s)")
    print(f"Output folder: {output_folder}\n")
    
    # Process each file
    for filename in excel_files:
        print(f"Processing: {filename}")
        file_path = os.path.join(folder_path, filename)
        
        try:
            # Read Excel file
            excel_file = pd.ExcelFile(file_path)
            
            # Prepare data structure
            file_data = {
                "filename": filename,
                "file_size": os.path.getsize(file_path),
                "last_modified": datetime.fromtimestamp(
                    os.path.getmtime(file_path)
                ).isoformat(),
                "total_sheets": len(excel_file.sheet_names),
                "sheets": {}
            }
            
            # Process each sheet
            for sheet_name in excel_file.sheet_names:
                try:
                    # Read sheet
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # Get column info
                    columns = []
                    for col in df.columns:
                        columns.append({
                            "name": str(col),
                            "dtype": str(df[col].dtype),
                            "non_null_count": int(df[col].count())
                        })
                    
                    # Get sample data (first 3 rows)
                    sample_data = df.head(3).fillna("").to_dict('records')
                    
                    # Handle special data types
                    for row in sample_data:
                        for key, value in row.items():
                            if pd.isna(value):
                                row[key] = None
                            elif hasattr(value, 'isoformat'):
                                row[key] = value.isoformat()
                            else:
                                try:
                                    json.dumps(value)
                                except:
                                    row[key] = str(value)
                    
                    # Store sheet info
                    file_data["sheets"][sheet_name] = {
                        "total_rows": len(df),
                        "total_columns": len(df.columns),
                        "columns": columns,
                        "sample_data_first_3_rows": sample_data
                    }
                    
                    print(f"  ✓ Sheet: {sheet_name} ({len(df.columns)} cols, {len(df)} rows)")
                    
                except Exception as e:
                    print(f"  ✗ Error in sheet '{sheet_name}': {str(e)}")
                    file_data["sheets"][sheet_name] = {"error": str(e)}
            
            # Save JSON file
            json_filename = filename.replace(' ', '_').replace('.', '_') + '_info.json'
            json_path = os.path.join(output_folder, json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(file_data, f, indent=2, ensure_ascii=False)
            
            print(f"  ✅ Saved: {json_filename}\n")
            
        except Exception as e:
            print(f"  ❌ Error processing file: {str(e)}\n")
    
    # Create summary
    create_summary(output_folder)
    
    print(f"\n🎉 All done! JSON files saved in: {output_folder}")

def create_summary(output_folder):
    """Create a summary of all processed files"""
    json_files = [f for f in os.listdir(output_folder) 
                  if f.endswith('_info.json')]
    
    summary = {
        "total_files": len(json_files),
        "total_sheets": 0,
        "files": []
    }
    
    for json_file in json_files:
        json_path = os.path.join(output_folder, json_file)
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                sheet_count = len(data.get('sheets', {}))
                summary['total_sheets'] += sheet_count
                summary['files'].append({
                    'filename': data['filename'],
                    'sheets': sheet_count,
                    'json_file': json_file
                })
        except:
            pass
    
    # Save summary
    summary_path = os.path.join(output_folder, 'summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"📊 Summary: {summary['total_files']} files, {summary['total_sheets']} sheets")
    print(f"📋 Summary saved to: {summary_path}")

if __name__ == "__main__":
    print("=" * 60)
    print("EXCEL TO JSON CONVERTER")
    print("=" * 60)
    process_excel_files()