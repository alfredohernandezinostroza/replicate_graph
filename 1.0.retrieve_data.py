import numpy as np
import pandas as pd
from pymedx import PubMed
from pathlib import Path


# %%[markdown]
#   #    1. Obtaining the data
#   ##   1.1 PubMed
#   The data from PubMed can be retrieved with the pymedx package:
# %%
pubmed = PubMed(tool="GetMotorLearningPublications", email="your@email.address")
query = '"Motor Learning" OR "Skill Acquisition" OR "Motor Adaptation" OR "Motor Sequence Learning" OR "Sport Practice" OR "Motor Skill Learning" OR "Sensorimotor Learning" OR "Motor Memory" OR "Motor Training"[Title] AND ("1933/01/01"[Date - Publication]: "2025/04/08"[Date - Publication])'
results = list(pubmed.query(query, max_results=16000)) #We know that with these keywords we should obtain less than 16000
output_path = Path("1.Data")
output_path.mkdir(exist_ok=True)
filepath = output_path/"pubmed_DB.json"
with open(filepath, 'w') as f:
    f.write('[')
    for id, article in enumerate(results):
        data = article.toJSON()
        f.write(data)
        if id < len(results)-1:
            f.write(',')
    f.write(']')
# %%[markdown]
#   ##   1.2 EBSCO's Academic Search Ultimate
#   This database was queried through their online interface on 09/04/2025, and the results were sent by email in the RIS format.
# %%[markdown]
#   ##   Web Of Science
#   This database was queried through their online interface on 09/04/2025, and the results were exported and downloaded in the TSV format.
# %%[markdown]
#   ##   Scopus
#   Scopus data was retrieved with the Python script "import_searchScoppus".    