import requests
import pandas as pd
from tqdm import tqdm

# Load the dataset
file_path = './data/RxNorm/split_chunk_001_test.csv'
data = pd.read_csv(file_path)

# ChEMBL API base URL
chembl_base_url = "https://www.ebi.ac.uk/chembl/api/data"

# Function to map drug name to target proteins
def get_proteins_for_drug(drug_name):
    try:
        # Query ChEMBL API for the drug
        response = requests.get(f"{chembl_base_url}/molecule", params={"name": drug_name})
        response.raise_for_status()
        results = response.json().get("molecules", [])
        if not results:
            return None  # No matches found
        
        # Get the ChEMBL ID for the drug
        chembl_id = results[0].get("molecule_chembl_id")
        if not chembl_id:
            return None
        
        # Query ChEMBL for the drug's targets
        target_response = requests.get(f"{chembl_base_url}/target", params={"molecule_chembl_id": chembl_id})
        target_response.raise_for_status()
        targets = target_response.json().get("targets", [])
        target_proteins = [target.get("target_chembl_id") for target in targets if target.get("target_chembl_id")]
        return ";".join(target_proteins)  # Return a semicolon-separated list of target proteins
    except Exception as e:
        print(f"Error fetching targets for {drug_name}: {e}")
        return None

# Map drug names to target proteins with progress bar
print("Mapping drug names to target proteins...")
data["drug_1_targets"] = [
    get_proteins_for_drug(drug_name) for drug_name in tqdm(data["drug_1_concept_name"], desc="Drug 1")
]
data["drug_2_targets"] = [
    get_proteins_for_drug(drug_name) for drug_name in tqdm(data["drug_2_concept_name"], desc="Drug 2")
]

# Save the dataset with target mappings
output_path = "./data/UniProt/dataset_with_targets.csv"
data.to_csv(output_path, index=False)

print(f"Dataset with target proteins saved to {output_path}")
