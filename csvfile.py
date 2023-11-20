import pandas as pd
import json
import sys
import os
import re
import warnings
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

docker_pull_requests = []

def clean_body(body, max_line_length=None):
    if body is None:
        return ""

    soup = BeautifulSoup(body, "html.parser")

    for tag in soup.find_all(["h3", "hr", "img", "table"]):
        tag.extract()

    cleaned_body = soup.get_text(separator=" ")

    cleaned_body = re.sub(r"â€™", "'", cleaned_body)
    cleaned_body = re.sub(r"â€œ", '"', cleaned_body)
    cleaned_body = re.sub(r"â€", '"', cleaned_body)
    cleaned_body = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned_body)
    cleaned_body = re.sub(r"\*\*([^\*]+)\*\*", r"\1", cleaned_body)
    cleaned_body = re.sub(r"\*([^\*]+)\*", r"\1", cleaned_body)
    cleaned_body = re.sub(r"ðŸ§|ðŸ› |â€™|ðŸ¦‰", "", cleaned_body)
    cleaned_body = re.sub(r"[\x80-\xFF]+", "", cleaned_body)
    cleaned_body = re.sub(r"[^a-zA-Z0-9\s|:-]", "", cleaned_body)

    if max_line_length and isinstance(max_line_length, int):
        lines = []
        words = cleaned_body.split()
        current_line = ""
        for word in words:
            if len(current_line) + len(word) + 1 <= max_line_length:
                if current_line:
                    current_line += " "
                current_line += word
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        cleaned_body = "\n".join(lines)

        cleaned_body = textwrap.fill(cleaned_body, width=max_line_length, subsequent_indent="| ")

    return cleaned_body

def extract_info(payload):
    try:
        data = json.loads(payload)
        pull_request = data.get("pull_request", None)

        if pull_request is not None:
            body = pull_request.get("body", "")

            body = clean_body(body)

            docker_related_pattern = r'(Docker|docker|DOCKER)'

            if re.search(docker_related_pattern, body):
                paragraphs = [p.strip() for p in body.split('\n\n') if p.strip()]
                cleaned_body = '\n\n'.join(paragraphs)

                label_mapping = {
                    "update": "Docker Dependency Update",
                    "storage issue": "Docker Storage Issue Fix",
                    "permissions": "Permission Change",
                    "optimization": "Performance Optimization",
                    "config": "Docker Configuration Update",
                    "security": "Docker Security",
                    "fix": "Docker Bug Fix",
                    "bug": "Docker Bug Fix",
                    # Add more keywords and labels here as needed
                }

                label_found = False

                for keyword, label in label_mapping.items():
                    if keyword in cleaned_body.lower():
                        extracted_info = {
                            "Title": clean_body(pull_request.get("title", "")),
                            "Pull Request Number": pull_request.get("number", ""),
                            "State": clean_body(pull_request.get("state", "")),
                            "Author": clean_body(pull_request["user"].get("login", "")),
                            "Body": cleaned_body,
                            "Created At": pull_request.get("created_at", ""),
                            "Commits": pull_request.get("commits", ""),
                            "Additions": pull_request.get("additions", ""),
                            "Deletions": pull_request.get("deletions", ""),
                            "Changed Files": pull_request.get("changed_files", ""),
                            "Links": {
                                "URL": clean_body(pull_request.get("url", "")),
                                "HTML URL": clean_body(pull_request.get("html_url", "")),
                                "Diff URL": clean_body(pull_request.get("diff_url", "")),
                                "Patch URL": clean_body(pull_request.get("patch_url", "")),
                            },
                            "Label": label
                        }
                        label_found = True
                        break

                if not label_found:
                    extracted_info = {
                        "Title": clean_body(pull_request.get("title", "")),
                        "Pull Request Number": pull_request.get("number", ""),
                        "State": clean_body(pull_request.get("state", "")),
                        "Author": clean_body(pull_request["user"].get("login", "")),
                        "Body": cleaned_body,
                        "Created At": pull_request.get("created_at", ""),
                        "Commits": pull_request.get("commits", ""),
                        "Additions": pull_request.get("additions", ""),
                        "Deletions": pull_request.get("deletions", ""),
                        "Changed Files": pull_request.get("changed_files", ""),
                        "Links": {
                            "URL": clean_body(pull_request.get("url", "")),
                            "HTML URL": clean_body(pull_request.get("html_url", "")),
                            "Diff URL": clean_body(pull_request.get("diff_url", "")),
                            "Patch URL": clean_body(pull_request.get("patch_url", "")),
                        },
                        "Label": "Other Docker Fix"
                    }

                docker_pull_requests.append(extracted_info)

            else:
                extracted_info = {}
        else:
            extracted_info = {}

        return extracted_info
    except json.JSONDecodeError:
        return {}

def main():
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        folder_path = input("Please enter the folder path: ")

    if not os.path.isdir(folder_path):
        print("The specified folder does not exist.")
        sys.exit(1)

    df_columns = list(extract_info(""))
    df = pd.DataFrame(columns=df_columns)

    for file_name in os.listdir(folder_path):
        if file_name.endswith(".csv"):
            csv_file_path = os.path.join(folder_path, file_name)
            print(f"Processing file: {csv_file_path}")

            with open(csv_file_path, mode="r", encoding="utf-8") as file:
                csv_reader = pd.read_csv(file)
                for _, row in csv_reader.iterrows():
                    payload = row.get("payload", "{}")
                    extracted_info = extract_info(payload)

                    if extracted_info:
                        docker_pull_requests.append(extracted_info)

    df = pd.DataFrame(docker_pull_requests)

    csv_output_file_name = input("Enter the CSV output file name (without extension): ")
    csv_output_file_path = os.path.join(folder_path, f"{csv_output_file_name}.csv")
    df.to_csv(csv_output_file_path, index=False, sep=",", encoding="utf-8")
    print("CSV output file saved.")

if __name__ == "__main__":
    main()
