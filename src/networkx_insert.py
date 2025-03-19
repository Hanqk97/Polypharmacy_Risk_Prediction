import networkx as nx
import json
import os

def insert_hyperfacts_to_multigraph(input_json, output_path):
    """
    Reads a JSON file containing hyperfacts and inserts them into a NetworkX MultiGraph.
    Saves the graph in JSON format at the specified output path.
    
    :param input_json: Path to the input hyperfacts JSON file.
    :param output_path: Path to save the generated graph JSON file.
    """
    # Ensure output directory exists
    os.makedirs(output_path, exist_ok=True)

    # Load hyperfacts from JSON file
    with open(input_json, "r") as f:
        hyperfacts = json.load(f)

    # Create a MultiGraph (allows multiple edges between nodes)
    G = nx.MultiGraph()

    # Insert hyperfacts into the graph
    for fact in hyperfacts:
        drug1 = fact["drug1"]
        drug2 = fact["drug2"]
        adverse_event = fact["attributes"]["adverseEvent"]
        prr_value = fact["attributes"]["PRR"]

        # Add multiple edges for the same pair (preserves all conditions)
        G.add_edge(drug1, drug2, adverseEvent=adverse_event, PRR=prr_value)

    # Define output file path
    output_json_file = os.path.join(output_path, "polypharmacy_multigraph.json")

    # Save the graph in JSON format
    data = nx.node_link_data(G)
    with open(output_json_file, "w") as f:
        json.dump(data, f, indent=4)
    
    print(f"Graph saved at: {output_json_file}")

# Example usage
if __name__ == "__main__":
    # input_json_path = "./output/test/hyperfacts.json"  # Change this to your input file path
    # output_directory = "./output/test/graph/"  # Change this to your desired output directory

    input_json_path = "./output/split_raw_twosides/hyperfacts.json"  # Change this to your input file path
    output_directory = "./output/split_raw_twosides/graph/"  # Change this to your desired output directory

    insert_hyperfacts_to_multigraph(input_json_path, output_directory)
