import pandas as pd
import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog
import json

def select_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    return file_path

def select_output_folder():
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory()
    return folder_path

def extract_info(payload, keys_to_extract):
    try:
        data = json.loads(payload)
        pull_request = data.get('pull_request', {})
        return {key: pull_request.get(key, '') for key in keys_to_extract}
    except json.JSONDecodeError:
        return {key: '' for key in keys_to_extract}

def main():
    csv_file_path = select_file()
    output_folder = select_output_folder()
    
    if csv_file_path and output_folder:
        print(f"Processing file: {csv_file_path}")
        output_file_name = simpledialog.askstring("Input", "Enter the output file name:")
        
        # Create an empty DataFrame
        df = pd.DataFrame(columns=["project_name", "url", "id", "node_id", "html_url", "diff_url", "patch_url", "issue_url", "number", "state", "locked", "title"])
        
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            csv_reader = pd.read_csv(file)
            for _, row in csv_reader.iterrows():
                payload = row.get('payload', '{}')
                project_name = row.get('project_name', '').strip()
                extracted_info = extract_info(payload, df.columns[1:])  # Exclude 'project_name' from extraction
                extracted_info['project_name'] = project_name
                df = pd.concat([df, pd.DataFrame([extracted_info])], ignore_index=True)
        
        output_file_path = f"{output_folder}/{output_file_name}.csv"
        df.to_csv(output_file_path, index=False)
        print("Processing complete. Output file saved.")
    else:
        print("No file selected. Exiting.")

if __name__ == "__main__":
    main()
