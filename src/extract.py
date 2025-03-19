import os
import pandas as pd
import json

def load_checkpoint(checkpoint_path):
    """Load the set of already processed filenames from the checkpoint file."""
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, "r") as f:
            processed = {line.strip() for line in f if line.strip()}
        return processed
    return set()

def update_checkpoint(checkpoint_path, filename):
    """Append a filename to the checkpoint file."""
    with open(checkpoint_path, "a") as f:
        f.write(filename + "\n")

def safe_float(val):
    try:
        return float(val)
    except ValueError:
        # Return a default value if conversion fails (e.g., 0.0)
        return 0.0


def process_folder(folder_path, output_path):
    # Create the output directory if it does not exist
    os.makedirs(output_path, exist_ok=True)
    # Directory to store checkpoint file
    checkpoint_path = os.path.join(output_path, "processed_files.txt")
    
    # Get list of CSV files in the folder and sort them by filename
    csv_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith(".csv")])
    total_files = len(csv_files)
    print(f"Found {total_files} CSV files in '{folder_path}' (sorted by filename).")
    
    # Load list of already processed files from checkpoint
    processed_files = load_checkpoint(checkpoint_path)
    print(f"{len(processed_files)} files already processed; skipping them.")
    
    # Initialize containers for accumulating results
    extracted_data_frames = []
    hyperfacts = []
    condition_set = set()
    
    # Define the required columns to extract
    required_cols = [
        'drug_1_rxnorm_id', 
        'drug_1_concept_name', 
        'drug_2_rxnorm_id', 
        'drug_2_concept_name', 
        'condition_meddra_id', 
        'condition_concept_name',
        'PRR'  # Added PRR column
    ]
    
    header_names = None
    col_positions = None  # To record column indices from the first file
    
    for idx, filename in enumerate(csv_files, start=1):
        if filename in processed_files:
            print(f"Skipping already processed file: {filename}")
            continue

        print(f"Processing file {idx}/{total_files}: {filename}")
        file_path = os.path.join(folder_path, filename)
        try:
            if header_names is None:
                # First file (or first unprocessed file that has header)
                df = pd.read_csv(file_path)
                header_names = df.columns.tolist()
                try:
                    col_positions = [header_names.index(col) for col in required_cols]
                except ValueError as ve:
                    raise Exception(f"Required column missing in header of {filename}: {ve}")
                df_extracted = df[required_cols].copy()
            else:
                # For files without header
                df = pd.read_csv(file_path, header=None)
                if col_positions is None:
                    raise Exception("Column positions not recorded from the first file.")
                df_extracted = df.iloc[:, col_positions].copy()
                df_extracted.columns = required_cols

            # Update condition set
            condition_set.update(df_extracted['condition_concept_name'].dropna().unique())
            # Append the extracted DataFrame to the list
            extracted_data_frames.append(df_extracted)
            
            # Build hyperrelation facts for each row
            for _, row in df_extracted.iterrows():
                fact = (
                    row['drug_1_concept_name'],
                    "interactWith",
                    row['drug_2_concept_name'],
                    {"adverseEvent": row['condition_concept_name'], "PRR": row['PRR']}
                )
                hyperfacts.append(fact)
                
            # Update checkpoint for this file
            update_checkpoint(checkpoint_path, filename)
            print(f"Successfully processed file: {filename}")
        except Exception as e:
            print(f"Error processing '{filename}': {e}")
    
    # If no valid files processed, exit
    if not extracted_data_frames:
        print("No valid CSV files processed. Exiting.")
        return
    
    # Combine all extracted dataframes and save to CSV
    combined_df = pd.concat(extracted_data_frames, ignore_index=True)
    output_csv = os.path.join(output_path, "extracted_data.csv")
    combined_df.to_csv(output_csv, index=False)
    print(f"Extracted data from {len(extracted_data_frames)} files saved to '{output_csv}'.")
    
    # Save unique conditions to JSON
    conditions = list(condition_set)
    output_conditions = os.path.join(output_path, "conditions.json")
    with open(output_conditions, "w") as f:
        json.dump(conditions, f, indent=4)
    print(f"Unique conditions ({len(conditions)}) saved to '{output_conditions}'.")
    
    # Prepare hyperrelation facts as a list of dictionaries for clarity
    hyperfacts_list = []
    for drug1, relation, drug2, attributes in hyperfacts:
        hyperfacts_list.append({
            "drug1": drug1,
            "relation": relation,
            "drug2": drug2,
            "attributes": attributes
        })
    
    # Then update the sorting line:
    hyperfacts_list.sort(key=lambda x: safe_float(x["attributes"]["PRR"]), reverse=True)
    
    output_hyperfacts = os.path.join(output_path, "hyperfacts.json")
    with open(output_hyperfacts, "w") as f:
        json.dump(hyperfacts_list, f, indent=4)
    print(f"Hyperrelation facts ({len(hyperfacts_list)}) saved to '{output_hyperfacts}'.")

if __name__ == "__main__":
    # Example folder paths; adjust as needed.
    folder_path = "./data/test/"
    output_path = "./output/test/"

    # folder_path = "./data/split_raw_twosides/"
    # output_path = "./output/split_raw_twosides/"
    process_folder(folder_path, output_path)
