import requests
import pandas as pd
from tqdm import tqdm

# Load the dataset
file_path = './data/RxNorm/split_chunk_001_test.csv'
data = pd.read_csv(file_path)

# ChEMBL API base URLs
chembl_molecule_url = "https://www.ebi.ac.uk/chembl/api/data/molecule"
chembl_target_url = "https://www.ebi.ac.uk/chembl/api/data/target"

# Function to search for ChEMBL ID based on drug name
def get_chembl_id(drug_name):
    try:
        response = requests.get(chembl_molecule_url, params={"pref_name__iexact": drug_name})
        response.raise_for_status()
        results = response.json().get("molecules", [])
        if results:
            return results[0]["molecule_chembl_id"]  # Return the first ChEMBL ID
    except Exception as e:
        print(f"Error fetching ChEMBL ID for {drug_name}: {e}")
    return None

# Function to fetch target proteins for a given ChEMBL ID
def get_targets_for_chembl_id(chembl_id):
    try:
        response = requests.get(chembl_target_url, params={"molecule_chembl_id": chembl_id})
        response.raise_for_status()
        results = response.json().get("targets", [])
        target_proteins = [target.get("target_chembl_id") for target in results if target.get("target_chembl_id")]
        return ";".join(target_proteins)  # Return a semicolon-separated list of target proteins
    except Exception as e:
        print(f"Error fetching targets for ChEMBL ID {chembl_id}: {e}")
    return None

# Full workflow: Map drug names to ChEMBL IDs and then to target proteins
def map_drug_to_proteins(drug_name):
    chembl_id = get_chembl_id(drug_name)
    if chembl_id:
        return get_targets_for_chembl_id(chembl_id)
    return None

# Map drug names to target proteins with progress bar
print("Mapping drug names to target proteins...")
data["drug_1_targets"] = [
    map_drug_to_proteins(drug_name) for drug_name in tqdm(data["drug_1_concept_name"], desc="Drug 1")
]
data["drug_2_targets"] = [
    map_drug_to_proteins(drug_name) for drug_name in tqdm(data["drug_2_concept_name"], desc="Drug 2")
]

# Save the dataset with target mappings
output_path = "./data/output/dataset_with_targets.csv"
data.to_csv(output_path, index=False)

print(f"Dataset with target proteins saved to {output_path}")
