import csv
import json
import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog
import os

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

def process_csv(file_path, output_folder, output_file_name, specific_project=None):
    keys_to_extract = ["url", "id", "node_id", "html_url", "diff_url", "patch_url", "issue_url", "number", "state", "locked", "title"]
    csv.field_size_limit(2147483647)  # Augmenter la limite de taille des champs CSV
    with open(file_path, mode='r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        
    for row in csv_reader:
            projectname = row.get('project name', 'N/A')

            if specific_project is None or projectname.lower() == specific_project.lower():
                extracted_info = extract_info(row.get('payload', '{}'), keys_to_extract)
                extracted_info["project_name"] = projectname  # Ajoutez le nom du projet à extracted_info
                output_file_path = os.path.join(output_folder, f"{output_file_name}.csv")
                print("Output File Path:", output_file_path)  # Débogage
                try:
                    with open(output_file_path, mode='a', newline='', encoding='utf-8') as output_file:
                        writer = csv.DictWriter(output_file, fieldnames=["project_name"] + keys_to_extract)
                        if output_file.tell() == 0:
                            writer.writeheader()
                        writer.writerow(extracted_info)
                except Exception as e:
                    print(f"Error writing to file: {e}")

def main():
    output_folder = select_output_folder()
    if output_folder:
        csv_file_path = select_file()
        if csv_file_path:
            print(f"Processing file: {csv_file_path}")
            output_file_name = simpledialog.askstring("Input", "Entrez le nom du fichier de sortie:")
            specific_project = simpledialog.askstring("Input", "Entrez le nom du projet à rechercher (laissez vide pour tous les projets):")
            process_csv(csv_file_path, output_folder, output_file_name, specific_project)
        else:
            print("No file selected. Exiting.")
    else:
        print("No output folder selected. Exiting.")

if __name__ == "__main__":
    main()
