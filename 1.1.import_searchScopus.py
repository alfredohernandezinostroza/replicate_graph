import os
import csv
import requests
from datetime import datetime


def fetch_motor_learning_literature(api_key, output_file, start_year, end_year, start_index=0):
    url = "https://api.elsevier.com/content/search/scopus"
    query = f"TITLE-ABS-KEY({{Motor Learning}} OR {{Skill Acquisition}} OR {{Motor Adaptation}} OR {{Motor Sequence Learning}} OR {{Sport Practice}} OR {{Motor Skill Learning}} OR {{Sensorimotor Learning}} OR {{Motor Memory}} OR {{Motor Training}} OR {{Movement Acquisition}} OR {{Movement Training}}) AND PUBYEAR AFT {start_year-1} AND PUBYEAR BEF {end_year+1}"
    headers = {
        "X-ELS-APIKey": api_key,
        "Accept": "application/json"
    }
    print(query)
    fetched_articles = 0
    total_articles = None

    while total_articles is None or fetched_articles < total_articles:
        params = {
            "query": query,
            "field": "eid,title,author,coverDate,sourceTitle,doi,citedby-count,pubmed_id",
            "count": 200,
            "sort": "relevance",
            "start": start_index
        } 
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            total_articles = int(data.get('search-results', {}).get('opensearch:totalResults', 0))
            entries = data.get('search-results', {}).get('entry', [])

            # Determine if the file already exists to decide whether to write headers
            file_exists = os.path.isfile(output_file)

            with open(output_file, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(["EID", "Title", "Authors", "Cover Date", "Source Title", "DOI", "Cited By Count", "PubMed ID"])
                for item in entries:
                    authors = item.get('author', [])
                    if isinstance(authors, list):
                        author_surnames = '. '.join([author.get('surname', '') for author in authors])
                    elif isinstance(authors, dict):
                        author_surnames = authors.get('surname', '')
                    else:
                        author_surnames = ''

                    writer.writerow([
                        item.get('eid', ''),
                        item.get('dc:title', ''),
                        author_surnames,  # This now contains only surnames separated by semicolons
                        item.get('prism:coverDate', ''),
                        item.get('prism:sourceTitle', ''),
                        item.get('prism:doi', ''),
                        item.get('citedby-count', ''),
                        item.get('pubmed-id', '')
                    ])

            fetched_articles += len(entries)
            print(f"Fetched {len(entries)} articles, total fetched: {fetched_articles}/{total_articles}")
            start_index += 200
        else:
            print("Failed to fetch data: ", response.status_code)
            break

# Usage
api_key = os.getenv('SCOPUS_API_KEY') # insert you SCOPUS API Key here, e.g., 'xxxxxxxxxxxxxxx' or os.getenv('SCOPUS_API_KEY')

# Create the Data directory one level up from the script's location
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(os.path.dirname(script_dir), '1.Data')
os.makedirs(data_dir, exist_ok=True)
output_file = os.path.join(data_dir, f"scopus_DB.csv")

date_ranges = [
    (1860, 1980),  # Covers 1860 to 1999
    (1981, 1999),  # Covers 1860 to 1999
    (2000, 2003),  # Covers 2000 to 2004
    (2004, 2006),  # Covers 2000 to 2004
    (2007, 2009),  # Covers 2005 to 2009
    (2010, 2013),  # Covers 2010 to 2014
    (2014, 2016),  # Covers 2015 to 2018
    (2017, 2019),  # Covers 2019 to 2023
    (2020, 2021),   # Covers only the year 2024
    (2022, 2023),   # Covers only the year 2024
    (2024, 2025),   # Covers only the year 2024

]

for start_year, end_year in date_ranges:
    fetch_motor_learning_literature(api_key, output_file, start_year, end_year)