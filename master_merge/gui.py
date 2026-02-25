import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import pandas as pd
from pathlib import Path

class ExcelMergerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel File Merger - Truck Data Consolidation")
        self.root.geometry("600x500")
        
        self.files_to_merge = []
        self.merger = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # Title
        title_label = tk.Label(
            self.root, 
            text="Excel Files Merger", 
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
            text="Add Excel Files",
            command=self.add_files,
            width=20
        )
        add_button.pack(pady=5)
        
        # Add folder button
        add_folder_button = tk.Button(
            frame,
            text="Add Folder with Excel Files",
            command=self.add_folder,
            width=20
        )
        add_folder_button.pack(pady=5)
        
        # File list
        list_frame = tk.Frame(frame)
        list_frame.pack(pady=10, fill="both", expand=True)
        
        list_label = tk.Label(list_frame, text="Selected Files:")
        list_label.pack(anchor="w")
        
        self.file_listbox = tk.Listbox(list_frame, height=8)
        self.file_listbox.pack(fill="both", expand=True, pady=5)
        
        scrollbar = tk.Scrollbar(self.file_listbox)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.file_listbox.yview)
        
        # Remove button
        remove_button = tk.Button(
            frame,
            text="Remove Selected",
            command=self.remove_selected,
            width=20
        )
        remove_button.pack(pady=5)
        
        # Output filename
        output_frame = tk.Frame(frame)
        output_frame.pack(pady=10, fill="x")
        
        output_label = tk.Label(output_frame, text="Output File Name:")
        output_label.pack(anchor="w")
        
        self.output_var = tk.StringVar(value="master_truck_data.xlsx")
        output_entry = tk.Entry(output_frame, textvariable=self.output_var, width=40)
        output_entry.pack(fill="x", pady=2)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            frame, 
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(fill="x", pady=10)
        
        # Merge button
        self.merge_button = tk.Button(
            frame,
            text="Merge Files",
            command=self.start_merge,
            bg="green",
            fg="white",
            font=("Arial", 10, "bold"),
            width=20
        )
        self.merge_button.pack(pady=10)
        
        # Status label
        self.status_label = tk.Label(frame, text="Ready", fg="blue")
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
                self.file_listbox.insert(tk.END, Path(file).name)
    
    def add_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Excel Files")
        
        if folder:
            excel_extensions = ['.xlsx', '.xls', '.xlsm', '.xlsb']
            for ext in excel_extensions:
                for file in Path(folder).glob(f"*{ext}"):
                    file_str = str(file)
                    if file_str not in self.files_to_merge:
                        self.files_to_merge.append(file_str)
                        self.file_listbox.insert(tk.END, file.name)
    
    def remove_selected(self):
        selected = self.file_listbox.curselection()
        for index in selected[::-1]:
            self.files_to_merge.pop(index)
            self.file_listbox.delete(index)
    
    def start_merge(self):
        if not self.files_to_merge:
            messagebox.showerror("Error", "No files selected!")
            return
        
        # Disable merge button during processing
        self.merge_button.config(state=tk.DISABLED)
        self.status_label.config(text="Processing...", fg="orange")
        
        # Start merge in separate thread
        thread = threading.Thread(target=self.perform_merge)
        thread.start()
    
    def perform_merge(self):
        try:
            output_file = self.output_var.get()
            if not output_file.endswith('.xlsx'):
                output_file += '.xlsx'
            
            # Create merger and process files
            self.merger = ExcelMerger(output_path=output_file)
            merged_data, summary = self.merger.merge_excel_files(excel_files=self.files_to_merge)
            
            if merged_data is not None:
                self.root.after(0, self.merge_complete, summary)
            else:
                self.root.after(0, self.merge_failed)
                
        except Exception as e:
            self.root.after(0, self.merge_error, str(e))
    
    def merge_complete(self, summary):
        self.progress_var.set(100)
        self.status_label.config(text="Merge Complete!", fg="green")
        self.merge_button.config(state=tk.NORMAL)
        
        # Show success message
        messagebox.showinfo(
            "Success",
            f"✅ Merge completed successfully!\n\n"
            f"Files processed: {summary['total_files_processed']}\n"
            f"Sheets processed: {summary['total_sheets_processed']}\n"
            f"Total rows: {summary['total_rows_after_merge']}\n"
            f"Output file: {self.output_var.get()}"
        )
    
    def merge_failed(self):
        self.status_label.config(text="Merge failed - No valid data found", fg="red")
        self.merge_button.config(state=tk.NORMAL)
        messagebox.showerror("Error", "No valid data found in the selected files!")
    
    def merge_error(self, error_msg):
        self.status_label.config(text=f"Error: {error_msg}", fg="red")
        self.merge_button.config(state=tk.NORMAL)
        messagebox.showerror("Error", f"An error occurred:\n{error_msg}")


# To run the GUI version
if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelMergerGUI(root)
    root.mainloop()