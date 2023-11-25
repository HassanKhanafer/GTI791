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
    # Remove all special characters except periods and spaces
    cleaned_body = re.sub(r"[^a-zA-Z0-9\s.]", "", cleaned_body)

    # Replace double line breaks with a single line break
    cleaned_body = re.sub(r"\n\n", "\n", cleaned_body)

    # Replace line breaks with spaces
    cleaned_body = cleaned_body.replace("\n", " ")

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

        cleaned_body = textwrap.fill(
            cleaned_body, width=max_line_length, subsequent_indent="| ")

    return cleaned_body


# Update label mapping with labels and associated keywords
label_keywords = {
    "Security Patch": ["security vulnerabilities", "security fixes", "patch security"],
    "Dependency Update": ["dependency update", "update dependencies", "update packages", "dependency upgrade"],
    "Configuration Change": ["configuration change", "Docker config change", "modify configuration", "change Docker settings"],
    "Storage Issue Fix": ["storage problems", "fix storage", "storage enhancements", "Docker storage fixes"],
    "Permission Change": ["permissions change", "update authorizations", "change permissions", "authorization modifications"],
    "Docker Image Upgrade": ["Docker image upgrade", "update Docker base image", "container image upgrade", "update container image"],
}



def extract_info(payload):
    try:
        data = json.loads(payload)
        pull_request = data.get("pull_request", None)

        if pull_request is not None:
            body = pull_request.get("body", "")

            cleaned_body = clean_body(body)

            # Parcourir les labels et les mots-clés correspondants
            for label, keywords in label_keywords.items():
                for keyword in keywords:
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
                        return extracted_info  # Sortir de la boucle dès qu'un label est trouvé

            # Si aucun label n'est trouvé, attribuer "Other Docker Fix"
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
            return extracted_info

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

    csv_output_file_name = input(
        "Enter the CSV output file name (without extension): ")
    csv_output_file_path = os.path.join(
        folder_path, f"{csv_output_file_name}.csv")
    df.to_csv(csv_output_file_path, index=False, sep=",", encoding="utf-8")
    print("CSV output file saved.")


if __name__ == "__main__":
    main()
