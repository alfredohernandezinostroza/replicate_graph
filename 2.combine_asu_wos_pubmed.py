
# %%
import os
from pathlib import Path
import pandas as pd

# %% [markdown]
# ### Summary:
# - PubMed, retrieved on 08/04/2025, JSON format. pubmed_DB.json.
# - Scopus, retrieved by Eric on 06/09/2024. CSV format. scopus_DB.csv.
# - EBSCO Academic Search Ultimate, retrieved on 09/04/2025, RIS format. EBSCO_ris.ris
# - Web of Science, retrieved on 09/04/2025, TSV format. Web_of_science_DB_with_33986_entries.csv.

input_path = Path("1.Data")
output_path = Path("2.Data")
output_path.mkdir(exist_ok=True)
# %% [markdown]
# ### Web of Science

# %%
fileterd_Wos = pd.read_csv(input_path/"Web_of_science_DB.csv",sep="\t", dtype=str)

# %% [markdown]
# This database's columns are not easy to identify. By carefully inspecting them, they were identified as:
# Title = TI, Authors = AU, Date = PD, DOI = DI, Abstract = AB, Journal = SO
# Note that this database does not record PubMed ID nor Keywords. Thus, they must be filled with NANs.
# Since the column Unnamed: 78 was filled with NANs, it was used to create the PubMed ID and Keywords columns.

# %%
fileterd_Wos = fileterd_Wos[["TI","AU","PD","DI","Unnamed: 78","Unnamed: 78","AB","SO"]]
fileterd_Wos.columns=["Title","Authors","Date","DOI","PubMed ID","Keywords","Abstract","Journal"]

# %% [markdown]
# ### EBSCO:

# %%
import rispy as rp
from copy import deepcopy

#%%
mapping = deepcopy(rp.TAG_KEY_MAPPING)
mapping["L3"] = "DOI"
with open(input_path/"EBSCO_DB.ris") as f:
    entries = rp.load(f, mapping=mapping)
EBSCO_db = pd.DataFrame(entries)
EBSCO_db["authors"] = EBSCO_db["authors"].map(lambda x:  '; '.join(x) if type(x) == list else x )
EBSCO_db["keywords"] = EBSCO_db["keywords"].map(lambda x:  ', '.join(x) if type(x) == list else x )
filtered_EBSCO = EBSCO_db[["primary_title","authors","publication_year","DOI","keywords","abstract","journal_name"]]
filtered_EBSCO.loc[:,"PubMed ID"] = None
filtered_EBSCO.columns=["Title","Authors","Date","DOI","Keywords","Abstract","Journal","PubMed ID"]

# %% [markdown]
# ### PubMed
pubmed_db = pd.read_json(input_path/"pubmed_DB.json")
def get_authors_from_authors_list(authors_list: list) -> str:
    authors_string = ''
    for author in authors_list:
        if author['firstname'] is None:
            author['firstname'] = ''
        if author['initials'] is None:
            author['initials'] = ''
        if author['lastname'] is None:
            author['lastname'] = ''
        new_author = author['firstname']+' '+author['initials']+'. '+author['lastname']+'; '
        if new_author == ' . ; ':
            continue
        authors_string += new_author
    authors_string = authors_string[0:-2] 
    return authors_string

pubmed_db["authors"] = pubmed_db["authors"].map(lambda x: get_authors_from_authors_list(x)  if type(x) == list and len(x) > 1 else x )

# %%
filtered_pubmed = pubmed_db[["title","authors","publication_date","doi","abstract","journal","pubmed_id"]]
filtered_pubmed.loc[:,"Keywords"] = None
filtered_pubmed.columns=["Title","Authors","Date","DOI","Abstract","Journal","PubMed ID","Keywords"]

# %%
filtered_EBSCO.loc[:,"Database"] = "EBSCO"
filtered_pubmed.loc[:,"Database"] = "Pubmed"
fileterd_Wos.loc[:,"Database"] = "Web of Science"
# %%  
pubmed_EBSCON_WoS = pd.concat([filtered_EBSCO, filtered_pubmed, fileterd_Wos])
pubmed_EBSCON_WoS.to_csv(output_path/"pubmed_EBSCON_WoS_DB.csv",sep="\t",index=False)
