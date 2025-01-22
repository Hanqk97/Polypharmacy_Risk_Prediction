import requests
import pandas as pd
from tqdm import tqdm

# Load the dataset
file_path = './data/RxNorm/split_chunk_001_test.csv'
data = pd.read_csv(file_path)

# ChEMBL API base URLs
chembl_molecule_url = "https://www.ebi.ac.uk/chembl/api/data/molecule"
chembl_mechanism_url = "https://www.ebi.ac.uk/chembl/api/data/mechanism"
chembl_target_url = "https://www.ebi.ac.uk/chembl/api/data/target"
chembl_activity_url = "https://www.ebi.ac.uk/chembl/api/data/activity"

# Function to search for ChEMBL ID based on drug name
def get_chembl_id(drug_name):
    try:
        response = requests.get(chembl_molecule_url, params={"pref_name__iexact": drug_name})
        response.raise_for_status()
        results = response.json().get("molecules", [])
        if results:
            chembl_id = results[0]["molecule_chembl_id"]
            print(f"[INFO] Found ChEMBL ID for {drug_name}: {chembl_id}")
            return chembl_id
        else:
            print(f"[WARNING] No ChEMBL ID found for {drug_name}")
    except Exception as e:
        print(f"[ERROR] Failed to fetch ChEMBL ID for {drug_name}: {e}")
    return None

# Function to fetch the mechanism of action for a given ChEMBL ID
def get_mechanism_of_action(chembl_id):
    try:
        response = requests.get(chembl_mechanism_url, params={"molecule_chembl_id": chembl_id})
        response.raise_for_status()
        results = response.json().get("mechanisms", [])
        if results:
            targets = [(entry["mechanism_of_action"], entry["target_chembl_id"]) for entry in results]
            print(f"[INFO] Mechanism of action for {chembl_id}: {targets}")
            return targets
        else:
            print(f"[WARNING] No mechanism of action found for {chembl_id}")
    except Exception as e:
        print(f"[ERROR] Failed to fetch mechanism of action for {chembl_id}: {e}")
    return None

# Function to fetch activity data for a drug-target pair
def get_activity_data(molecule_chembl_id, target_chembl_id):
    try:
        params = {
            "molecule_chembl_id": molecule_chembl_id,
            "target_chembl_id": target_chembl_id,
        }
        response = requests.get(chembl_activity_url, params=params)
        response.raise_for_status()
        activities = response.json().get("activities", [])
        if activities:
            activity_values = [
                {"standard_type": act.get("standard_type"), "value": act.get("standard_value")}
                for act in activities
            ]
            print(f"[INFO] Activity data for {molecule_chembl_id} -> {target_chembl_id}: {activity_values}")
            return activity_values
        else:
            print(f"[WARNING] No activity data found for {molecule_chembl_id} -> {target_chembl_id}")
    except Exception as e:
        print(f"[ERROR] Failed to fetch activity data for {molecule_chembl_id} -> {target_chembl_id}: {e}")
    return None

# Map drug names to targets and activity data
def map_drug_to_targets(drug_name):
    chembl_id = get_chembl_id(drug_name)
    if not chembl_id:
        return None
    
    mechanisms = get_mechanism_of_action(chembl_id)
    if not mechanisms:
        return None
    
    # Fetch activity data for each target
    target_activity_data = {}
    for mechanism, target_id in mechanisms:
        activity_data = get_activity_data(chembl_id, target_id)
        target_activity_data[target_id] = {
            "mechanism": mechanism,
            "activity": activity_data,
        }
    return target_activity_data

# Apply the mapping with progress tracking
print("Mapping drugs to targets and activity data...")
drug_target_data = []
for drug_name in tqdm(data["drug_1_concept_name"], desc="Drug 1"):
    result = map_drug_to_targets(drug_name)
    drug_target_data.append({"drug_name": drug_name, "targets": result})

# Save the results to a file
output_path = "./data/output/drug_target_mapping.json"
import json
with open(output_path, "w") as f:
    json.dump(drug_target_data, f, indent=4)

print(f"Drug-target mapping saved to {output_path}")
