import csv
import requests
import os
from datetime import datetime
import time
import pandas as pd
from pathlib import Path

def read_csv(filename, start_row=0):
    with open(filename, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='\t')
        next(reader, None)  # Skip header row
        for i, row in enumerate(reader):
            if i >= start_row:
                yield (row[0], row[7], row[3], row[8])  # Title, PubMed ID, DOI and database

def fetch_citations_and_references(doi, pubmed_id):
    if doi:
        url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=citations.externalIds,references.externalIds"
    elif pubmed_id:
        url = f"https://api.semanticscholar.org/graph/v1/paper/PMID:{pubmed_id}?fields=citations.externalIds,references.externalIds"
    else:
        return None, None, "No DOI or PubMed ID available"

    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('citations', []) is None:
                data['citations'] = []
            citations = [(c.get('paperId', ''), c.get('externalIds', {}).get('DOI', '')) for c in data.get('citations', []) if c.get('externalIds')]
            if data.get('references', []) is None:
                data['references'] = []
            references = [(r.get('paperId', ''), r.get('externalIds', {}).get('DOI', '')) for r in data.get('references', []) if r.get('externalIds')]
            return citations, references, None
        else:
            error_message = f"Failed to fetch data: status code {response.status_code}"
            return None, None, error_message
    except requests.RequestException as e:
        return None, None, f"Request failed: {str(e)}"

def main():
    # Set the row number to start from (0-indexed, so 1 means starting from the second row)
    row_start = 0  # Change this value to start from a specific row

    # script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join("4.Data")
    output_dir = os.path.join("5.Data")
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    database_file = os.path.join(input_dir, 'db_v2.csv')
    citations_filename = os.path.join(output_dir, f'citations.csv')
    references_filename = os.path.join(output_dir, f'references.csv')
    failed_fetch_filename = os.path.join(output_dir, f'failed_fetches.csv')

    # Check if files exist, if not, create them with headers
    if not os.path.exists(citations_filename):
        init_csv(citations_filename, ['DOI', 'Citing Paper ID', 'Paper DOI'])
    if not os.path.exists(references_filename):
        init_csv(references_filename, ['DOI', 'Cited Paper ID', 'Paper DOI'])
    if not os.path.exists(failed_fetch_filename):
        init_csv(failed_fetch_filename, ['Title', 'DOI', 'PubMed ID', 'Error Message', 'Database'])
    current_citations, current_references, current_failed_fetches = get_already_fetched_DOIs(citations_filename, references_filename, failed_fetch_filename)
    checked_DOIs = set(current_citations['DOI'].tolist() + current_references['DOI'].tolist() + current_failed_fetches['DOI'].tolist())
    
    for i, (Title, PubMed_ID, DOI, database) in enumerate(read_csv(database_file, row_start), start=row_start):
        if DOI in checked_DOIs:
            print(f"Skipping row {i+1}: {Title} has already been processed.")	
            continue
        # if not DOI in current_failed_fetches.values:
        #     print(f"Skipping row {i+1}: {Title} has already been processed.")	
        #     continue
        print(f"Processing row {i+1}: Fetching data for {Title}...")
        citations, references, error = fetch_citations_and_references(DOI, PubMed_ID)
        if error:
            save_failed_fetch(failed_fetch_filename, Title, DOI, PubMed_ID, database, error)
        else:
            save_to_csv({DOI or PubMed_ID: citations}, citations_filename, 'Citing Paper ID', mode='a')
            save_to_csv({DOI or PubMed_ID: references}, references_filename, 'Cited Paper ID', mode='a')
        time.sleep(1)  # Add a 1-second delay between requests to avoid overwhelming the API

def get_already_fetched_DOIs(citations_filename, references_filename, failed_fetch_filename):
    current_citations = pd.read_csv(citations_filename, usecols=['DOI'])
    current_references = pd.read_csv(references_filename, usecols=['DOI'])
    current_failed_fetches = pd.read_csv(failed_fetch_filename)
    current_failed_fetches = current_failed_fetches.loc[current_failed_fetches.loc[:,"Error Message"].str.contains("Failed to fetch data: status code 404")].reset_index(drop=True)
    return current_citations, current_references, current_failed_fetches

def init_csv(filename, headers):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)  # Header row

def save_to_csv(data, filename, header, mode='a'):
    with open(filename, mode=mode, newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for doi, papers in data.items():
            for paper_id, paper_doi in papers:
                writer.writerow([doi, paper_id, paper_doi])

def save_failed_fetch(filename, title, doi, pubmed_id, error_message, database=None):
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if database:
            writer.writerow([title, doi, pubmed_id, database, error_message])
        else:
            writer.writerow([title, doi, pubmed_id, error_message])

if __name__ == "__main__":
    main()