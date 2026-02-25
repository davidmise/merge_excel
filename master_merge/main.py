import pandas as pd
import os
from pathlib import Path
import warnings
from datetime import datetime
import numpy as np
from collections import defaultdict

warnings.filterwarnings('ignore')

class ExcelMerger:
    def __init__(self, input_dir=None, output_path="master_file.xlsx"):
        """
        Initialize Excel Merger
        
        Args:
            input_dir: Directory containing Excel files (optional)
            output_path: Path for the merged master file
        """
        self.input_dir = input_dir
        self.output_path = output_path
        self.column_mappings = {}
        self.standardized_columns = {}
        
    def find_excel_files(self, directory=None):
        """
        Find all Excel files in the specified directory
        
        Args:
            directory: Directory to search (uses self.input_dir if None)
            
        Returns:
            List of Excel file paths
        """
        if directory is None:
            directory = self.input_dir
            
        if not directory:
            raise ValueError("No directory specified")
            
        excel_extensions = ['.xlsx', '.xls', '.xlsm', '.xlsb']
        excel_files = []
        
        for ext in excel_extensions:
            excel_files.extend(Path(directory).glob(f"*{ext}"))
            
        return [str(f) for f in excel_files if f.is_file()]
    
    def analyze_column(self, column_name):
        """
        Analyze and standardize column names for better matching
        
        Args:
            column_name: Original column name
            
        Returns:
            Standardized column name for matching
        """
        if pd.isna(column_name):
            return ""
            
        # Convert to string and standardize
        col_str = str(column_name).strip().lower()
        
        # Remove common prefixes/suffixes and standardize
        replacements = {
            'truck': 'truck',
            'vehicle': 'truck',
            'unit': 'truck',
            'truck_no': 'truck_number',
            'truck_nbr': 'truck_number',
            'truck_num': 'truck_number',
            'truck#': 'truck_number',
            'trk': 'truck',
            'loc': 'location',
            'gps': 'location',
            'position': 'location',
            'coord': 'location',
            'lat': 'latitude',
            'lon': 'longitude',
            'long': 'longitude',
            'status': 'status',
            'state': 'status',
            'condition': 'status',
            'date': 'date',
            'time': 'time',
            'timestamp': 'datetime',
            'driver': 'driver',
            'operator': 'driver',
            'load': 'load',
            'cargo': 'load',
            'weight': 'weight',
            'destination': 'destination',
            'dest': 'destination',
            'origin': 'origin',
            'src': 'origin',
            'speed': 'speed',
            'velocity': 'speed',
            'fuel': 'fuel',
            'mileage': 'mileage',
            'odometer': 'mileage',
            'temp': 'temperature',
            'temperature': 'temperature',
        }
        
        # Try to match with standardized names
        for key, value in replacements.items():
            if key in col_str:
                return value
        
        # Return cleaned original
        return col_str
    
    def extract_dataframes(self, excel_files):
        """
        Extract dataframes from all Excel files and worksheets
        
        Args:
            excel_files: List of Excel file paths
            
        Returns:
            List of dictionaries with file info and dataframes
        """
        all_data = []
        
        for file_path in excel_files:
            try:
                # Read all sheets
                xls = pd.ExcelFile(file_path)
                sheet_names = xls.sheet_names
                
                for sheet_name in sheet_names:
                    try:
                        # Try reading with different parameters
                        df = pd.read_excel(
                            file_path, 
                            sheet_name=sheet_name,
                            engine='openpyxl'
                        )
                        
                        # Skip empty dataframes
                        if df.empty or df.shape[0] == 0:
                            continue
                            
                        # Clean column names
                        df.columns = [str(col).strip() for col in df.columns]
                        
                        # Analyze and standardize column names for this sheet
                        standardized_cols = {}
                        for col in df.columns:
                            std_col = self.analyze_column(col)
                            if std_col:
                                standardized_cols[col] = std_col
                        
                        all_data.append({
                            'file_path': file_path,
                            'sheet_name': sheet_name,
                            'original_columns': df.columns.tolist(),
                            'standardized_columns': standardized_cols,
                            'dataframe': df,
                            'row_count': len(df)
                        })
                        
                        print(f"✓ Loaded: {Path(file_path).name} - Sheet: {sheet_name} ({len(df)} rows)")
                        
                    except Exception as e:
                        print(f"✗ Error reading sheet {sheet_name} in {file_path}: {str(e)}")
                        
            except Exception as e:
                print(f"✗ Error processing file {file_path}: {str(e)}")
        
        return all_data
    
    def create_column_mapping(self, data_info_list):
        """
        Create intelligent column mapping across all files
        
        Args:
            data_info_list: List of data dictionaries
            
        Returns:
            Column mapping dictionary
        """
        # Collect all standardized column names
        all_std_columns = defaultdict(list)
        
        for data_info in data_info_list:
            for orig_col, std_col in data_info['standardized_columns'].items():
                all_std_columns[std_col].append((data_info['file_path'], data_info['sheet_name'], orig_col))
        
        # Create mapping
        column_mapping = {}
        for std_col, occurrences in all_std_columns.items():
            if len(occurrences) > 0:
                # Get the most common original column name
                original_columns = [occ[2] for occ in occurrences]
                most_common = max(set(original_columns), key=original_columns.count)
                column_mapping[std_col] = most_common
        
        print(f"\nDetected {len(column_mapping)} unique standardized columns")
        return column_mapping
    
    def merge_dataframes(self, data_info_list, column_mapping):
        """
        Merge all dataframes using the column mapping
        
        Args:
            data_info_list: List of data dictionaries
            column_mapping: Column mapping dictionary
            
        Returns:
            Merged dataframe
        """
        merged_data = []
        
        for data_info in data_info_list:
            df = data_info['dataframe'].copy()
            
            # Create a new dataframe with standardized columns
            standardized_df = pd.DataFrame()
            
            for std_col, orig_col in column_mapping.items():
                # Try to find this column in the current dataframe
                found = False
                
                # Check exact match first
                if orig_col in df.columns:
                    standardized_df[std_col] = df[orig_col].copy()
                    found = True
                else:
                    # Try to find similar column
                    for df_col in df.columns:
                        if self.analyze_column(df_col) == std_col:
                            standardized_df[std_col] = df[df_col].copy()
                            found = True
                            break
                
                # If not found, add empty column
                if not found:
                    standardized_df[std_col] = np.nan
            
            # Add source information
            standardized_df['source_file'] = Path(data_info['file_path']).name
            standardized_df['source_sheet'] = data_info['sheet_name']
            standardized_df['merge_timestamp'] = datetime.now()
            
            merged_data.append(standardized_df)
        
        # Concatenate all dataframes
        if merged_data:
            master_df = pd.concat(merged_data, ignore_index=True)
            
            # Remove exact duplicates
            initial_count = len(master_df)
            
            # Identify columns for deduplication (excluding source info)
            data_columns = [col for col in master_df.columns 
                          if col not in ['source_file', 'source_sheet', 'merge_timestamp']]
            
            if len(data_columns) > 0:
                master_df = master_df.drop_duplicates(subset=data_columns, keep='first')
                duplicates_removed = initial_count - len(master_df)
                print(f"Removed {duplicates_removed} duplicate records")
            
            return master_df
        else:
            return pd.DataFrame()
    
    def generate_summary_report(self, master_df, data_info_list):
        """
        Generate a summary report of the merge process
        
        Args:
            master_df: Merged dataframe
            data_info_list: Original data information
            
        Returns:
            Summary statistics dictionary
        """
        summary = {
            'total_files_processed': len(set(info['file_path'] for info in data_info_list)),
            'total_sheets_processed': len(data_info_list),
            'total_rows_before_merge': sum(info['row_count'] for info in data_info_list),
            'total_rows_after_merge': len(master_df),
            'unique_columns_found': len(master_df.columns) if not master_df.empty else 0,
            'merge_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # File-specific summary
        file_summary = {}
        for info in data_info_list:
            filename = Path(info['file_path']).name
            if filename not in file_summary:
                file_summary[filename] = {
                    'sheets': [],
                    'total_rows': 0
                }
            file_summary[filename]['sheets'].append(info['sheet_name'])
            file_summary[filename]['total_rows'] += info['row_count']
        
        summary['file_details'] = file_summary
        
        return summary
    
    def export_to_excel(self, master_df, summary):
        """
        Export merged data to Excel with multiple sheets
        
        Args:
            master_df: Merged dataframe
            summary: Summary statistics
        """
        with pd.ExcelWriter(self.output_path, engine='openpyxl') as writer:
            # Write main data
            if not master_df.empty:
                master_df.to_excel(writer, sheet_name='Master_Data', index=False)
            
            # Write summary
            summary_df = pd.DataFrame([summary])
            summary_df.to_excel(writer, sheet_name='Merge_Summary', index=False)
            
            # Write column mapping info
            mapping_df = pd.DataFrame(
                list(self.column_mappings.items()), 
                columns=['Standardized_Name', 'Original_Name']
            )
            mapping_df.to_excel(writer, sheet_name='Column_Mapping', index=False)
            
            # Write file details
            file_details = []
            for filename, details in summary.get('file_details', {}).items():
                file_details.append({
                    'File_Name': filename,
                    'Sheets': ', '.join(details['sheets']),
                    'Total_Rows': details['total_rows']
                })
            
            if file_details:
                file_details_df = pd.DataFrame(file_details)
                file_details_df.to_excel(writer, sheet_name='File_Details', index=False)
        
        print(f"\n✅ Master file created: {self.output_path}")
        print(f"   Total rows: {summary['total_rows_after_merge']}")
        print(f"   Total columns: {summary['unique_columns_found']}")
    
    def merge_excel_files(self, excel_files=None, directory=None):
        """
        Main method to merge Excel files
        
        Args:
            excel_files: List of specific Excel files to merge (optional)
            directory: Directory to search for Excel files (optional)
            
        Returns:
            Merged dataframe and summary
        """
        print("=" * 60)
        print("EXCEL FILES MERGER - TRUCK DATA CONSOLIDATION")
        print("=" * 60)
        
        # Get Excel files
        if excel_files is None:
            if directory:
                self.input_dir = directory
            excel_files = self.find_excel_files()
        
        if not excel_files:
            print("No Excel files found to process!")
            return None, None
        
        print(f"\nFound {len(excel_files)} Excel file(s):")
        for file in excel_files:
            print(f"  • {Path(file).name}")
        
        # Extract data from all files and sheets
        print("\n" + "-" * 60)
        print("EXTRACTING DATA FROM FILES AND SHEETS...")
        data_info_list = self.extract_dataframes(excel_files)
        
        if not data_info_list:
            print("No valid data found in the files!")
            return None, None
        
        # Create column mapping
        print("\n" + "-" * 60)
        print("ANALYZING COLUMNS AND CREATING MAPPING...")
        self.column_mappings = self.create_column_mapping(data_info_list)
        
        # Print column mapping
        print("\nColumn Mapping (Standardized → Original):")
        for std_col, orig_col in self.column_mappings.items():
            print(f"  {std_col:20} → {orig_col}")
        
        # Merge dataframes
        print("\n" + "-" * 60)
        print("MERGING DATA...")
        master_df = self.merge_dataframes(data_info_list, self.column_mappings)
        
        if master_df.empty:
            print("No data to merge!")
            return None, None
        
        # Generate summary
        print("\n" + "-" * 60)
        print("GENERATING SUMMARY...")
        summary = self.generate_summary_report(master_df, data_info_list)
        
        # Print summary
        print("\n📊 MERGE SUMMARY:")
        print(f"  Files processed: {summary['total_files_processed']}")
        print(f"  Sheets processed: {summary['total_sheets_processed']}")
        print(f"  Total rows before merge: {summary['total_rows_before_merge']}")
        print(f"  Total rows after merge: {summary['total_rows_after_merge']}")
        print(f"  Duplicates removed: {summary['total_rows_before_merge'] - summary['total_rows_after_merge']}")
        print(f"  Unique columns: {summary['unique_columns_found']}")
        
        # Export to Excel
        print("\n" + "-" * 60)
        print("EXPORTING TO EXCEL...")
        self.export_to_excel(master_df, summary)
        
        return master_df, summary


# Additional utility functions for easier usage
def merge_excel_files_in_folder(folder_path, output_filename="master_truck_data.xlsx"):
    """
    Convenience function to merge all Excel files in a folder
    
    Args:
        folder_path: Path to folder containing Excel files
        output_filename: Name of output file
        
    Returns:
        Merged dataframe
    """
    merger = ExcelMerger(folder_path, output_filename)
    return merger.merge_excel_files()


def merge_specific_files(file_list, output_filename="merged_output.xlsx"):
    """
    Convenience function to merge specific Excel files
    
    Args:
        file_list: List of Excel file paths
        output_filename: Name of output file
        
    Returns:
        Merged dataframe
    """
    merger = ExcelMerger(output_path=output_filename)
    return merger.merge_excel_files(excel_files=file_list)


if __name__ == "__main__":
    # Example usage
    print("Excel File Merger - Ready to Process Truck Data")
    print("\nUsage Options:")
    print("1. Merge all Excel files in a folder")
    print("2. Merge specific Excel files")
    print("3. Use as a module in your code")
    
    # Example 1: Merge all files in a folder
    # merged_data, summary = merge_excel_files_in_folder("path/to/your/excel/files")
    
    # Example 2: Merge specific files
    # files_to_merge = ["file1.xlsx", "file2.xlsx", "file3.xlsx"]
    # merged_data, summary = merge_specific_files(files_to_merge)