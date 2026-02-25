import pandas as pd
import os
from pathlib import Path
import warnings
from datetime import datetime
import numpy as np
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading

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


class ExcelMergerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel File Merger - Truck Data Consolidation")
        self.root.geometry("600x500")
        
        # Center the window
        self.center_window(600, 500)
        
        self.files_to_merge = []
        self.merger = None
        
        self.setup_ui()
    
    def center_window(self, width, height):
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # Set window position
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        # Title
        title_label = tk.Label(
            self.root, 
            text="🚛 Excel Files Merger", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        subtitle_label = tk.Label(
            self.root, 
            text="Truck Data Consolidation Tool",
            font=("Arial", 10)
        )
        subtitle_label.pack()
        
        # File selection frame
        frame = tk.Frame(self.root)
        frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Add files button
        add_button = tk.Button(
            frame,
            text="📁 Add Excel Files",
            command=self.add_files,
            width=25,
            height=2,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10)
        )
        add_button.pack(pady=5)
        
        # Add folder button
        add_folder_button = tk.Button(
            frame,
            text="📂 Add Folder with Excel Files",
            command=self.add_folder,
            width=25,
            height=2,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10)
        )
        add_folder_button.pack(pady=5)
        
        # File list
        list_frame = tk.Frame(frame)
        list_frame.pack(pady=10, fill="both", expand=True)
        
        list_label = tk.Label(list_frame, text="Selected Files:", font=("Arial", 10, "bold"))
        list_label.pack(anchor="w")
        
        self.file_listbox = tk.Listbox(list_frame, height=8, font=("Arial", 9))
        self.file_listbox.pack(fill="both", expand=True, pady=5)
        
        scrollbar = tk.Scrollbar(self.file_listbox)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.file_listbox.yview)
        
        # Remove button
        remove_button = tk.Button(
            frame,
            text="🗑️ Remove Selected",
            command=self.remove_selected,
            width=20,
            bg="#f44336",
            fg="white"
        )
        remove_button.pack(pady=5)
        
        # Output filename
        output_frame = tk.Frame(frame)
        output_frame.pack(pady=10, fill="x")
        
        output_label = tk.Label(output_frame, text="Output File Name:", font=("Arial", 10, "bold"))
        output_label.pack(anchor="w")
        
        self.output_var = tk.StringVar(value="master_truck_data.xlsx")
        output_entry = tk.Entry(output_frame, textvariable=self.output_var, width=40, font=("Arial", 10))
        output_entry.pack(fill="x", pady=2)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            frame, 
            variable=self.progress_var,
            maximum=100,
            length=400
        )
        self.progress_bar.pack(fill="x", pady=10)
        
        # Merge button
        self.merge_button = tk.Button(
            frame,
            text="🔄 Merge Files",
            command=self.start_merge,
            bg="#FF9800",
            fg="white",
            font=("Arial", 12, "bold"),
            width=25,
            height=2
        )
        self.merge_button.pack(pady=10)
        
        # Status label
        self.status_label = tk.Label(frame, text="Ready to merge files", fg="#4CAF50", font=("Arial", 10))
        self.status_label.pack()
    
    def add_files(self):
        files = filedialog.askopenfilenames(
            title="Select Excel Files",
            filetypes=[
                ("Excel files", "*.xlsx *.xls *.xlsm *.xlsb"),
                ("All files", "*.*")
            ]
        )
        
        for file in files:
            if file not in self.files_to_merge:
                self.files_to_merge.append(file)
                self.file_listbox.insert(tk.END, f"📄 {Path(file).name}")
        
        if files:
            self.update_status(f"Added {len(files)} file(s)")
    
    def add_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Excel Files")
        
        if folder:
            excel_extensions = ['.xlsx', '.xls', '.xlsm', '.xlsb']
            files_added = 0
            for ext in excel_extensions:
                for file in Path(folder).glob(f"*{ext}"):
                    file_str = str(file)
                    if file_str not in self.files_to_merge:
                        self.files_to_merge.append(file_str)
                        self.file_listbox.insert(tk.END, f"📄 {file.name}")
                        files_added += 1
            
            if files_added:
                self.update_status(f"Added {files_added} file(s) from folder")
            else:
                self.update_status("No Excel files found in the folder", "orange")
    
    def remove_selected(self):
        selected = self.file_listbox.curselection()
        if selected:
            for index in selected[::-1]:
                self.files_to_merge.pop(index)
                self.file_listbox.delete(index)
            self.update_status(f"Removed {len(selected)} file(s)")
    
    def update_status(self, message, color=None):
        self.status_label.config(text=message)
        if color:
            self.status_label.config(fg=color)
    
    def start_merge(self):
        if not self.files_to_merge:
            messagebox.showerror("Error", "Please select at least one Excel file!")
            return
        
        # Disable merge button during processing
        self.merge_button.config(state=tk.DISABLED, text="🔄 Processing...")
        self.update_status("Processing files... Please wait", "orange")
        self.progress_var.set(10)
        
        # Start merge in separate thread
        thread = threading.Thread(target=self.perform_merge)
        thread.daemon = True
        thread.start()
    
    def perform_merge(self):
        try:
            output_file = self.output_var.get()
            if not output_file.endswith('.xlsx'):
                output_file += '.xlsx'
            
            # Update progress
            self.root.after(0, lambda: self.progress_var.set(20))
            
            # Create merger and process files
            self.merger = ExcelMerger(output_path=output_file)
            
            self.root.after(0, lambda: self.progress_var.set(40))
            merged_data, summary = self.merger.merge_excel_files(excel_files=self.files_to_merge)
            
            self.root.after(0, lambda: self.progress_var.set(80))
            
            if merged_data is not None:
                self.root.after(0, lambda: self.merge_complete(summary))
            else:
                self.root.after(0, self.merge_failed)
                
        except Exception as e:
            self.root.after(0, lambda: self.merge_error(str(e)))
    
    def merge_complete(self, summary):
        self.progress_var.set(100)
        self.merge_button.config(state=tk.NORMAL, text="🔄 Merge Files")
        self.update_status("Merge Complete!", "#4CAF50")
        
        # Show success message
        messagebox.showinfo(
            "✅ Success!",
            f"Excel files merged successfully!\n\n"
            f"📊 Summary:\n"
            f"• Files processed: {summary['total_files_processed']}\n"
            f"• Sheets processed: {summary['total_sheets_processed']}\n"
            f"• Total rows merged: {summary['total_rows_after_merge']}\n"
            f"• Output saved as: {self.output_var.get()}\n\n"
            f"The master file contains:\n"
            f"1. Master_Data - All merged data\n"
            f"2. Merge_Summary - Summary report\n"
            f"3. Column_Mapping - How columns were matched\n"
            f"4. File_Details - Source file information"
        )
    
    def merge_failed(self):
        self.progress_var.set(0)
        self.merge_button.config(state=tk.NORMAL, text="🔄 Merge Files")
        self.update_status("Merge failed - No valid data found", "red")
        messagebox.showerror("Error", "No valid data found in the selected files!")
    
    def merge_error(self, error_msg):
        self.progress_var.set(0)
        self.merge_button.config(state=tk.NORMAL, text="🔄 Merge Files")
        self.update_status(f"Error: {error_msg[:50]}...", "red")
        messagebox.showerror("Error", f"An error occurred:\n{error_msg}")


# Create a simple launcher script
def main():
    print("Starting Excel Merger GUI...")
    print("Make sure you have pandas and openpyxl installed:")
    print("If not, run in Command Prompt as Administrator:")
    print("python -m pip install pandas openpyxl")
    
    try:
        # Check if required packages are installed
        import pandas
        import openpyxl
        print("✓ Required packages are installed")
    except ImportError as e:
        print(f"✗ Missing package: {e}")
        print("\nPlease install missing packages first:")
        print("Open Command Prompt as Administrator and run:")
        print("python -m pip install pandas openpyxl")
        input("\nPress Enter to exit...")
        return
    
    root = tk.Tk()
    app = ExcelMergerGUI(root)
    
    # Add some styling
    style = ttk.Style()
    style.theme_use('clam')
    
    root.mainloop()


if __name__ == "__main__":
    main()