import requests
import pandas as pd

# Load the dataset
file_path = './data/RxNorm/split_chunk_001_test.csv'
data = pd.read_csv(file_path)

# UniProt REST API base URL
base_url = "https://rest.uniprot.org/uniprotkb/search"

# Function to query UniProt REST API using RxNORM ID
def map_rxnorm_to_uniprot(rxnorm_id):
    # Example query: searching proteins associated with RxNORM ID
    query = f"database:(rxnorm:{rxnorm_id})"
    params = {
        "query": query,
        "format": "tsv",
        "fields": "accession,id,protein_name"
    }
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        lines = response.text.splitlines()
        if len(lines) > 1:  # Skip header line
            return lines[1].split('\t')[0]  # Return the first UniProt accession
    return None  # Return None if no match found

# Map RxNORM IDs to UniProt URIs
data["drug_1_uniprot"] = data["drug_1_rxnorn_id"].apply(map_rxnorm_to_uniprot)
data["drug_2_uniprot"] = data["drug_2_rxnorm_id"].apply(map_rxnorm_to_uniprot)

# Save the dataset with UniProt mappings
output_path = "./data/UniProt/dataset_with_uniprot_rest.csv"
data.to_csv(output_path, index=False)

print(f"Dataset with UniProt mappings saved to {output_path}")
