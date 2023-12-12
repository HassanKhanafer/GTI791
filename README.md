# Explanation of the Python Script for Analyzing Docker Pull Requests

This document provides an explanation of the provided Python script designed to analyze Docker pull requests. The script assigns labels to pull requests based on their content and generates statistics and a stacked bar chart to visualize the percentage of pull requests in different states for each label.

## Importing Libraries

The script starts by importing the following libraries:

- `pandas`: For data manipulation and analysis.
- `json`: For parsing JSON data.
- `sys`: For system-related functions and command-line arguments.
- `os`: For file system operations.
- `re`: For regular expressions.
- `warnings`: For handling warnings.
- `BeautifulSoup`: For parsing HTML content.
- `tqdm`: For creating progress bars.
- `matplotlib.pyplot`: For data visualization.

## Suppressing Warnings

The script suppresses specific BeautifulSoup-related warnings using `warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)`.

## Initializing Variables

- `docker_pull_requests`: An empty list to store pull request information.
- `label_keywords`: A dictionary associating labels with corresponding keywords.
- `label_counts`: A dictionary to count the number of pull requests per label.
- `df`: An empty pandas DataFrame to store extracted pull request data.
- `csv_output_file_name`: The name of the output CSV file where extracted data will be saved.
- `progress_bar`: A progress bar for processing CSV files.

## Cleaning HTML Content (`clean_body` Function)

The `clean_body` function cleans HTML content extracted from pull requests. It removes unwanted HTML tags, special characters, normalizes spaces, and optionally limits line lengths.

## Assigning Labels (`assign_labels` Function)

The `assign_labels` function assigns labels to pull requests based on their content. It uses predefined keywords to identify labels, such as "Major Docker Image Upgrade," "Minor Docker Image Upgrade," and more.

## Extracting Information (`extract_info` Function)

The `extract_info` function takes a JSON payload as input and extracts relevant information. It includes pull request title, body, state, author, comments, and labels based on content.

## Main Function (`main` Function)

The `main` function is the entry point of the script. It processes CSV files within a specified folder, extracts and analyzes pull request data, and generates output CSV files and a stacked bar chart.

1. It prompts the user for a folder path and CSV output file name.
2. It processes CSV files in the folder, extracting pull request data and assigning labels.
3. Extracted data is stored in a pandas DataFrame and saved to a CSV file.
4. The script calculates and displays the percentage of pull requests in different states for each label.
5. It generates a stacked bar chart using `matplotlib` to visualize the data.

## Running the Script

To run the script:
- Provide a folder path containing CSV files with pull request data.
- Ensure the required libraries (`pandas`, `beautifulsoup4`, `tqdm`, and `matplotlib`) are installed.
- Execute the script, and it will process the data, assign labels, and generate analysis outputs.

This script is useful for automating the analysis of Docker pull requests, making it easier to manage and categorize them based on their content.
