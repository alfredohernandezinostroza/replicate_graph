
# %%
import pandas as pd
from pathlib import Path

input_path = Path("2.Data")
output_path = Path("3.Data")
output_path.mkdir(exist_ok=True)

# %%
pubmed_EBSCON_WoS_DB = pd.read_csv(input_path/"pubmed_EBSCON_WoS_DB.csv", sep="\t", index_col=None)
# %% [markdown]
# Modify the authors column so it follow the followoing format:
# Firstauthorname FirstauthorLastname, Secondauthorname SecondauthorLastname...
authors_new = pubmed_EBSCON_WoS_DB.Authors
authors_new = authors_new.str.split(";", expand=True)
df = authors_new.stack().str.split(',', expand=True)
df = df[df[2].isnull()]
df = df.iloc[:,0:2]
df['cat'] = df[1].str.cat(df[0], sep=' ')
df['cat'] = df['cat'].str.strip()
df.loc[df['cat'].isnull(), 'cat'] = df.loc[df['cat'].isnull(), 0]
df2 = df.groupby(level=0)['cat'].transform(lambda x: ','.join(x))
df2 = df2.groupby(level=0).head(1)
concatenated_names = df2.droplevel(1)
missing_indexes = pubmed_EBSCON_WoS_DB.index.difference(concatenated_names.index)
pubmed_EBSCON_WoS_DB = pubmed_EBSCON_WoS_DB.drop(missing_indexes)
pubmed_EBSCON_WoS_DB['Authors'] = concatenated_names
# %%
scopus = pd.read_csv(Path("1.Data")/"scopus_DB.csv", sep=",", index_col=None)
#%%
scopus=scopus.rename(columns={"Cover Date": "Date"})
#%%
mod_authors = scopus[['Title', 'Authors', 'Date', 'DOI','PubMed ID']]
#%% [markdown]
# We need to use the same format as before for the authors
mod_authors.loc[:,'Authors'] = mod_authors['Authors'].str.split('. ')
mod_authors.loc[:,'Authors'] = mod_authors['Authors'].str.join(',')
db = pd.concat([pubmed_EBSCON_WoS_DB,mod_authors], ignore_index=True)
db.to_csv(output_path/"db_v1.csv",sep='\t',index=False)