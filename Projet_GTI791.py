import pandas as pd
import json
import sys
import os
import re
import warnings
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from tqdm import tqdm
import matplotlib.pyplot as plt

# Suppress specific BeautifulSoup-related warnings
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

# Empty list to store pull requests
docker_pull_requests = []

# Function to clean HTML content extracted from pull requests
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

    # Normalize spaces to have a single space between words
    cleaned_body = ' '.join(cleaned_body.split())

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

# Dictionary associating labels with corresponding keywords
label_keywords = {
    "Major Docker Image Upgrade": ["Docker base image uptodate", " upgrade to alpinelatest", "latest version of your chosen image", "Docker image upgrade", "image security", "Critical", "critical" ],
    "Minor Docker Image Upgrade": ["Docker base image uptodate", " upgrade to alpinelatest", "latest version of your chosen image", "Docker image upgrade", "image security"],
    "Major Dependency Upgrade": ["breaking change", " major version", " upgrade to version 3.0.0", "major upgrade", " version 3.x", " Keep your dependencies uptodate", "The recommended version", "dependencies",],
    "Minor Dependency Upgrade": ["new features", " minor version", " upgrade to version 2.x.x", "minor upgrade", "minor release", "new functionality", "The recommended version"],
    "Patch Dependency Upgrade": ["bug fixes", " patch version", " upgrade to version 2.11.x", "patch upgrade", "bugfix release"],
    "Configuration Change": ["quality assurance", " integration testing", " test coverage", "automated testing", " test results", "CI test", "configuration change", "Docker config change", "modify configuration", "change Docker settings", "configuration update", "settings change", "vulnerable packages", "packages"],
    "Storage Issue Fix": ["fixing the storage problem", " addressing storage concerns", "resolving storage issues", "correcting data storage", "enhancing storage security", "mitigating storage challenges", "upgrading data storage", "protecting sensitive data", " storage ", "storage issues", "storage issue"],
    "Permission Change": ["Incorrect Permission Assignment", "update of permission settings", "change in user access rights", "modification of authorization parameters", "user permission update", "revision of access control", "Permission", ],
}

# Initialize a dictionary to count the number of pull requests per label
label_counts = {label: 0 for label in label_keywords.keys()}

# Function to assign labels based on pull request content
def assign_labels(body):
    body_normalized = ' '.join(body.split()).replace(".", "").lower()  # Convert all text to lowercase

    labels = []

    # Check for Major or Minor Docker Image Upgrade
    if "critical" in body_normalized:  # Case-insensitive check
        labels.append("Major Docker Image Upgrade")
    else:
        # Add a Minor Docker Image Upgrade label only if there are corresponding keywords
        if any(re.compile(r'(?i)\b{}\b'.format(re.escape(' '.join(keyword.split())))).search(body_normalized) for keyword in label_keywords["Minor Docker Image Upgrade"]):
            labels.append("Minor Docker Image Upgrade")

    # Check for Major or Minor Dependency Upgrade
    recommended_version_count = body_normalized.count("the recommended version")
    if recommended_version_count > 1:
        labels.append("Major Dependency Upgrade")
    else:
        # Add a Minor Dependency Upgrade label only if there are corresponding keywords
        if any(re.compile(r'(?i)\b{}\b'.format(re.escape(' '.join(keyword.split())))).search(body_normalized) for keyword in label_keywords["Minor Dependency Upgrade"]):
            labels.append("Minor Dependency Upgrade")

    # Check for other labels
    other_labels = [label for label in label_keywords.keys() if label not in ["Major Docker Image Upgrade", "Minor Docker Image Upgrade", "Major Dependency Upgrade", "Minor Dependency Upgrade"]]
    for label in other_labels:
        if any(re.compile(r'(?i)\b{}\b'.format(re.escape(' '.join(keyword.split())))).search(body_normalized) for keyword in label_keywords[label]):
            labels.append(label)

    return list(set(labels))

# Function to extract relevant information from JSON data of pull requests
def extract_info(payload):
    try:
        data = json.loads(payload)
        pull_request = data.get("pull_request", None)

        extracted_info = {}  # Dictionary to store extracted information

        if pull_request is not None:
            # Extracting title, body, and comments of the PR
            title = pull_request.get("title", "")
            body = pull_request.get("body", "")
            comments = [comment.get("body", "") for comment in data.get("comments", [])]

            # Combine title, body, and comments into a single text
            full_text = f"{title}\n{body}\n{' '.join(comments)}"

            # Checking for Docker content and extracting relevant information
            if full_text and re.search(r'(Docker|docker|DOCKER|DOCKERFILE|Dockerfile|dockerfile)', full_text):
                # Creating a dictionary of extracted information
                extracted_info = {
                    "Title": clean_body(title),
                    "Pull Request Number": pull_request.get("number", ""),
                    "State": clean_body(pull_request.get("state", "")),
                    "Merged": pull_request.get("merged", ""),
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

                # Assigning labels based on content
                extracted_info["Labels"] = assign_labels(full_text)

                # Removing duplicate labels within the same PR
                extracted_info["Labels"] = list(set(extracted_info["Labels"]))

                # Updating the PR count for each label
                for label in extracted_info["Labels"]:
                    label_counts[label] += 1

        else:
            extracted_info = {}

        return extracted_info
    except json.JSONDecodeError:
        return {}

# Main function
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

    csv_output_file_name = input("Enter the output CSV file name (without extension): ")

    # Create a progress bar for processing CSV files
    progress_bar = tqdm(os.listdir(folder_path), desc="Processing CSV files", ncols=100)

    for file_name in progress_bar:
        if file_name.endswith(".csv"):
            csv_file_path = os.path.join(folder_path, file_name)
            progress_bar.set_description(f"Processing {file_name}")
            with open(csv_file_path, mode="r", encoding="utf-8") as file:
                csv_reader = pd.read_csv(file)
                for _, row in tqdm(csv_reader.iterrows(), total=len(csv_reader), leave=False, ncols=100):
                    payload = row.get("payload", "{}")
                    extracted_info = extract_info(payload)

                    if extracted_info:
                        docker_pull_requests.append(extracted_info)

    df = pd.DataFrame(docker_pull_requests)

    csv_output_file_path = os.path.join(folder_path, f"{csv_output_file_name}.csv")
    df.to_csv(csv_output_file_path, index=False, sep=",", encoding="utf-8")
    print("Output CSV file saved.")

    total_pull_requests = len(docker_pull_requests)

    # Calculate and display percentages for "Accepted," "Rejected," and "Still Open" for each label
    print("Percentage of pull requests for each label and state:")
    label_percentages = {}

    for label, count in label_counts.items():
        total_label_pull_requests = count
        accepted_count = df[(df['State'] == 'closed') & (df['Merged'] == True) & (df['Labels'].apply(lambda x: label in x))].shape[0]
        rejected_count = df[(df['State'] == 'closed') & (df['Merged'] == False) & (df['Labels'].apply(lambda x: label in x))].shape[0]
        still_open_count = df[(df['State'] == 'open') & (df['Labels'].apply(lambda x: label in x))].shape[0]

        label_percentages[label] = {
            'Accepted': (accepted_count / total_label_pull_requests) * 100,
            'Rejected': (rejected_count / total_label_pull_requests) * 100,
            'Still Open': (still_open_count / total_label_pull_requests) * 100
        }

        print(f"{label}:")
        print(f"Accepted: {accepted_count} pull requests ({label_percentages[label]['Accepted']:.2f}%)")
        print(f"Rejected: {rejected_count} pull requests ({label_percentages[label]['Rejected']:.2f}%)")
        print(f"Still Open: {still_open_count} pull requests ({label_percentages[label]['Still Open']:.2f}%)")
        print()

    # Create a DataFrame from the percentage dictionary
    df_percentages = pd.DataFrame(label_percentages).T

    # Plot a stacked bar chart
    ax = df_percentages.plot(kind='bar', stacked=True, figsize=(12, 6))

    # Add percentage labels
    for p in ax.patches:
        width, height = p.get_width(), p.get_height()
        x, y = p.get_xy() 
        if height > 0:  # To avoid displaying labels for zero-height bars
            ax.text(x + width/2, 
                    y + height/2, 
                    '{:.1f}%'.format(height), 
                    ha='center', 
                    va='center', 
                    color='black')

    plt.xlabel("Label")
    plt.ylabel("Percentage")
    plt.title("Percentage of States by Label")
    plt.legend(title="State", loc='upper right', bbox_to_anchor=(1.2, 1))
    plt.show()

# Execute the main function if the script is run as the main program
if __name__ == "__main__":
    main()
