import pandas as pd
import json
import sys
import os
import re
import warnings
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning


warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)


def clean_body(body):
    if body is None:
        return ""

    body = body.replace("â€™", "'").replace("â€œ", '"').replace("â€", '"')

    body = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", body)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", MarkupResemblesLocatorWarning)
        soup = BeautifulSoup(body, "html.parser")
    body = soup.get_text(separator=" ")

    body = re.sub(r"\*\*([^\*]+)\*\*", r"\1", body)
    body = re.sub(r"\*([^\*]+)\*", r"\1", body)

    body = re.sub(r"![\[\(].*?[\]\)]", "", body)
    body = re.sub(r"ðŸ§|ðŸ› |â€™|ðŸ¦‰", "", body)
    body = re.sub(r"[\x80-\xFF]+", "", body)

    body = re.sub(r"[^a-zA-Z0-9\s]", "", body)

    body = " ".join(body.split())

    return body


def extract_info(payload):
    try:
        data = json.loads(payload)
        pull_request = data.get("pull_request", None)

        if pull_request is not None:
            milestone_data = pull_request.get("milestone", None)
            milestone_title = (
                clean_body(milestone_data.get("title", "")) if milestone_data else ""
            )

            extracted_info = {
                "Title": clean_body(pull_request.get("title", "")),
                "Pull Request Number": pull_request.get("number", ""),
                "State": clean_body(pull_request.get("state", "")),
                "Author": clean_body(pull_request["user"].get("login", "")),
                "Body": clean_body(pull_request.get("body", "")),
                "Created At": pull_request.get("created_at", ""),
                "Commits": pull_request.get("commits", ""),
                "Additions": pull_request.get("additions", ""),
                "Deletions": pull_request.get("deletions", ""),
                "Changed Files": pull_request.get("changed_files", ""),
                "Vulnerabilities": clean_body(pull_request.get("vulnerabilities", "")),
                "Links": {
                    "URL": clean_body(pull_request.get("url", "")),
                    "HTML URL": clean_body(pull_request.get("html_url", "")),
                    "Diff URL": clean_body(pull_request.get("diff_url", "")),
                    "Patch URL": clean_body(pull_request.get("patch_url", "")),
                },
                "Reviewers": clean_body(
                    str(pull_request.get("requested_reviewers", ""))
                ),
                "Labels": [
                    clean_body(label["name"])
                    for label in pull_request.get("labels", [])
                ],
                "Milestone": milestone_title,
                "Merge Status": clean_body(str(pull_request.get("merged", ""))),
                "Comments": pull_request.get("comments", ""),
                "Assignees": [
                    clean_body(assignee["login"])
                    for assignee in pull_request.get("assignees", [])
                ],
                "Mergeability State": clean_body(
                    pull_request.get("mergeable_state", "")
                ),
                "Merge Commit SHA": clean_body(
                    pull_request.get("merge_commit_sha", "")
                ),
                "Draft Status": clean_body(str(pull_request.get("draft", ""))),
            }
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
                    df = pd.concat(
                        [df, pd.DataFrame([extracted_info])], ignore_index=True
                    )

    output_file_name = input("Enter the output file name (without extension): ")
    output_file_path = os.path.join(folder_path, f"{output_file_name}.csv")
    df.to_csv(output_file_path, index=False, sep=",", encoding="utf-8")
    print("Processing complete. Output file saved.")


if __name__ == "__main__":
    main()
