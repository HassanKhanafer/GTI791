import pandas as pd
import json
import sys
import os
import re
import warnings
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from tqdm import tqdm

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

    return cleaned_body

# Update label mapping with labels and associated keywords
label_keywords = {
    "Docker Image Upgrade": ["Docker base image uptodate", "upgrade to alpinelatest", "latest version of your chosen image", "Docker image upgrade", "image security"],
    "Major Dependency Upgrade": ["breaking change", "major version", "upgrade to version 3.0.0", "major upgrade", "version 3.x"],
    "Minor Dependency Upgrade": ["new features", "minor version", "upgrade to version 2.x.x", "minor upgrade", "minor release", "new functionality"],
    "Patch Dependency Upgrade": ["bug fixes", "patch version", "upgrade to version 2.11.x", "patch upgrade", "bugfix release"],
    "Configuration Change": [ "quality assurance", "integration testing", "test coverage", "automated testing", "test results", "CI test", "configuration change", "Docker config change", "modify configuration", "change Docker settings", "configuration update", "settings change"],
    "Storage Issue Fix": [ "fixing the storage problem", "addressing storage concerns", "resolving storage issues", "correcting data storage", "enhancing storage security", "mitigating storage challenges", "upgrading data storage", "protecting sensitive data", " storage ", "storage issues", "storage issue"],
    "Permission Change": [
        "alteration of user authorizations",
        "update of permission settings",
        "change in user access rights",
        "modification of authorization parameters",
        "user permission update",
        "revision of access control",
    ],
}

# Create a dictionary to store the count of pull requests for each label
label_counts = {label: 0 for label in label_keywords.keys()}

def assign_label(body):
    # Initialize label as None
    label = None

    # Iterate through labels and corresponding keywords
    for candidate_label, keywords in label_keywords.items():
        for keyword in keywords:
            if keyword in body.lower():
                label = candidate_label
                break  # Exit the loop as soon as a keyword is found

    return label

def extract_info(payload):
    try:
        data = json.loads(payload)
        pull_request = data.get("pull_request", None)

        extracted_info = {}  # Initialize extracted_info as an empty dictionary

        if pull_request is not None:
            body = pull_request.get("body", "")

            # Check if the body is not None and contains Docker-related keywords or patterns
            if body and re.search(r'(Docker|docker|DOCKER|DOCKERFILE|Dockerfile|dockerfile)', body):
                # If Docker-related content is found, extract information
                extracted_info = {
                    "Title": clean_body(pull_request.get("title", "")),
                    "Pull Request Number": pull_request.get("number", ""),
                    "State": clean_body(pull_request.get("state", "")),
                    "Author": clean_body(pull_request["user"].get("login", "")),
                    "Body": clean_body(body),
                    "Created At": pull_request.get("created_at", ""),
                    "Commits": pull_request.get("commits", ""),
                    "Additions": pull_request.get("additions", ""),
                    "Deletions": pull_request.get("deletions", ""),
                    "Changed Files": pull_request.get("changed_files", ""),
                    "Links": {
                        "URL": pull_request.get("url", ""),
                    }
                }

                # Assign label based on keywords in the body
                extracted_info["Label"] = assign_label(body)

                # Update the count of pull requests for the assigned label
                if extracted_info["Label"] is not None:
                    label_counts[extracted_info["Label"]] += 1

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
                for _, row in tqdm(csv_reader.iterrows(), total=len(csv_reader)):  # Add tqdm here
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

    total_pull_requests = len(docker_pull_requests)

    # Calculate the total percentage of all labels
    total_percentage = 0.0

    # Calculate and display the percentage for each label
    print("Percentage of pull requests for each label:")
    for label, count in label_counts.items():
        total_percentage += (count / total_pull_requests) * 100

    for label, count in label_counts.items():
        percentage = (count / total_pull_requests) * 100

        # Adjust the percentage based on the total_percentage
        if total_percentage != 100.0:
            percentage = (percentage / total_percentage) * 100

        print(f"{label}: {count} pull requests ({percentage:.2f}%)")

if __name__ == "__main__":
    main()
