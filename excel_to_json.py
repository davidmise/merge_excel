import pandas as pd
import json
import os
from pathlib import Path

def process_excel_files(folder_path, output_folder=None, sample_rows=3):
    """
    Process all Excel files in a folder and create JSON files with column names and sample data.
    
    Args:
        folder_path: Path to the folder containing Excel files
        output_folder: Path to save JSON files (if None, saves in the same folder)
        sample_rows: Number of sample rows to extract from each sheet
    """
    
    # Create output folder if specified and doesn't exist
    if output_folder:
        os.makedirs(output_folder, exist_ok=True)
    else:
        output_folder = folder_path
    
    # Get all Excel files in the folder
    excel_extensions = ['.xlsx', '.xls', '.xlsm']
    excel_files = []
    
    for file in os.listdir(folder_path):
        if any(file.lower().endswith(ext) for ext in excel_extensions):
            excel_files.append(file)
    
    if not excel_files:
        print("No Excel files found in the specified folder.")
        return
    
    print(f"Found {len(excel_files)} Excel file(s) to process...")
    
    # Process each Excel file
    for filename in excel_files:
        file_path = os.path.join(folder_path, filename)
        print(f"\nProcessing: {filename}")
        
        try:
            # Get all sheet names
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            # Initialize dictionary to store file data
            file_data = {
                "filename": filename,
                "total_sheets": len(sheet_names),
                "sheets": {}
            }
            
            # Process each sheet
            for sheet_name in sheet_names:
                print(f"  - Processing sheet: {sheet_name}")
                
                try:
                    # Read the sheet
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # Get column names and data types
                    columns_info = []
                    for col in df.columns:
                        columns_info.append({
                            "name": str(col),
                            "dtype": str(df[col].dtype)
                        })
                    
                    # Get sample data (first few rows)
                    sample_data = df.head(sample_rows).fillna("").to_dict('records')
                    
                    # Convert any non-serializable objects to strings
                    for row in sample_data:
                        for key, value in row.items():
                            if pd.isna(value):
                                row[key] = None
                            elif hasattr(value, 'isoformat'):  # Handle datetime
                                row[key] = value.isoformat()
                            else:
                                try:
                                    # Test if JSON serializable
                                    json.dumps(value)
                                except:
                                    row[key] = str(value)
                    
                    # Store sheet information
                    file_data["sheets"][sheet_name] = {
                        "total_rows": len(df),
                        "total_columns": len(df.columns),
                        "columns": columns_info,
                        f"sample_data_first_{sample_rows}_rows": sample_data
                    }
                    
                except Exception as e:
                    print(f"    Error processing sheet {sheet_name}: {str(e)}")
                    file_data["sheets"][sheet_name] = {
                        "error": f"Failed to process sheet: {str(e)}"
                    }
            
            # Save JSON file
            json_filename = os.path.splitext(filename)[0] + '_info.json'
            json_path = os.path.join(output_folder, json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(file_data, f, indent=2, ensure_ascii=False)
            
            print(f"  ✓ Saved: {json_filename}")
            
        except Exception as e:
            print(f"  ✗ Error processing file {filename}: {str(e)}")
            
            # Create error JSON
            error_data = {
                "filename": filename,
                "error": f"Failed to process file: {str(e)}"
            }
            
            json_filename = os.path.splitext(filename)[0] + '_error.json'
            json_path = os.path.join(output_folder, json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, indent=2)

def create_summary_json(folder_path, output_file=None):
    """
    Create a summary JSON file containing information from all processed Excel files.
    """
    if output_file is None:
        output_file = os.path.join(folder_path, 'all_files_summary.json')
    
    summary = {
        "total_files_processed": 0,
        "files": []
    }
    
    # Find all generated JSON files
    json_files = [f for f in os.listdir(folder_path) if f.endswith('_info.json')]
    
    for json_file in json_files:
        json_path = os.path.join(folder_path, json_file)
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                summary["files"].append(file_data)
                summary["total_files_processed"] += 1
        except:
            pass
    
    # Save summary
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSummary saved to: {output_file}")

# Example usage
if __name__ == "__main__":
    # Set your folder path here
    folder_path = r"C:\Your\Folder\Path\Here"  # Change this to your folder path
    
    # Optional: specify output folder (if None, saves in the same folder)
    output_folder = None  # or r"C:\path\to\output\folder"
    
    # Process all Excel files
    process_excel_files(folder_path, output_folder, sample_rows=3)
    
    # Create a summary of all processed files
    create_summary_json(output_folder if output_folder else folder_path)
    
    print("\n✅ Processing complete!")