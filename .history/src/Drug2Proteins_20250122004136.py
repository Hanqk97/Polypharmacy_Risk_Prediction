import requests
import pandas as pd
from tqdm import tqdm
import time

# Load the dataset
file_path = './data/RxNorm/split_chunk_001_test.csv'
data = pd.read_csv(file_path)

# ChEMBL API base URLs
chembl_molecule_url = "https://www.ebi.ac.uk/chembl/api/data/molecule"
chembl_mechanism_url = "https://www.ebi.ac.uk/chembl/api/data/mechanism"
chembl_activity_url = "https://www.ebi.ac.uk/chembl/api/data/activity"

# Function to search for ChEMBL ID based on drug name
def get_chembl_id(drug_name):
    try:
        response = requests.get(
            chembl_molecule_url,
            params={"pref_name__icontains": drug_name},  # Use partial matching
        )
        if response.status_code == 200 and response.text.strip():
            results = response.json().get("molecules", [])
            if results:
                chembl_id = results[0]["molecule_chembl_id"]
                print(f"[INFO] Found ChEMBL ID for {drug_name}: {chembl_id}")
                return chembl_id
            else:
                print(f"[WARNING] No ChEMBL ID found for {drug_name}")
        else:
            print(f"[ERROR] Empty response for {drug_name}: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Failed to fetch ChEMBL ID for {drug_name}: {e}")
    return None

# Function to fetch mechanism of action
def get_mechanism_of_action(chembl_id):
    try:
        response = requests.get(chembl_mechanism_url, params={"molecule_chembl_id": chembl_id})
        if response.status_code == 200 and response.text.strip():
            results = response.json().get("mechanisms", [])
            if results:
                targets = [(entry["mechanism_of_action"], entry["target_chembl_id"]) for entry in results]
                print(f"[INFO] Mechanism of action for {chembl_id}: {targets}")
                return targets
            else:
                print(f"[WARNING] No mechanism of action found for {chembl_id}")
        else:
            print(f"[ERROR] Empty response for {chembl_id}: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Failed to fetch mechanism of action for {chembl_id}: {e}")
    return None

# Map drug names to targets
print("Mapping drugs to targets...")
drug_target_data = []
for drug_name in tqdm(data["drug_1_concept_name"], desc="Drug 1"):
    chembl_id = get_chembl_id(drug_name)
    if chembl_id:
        mechanisms = get_mechanism_of_action(chembl_id)
        drug_target_data.append({"drug_name": drug_name, "chembl_id": chembl_id, "mechanisms": mechanisms})
    time.sleep(0.5)  # Delay to avoid hitting rate limits

# Save the results to a file
output_path = "./data/UniProt/drug_target_mapping_with_logs.json"
import json
with open(output_path, "w") as f:
    json.dump(drug_target_data, f, indent=4)

print(f"Drug-target mapping saved to {output_path}")
