from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, XSD
import pandas as pd

# Load the dataset with UniProt mappings
file_path = '/mnt/data/dataset_with_uniprot.csv'
data = pd.read_csv(file_path)

# Define namespaces
UNIPROT = Namespace("http://uniprot.org/uniprot/")
MEDDRA = Namespace("http://meddra.org/condition/")
EX = Namespace("http://example.org/")

# Create RDF graph
g = Graph()

# Process each row in the dataset
total_rows = len(data)
print(f"Starting RDF generation for {total_rows} rows...")
for i, row in enumerate(data.itertuples(), 1):
    # Get drug and condition URIs
    drug1_uri = URIRef(row.drug_1_uniprot)
    drug2_uri = URIRef(row.drug_2_uniprot)
    condition_uri = MEDDRA[row.condition_meddra_id]

    # Create the hyper-relation: <<Drug1 interacts_with Drug2>>
    interaction_triple = (drug1_uri, EX.interacts_with, drug2_uri)

    # Add hyper-relational triples
    g.add((interaction_triple, EX.causes_side_effect, condition_uri))
    g.add((interaction_triple, EX.A, Literal(row.A, datatype=XSD.int)))
    g.add((interaction_triple, EX.B, Literal(row.B, datatype=XSD.int)))
    g.add((interaction_triple, EX.C, Literal(row.C, datatype=XSD.int)))
    g.add((interaction_triple, EX.D, Literal(row.D, datatype=XSD.int)))
    g.add((interaction_triple, EX.PRR, Literal(row.PRR, datatype=XSD.float)))
    g.add((interaction_triple, EX.PRR_error, Literal(row.PRR_error, datatype=XSD.float)))
    g.add((interaction_triple, EX.mean_reporting_frequency, Literal(row.mean_reporting_frequency, datatype=XSD.float)))

    # Print progress
    if i % 100 == 0 or i == total_rows:  # Show progress every 100 rows or at the end
        print(f"Processed {i}/{total_rows} rows...")

# Serialize the RDF graph to Turtle-star format
output_path = "/mnt/data/hyper_relational_kg.ttl"
g.serialize(destination=output_path, format="turtle")
print(f"Hyper-relational knowledge graph saved to {output_path}")

# Print example RDF triples
print("\nExample RDF triples:")
example_triples = list(g)[:5]  # Get the first 5 triples
for triple in example_triples:
    print(triple)
