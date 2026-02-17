import csv
import pandas as pd
import numpy as np
import os
from datetime import datetime
import time

def read_csv_to_dict(filename, key_col, value_col):
    data = {}
    with open(filename, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader, None)  # Skip header row
        for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
            if len(row) < max(key_col, value_col):
                print(f"Warning: Row {row_num} has fewer columns than expected. Skipping.")
                continue
            
            try:
                key = row[key_col - 1].lower()  # Adjust for 0-based indexing
                value = row[value_col - 1].lower()  # Adjust for 0-based indexing
                
                if key in data:
                    data[key].append(value)
                else:
                    data[key] = [value]
            except IndexError:
                print(f"Error: Unable to process row {row_num}. Skipping.")
    
    return data

def read_doi_pubmed_to_title(filename):
    data = {}
    date_data = {}
    data_author = {}
    data_keywords = {}
    data_abstract = {}
    data_journal = {}
    data_database = {}
    with open(filename, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter="\t")
        next(reader, None)  # Skip header row
        for row in reader:#row[0], row[7], row[3], row[8])  # Title, PubMed ID, DOI and database
            title = row[0]  # Title in column 1 (0-based index 0)
            author = row[1]
            date = row[2]
            doi = row[3]  # DOI in column 4 (0-based index 3)
            keywords = row[4]
            abstract = row[5]
            journal = row[6]
            pubmed_id = row[7]  # PubMed ID in column 8 (0-based index 7)
            database = row[8]
            identifier = doi if doi else pubmed_id
            data[identifier] = title
            date_data[identifier] = date
            data_author[identifier] = author
            data_keywords[identifier] = keywords
            data_abstract[identifier] = abstract
            data_journal[identifier] =  journal
            data_database[identifier] = database
    return data, date_data, data_author, data_keywords,    data_abstract,    data_journal ,    data_database

def create_citation_matrix(citations, references, doi_pubmed_to_title, date, authors, keywords, abstracts, journals , databases):
    all_dois = set(citations.keys()).union(set(references.keys()))
    all_titles = {doi: doi_pubmed_to_title.get(doi, doi) for doi in all_dois}
    all_authors = {doi: authors.get(doi, "Unknown Author") for doi in all_dois}
    all_keywords = {doi: keywords.get(doi, "Unknown keywords") for doi in all_dois}
    all_abstracts = {doi: abstracts.get(doi, "Unknown abstract") for doi in all_dois}
    all_journals = {doi: journals.get(doi, "Unknown journal") for doi in all_dois}
    all_databases = {doi: databases.get(doi, "Unknown database") for doi in all_dois}
    all_dates = {doi: date.get(doi, "Unknown Date") for doi in all_dois}  # Default to "Unknown Date" if not found 
    doi_to_index = {doi: idx for idx, doi in enumerate(all_titles.keys())}  # Map DOIs to indices
    citation_matrix = pd.DataFrame(0, index=all_titles.values(), columns=all_titles.values())
    
    # Initialize an empty set for edges to ensure uniqueness
    edges = set()

    # Populate citation matrix and collect edges for citations
    for cited_doi, citing_dois in citations.items():
        cited_index = doi_to_index.get(cited_doi)
        if cited_index is not None:  # Ensure cited DOI is in the matrix
            for citing_doi in citing_dois:
                citing_index = doi_to_index.get(citing_doi)
                if citing_index is not None:  # Ensure cited DOI is in the matrix
                    citation_matrix.iat[citing_index, cited_index] = 1
                    edges.add((citing_index, cited_index))  # Add edge with correct direction

    # Collect edges for references, ensuring they are unique and correctly directed
    for citing_doi, cited_dois in references.items():
        citing_index = doi_to_index.get(citing_doi)
        if citing_index is not None:  # Ensure cited DOI is in the matrix
            for cited_doi in cited_dois:
                cited_index = doi_to_index.get(cited_doi)
                if cited_index is not None:  # Ensure citing DOI is in the matrix
                    citation_matrix.iat[citing_index, cited_index] = 1
                    edges.add((citing_index, cited_index))  

    citation_count = citation_matrix.sum(axis=0)
    
    # Print the 10 most cited papers
    print(citation_count.nlargest(10))
    
    title_date_df = pd.DataFrame({
        'Id': range(len(all_titles)),
        'Label': list(all_titles.values()),
        'Author': [all_authors[doi] for doi in all_titles.keys()],
        'Abstract': [all_abstracts[doi] for doi in all_titles.keys()],
        'Keywords': [all_keywords[doi] for doi in all_titles.keys()],
        'Journal': [all_journals[doi] for doi in all_titles.keys()],
        'Database': [all_databases[doi] for doi in all_titles.keys()],
        'Doi': [doi for doi in all_titles.keys()],
        'Date': [all_dates[doi] for doi in all_dois],
        # 'Date': [pd.to_datetime(all_dates[doi]).year if pd.to_datetime(all_dates[doi], errors='coerce') is not pd.NaT else "Unknown" for doi in all_dois],
        'CitationCount': citation_count
    })

    # Convert unique edges set to DataFrame
    edge_df = pd.DataFrame(list(edges), columns=['Source', 'Target'])

    return citation_matrix, title_date_df, edge_df


def main():
    input_dir = '5.Data'
    output_dir = '6.Data'
    os.makedirs(output_dir, exist_ok=True)
    # Load DOI/PubMed ID to title mapping
    doi_pubmed_to_title, date, authors, keywords, abstracts, journals , databases = read_doi_pubmed_to_title(os.path.join("4.Data", 'db_v2.csv'))
    # Load citation and reference data
    citations = read_csv_to_dict(os.path.join(input_dir, 'citations.csv'), 1, 3)
    references = read_csv_to_dict(os.path.join(input_dir, 'references.csv'), 1, 3)

    # Create citation matrix and title-date DataFrame
    citation_matrix, title_date_df, edge_df = create_citation_matrix(citations, references, doi_pubmed_to_title, date, authors, keywords, abstracts, journals , databases)

    # Save the citation matrix to a CSV file
    citation_matrix.to_csv(os.path.join(output_dir, 'citation_matrix.csv'), sep='|', encoding='utf-8')

    # Save the title-date DataFrame to a CSV file
    title_date_df.to_csv(os.path.join(output_dir, 'node_attributes.csv'), sep=',', index=False, encoding='utf-8')
    edge_df.to_csv(os.path.join(output_dir, 'edge_attributes.csv'), index=False, encoding='utf-8')


if __name__ == "__main__":
    main()
