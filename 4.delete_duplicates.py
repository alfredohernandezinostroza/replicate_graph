# %%
import pandas as pd
from pathlib import Path

input_path = Path("3.Data")
output_path = Path("4.Data")
output_path.mkdir(exist_ok=True)
# %%
db = pd.read_csv(input_path/"db_v1.csv", sep='\t', index_col=None)

# %%[markdown]
# ##    Remove duplicates
# For that we will use the DOI column as an unique identifier.
# First, we need to convert all the DOIs to lower case, since they are case insensitive.
db.DOI = db.DOI.str.lower()

# %%[markdown]
# Then, we merge the exact duplicates
def fill_NANs_and_merge_exact_duplicates(identifier: list[str], other_columns: list[str], df: pd.DataFrame, inplace: bool = False, reset_index: bool = True) -> pd.DataFrame:
    if not inplace:
        df = df.copy(deep=True)
    filledgroups = df.groupby(identifier)[other_columns].apply(lambda x: x.ffill().bfill())
    filledgroups.reset_index(inplace=True)
    filledgroups.set_index("level_1", inplace=True)
    df.loc[:,other_columns] = filledgroups.loc[:,other_columns]
    df.drop_duplicates(inplace=True)
    if reset_index:
        df.reset_index(drop=True, inplace=True)
    # if not inplace and (id(df) != df_id):
    #     raise ValueError("original dataframe has been lost")
    if not inplace:
        return df

db = fill_NANs_and_merge_exact_duplicates(["DOI"],
                                       ["Title", "Authors", "Date",'Keywords','Abstract','Journal','Database', 'PubMed ID'],
                                       db)
# %% [markdown]
#   We might still have duplicated entries with slightly different values, like having the same titles but in caps, etc.
#   First, let's remove every entry that does not have a DOI
db = db[db["DOI"].notnull()]
# %% [markdown]
# We still have duplicated DOIs:
db[db.duplicated(subset=['DOI'], keep=False)].sort_values(by='DOI')
db[db.duplicated(subset=['DOI'], keep='first')].sort_values(by='DOI')
# %%
# So we need to remove them
db = db.drop_duplicates(subset=['DOI'], keep='first')
# %% [markdown]
# Remove final dot from titles
db.Title = db.Title.apply(lambda x: x[:-1] if x[-1] == '.' else x)
# %%[markdown]
# we fill and merge according to title, not filling the pubmed id
# this is so we propagate important information like keywords and abstracts,
# but not pubmed ids, since they might be different 
# (for example, some papers have supplemental data on Zenodo with the same title as the paper)
db = fill_NANs_and_merge_exact_duplicates(["Title"],
                                       ["Authors", "Date",'Keywords','Abstract','Journal','Database'],
                                       db)
# %% We are not removing these duplicates yet because they should  be removed later when 
# when we delete every node that does not have citations
# if they are not deleted at that step there might be two reasons:
# 1. They are rightfully cited, like when an author cites the data in zenodo instead of the paper, so they must be kept
# 2. The citations are divided across two different entries that represent the same paper. If that happens, we'll merge them.
db.to_csv(output_path/"db_v2.csv",sep='\t',index=False)