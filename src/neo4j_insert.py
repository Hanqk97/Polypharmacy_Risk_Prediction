import os
import json
from neo4j import GraphDatabase

# Connection parameters – update these as needed
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "12345678"  # Update this to your Neo4j password

def create_database_if_not_exists(driver, db_name):
    """
    Creates a Neo4j database with the given name.
    Note: Creating databases is only available on Neo4j Enterprise edition.
    """
    with driver.session(database="system") as session:
        try:
            session.run(f"CREATE DATABASE {db_name}")
            print(f"Database '{db_name}' created.")
        except Exception as e:
            print(f"Database '{db_name}' might already exist or cannot be created. Error: {e}")

def insert_hyperfacts(driver, db_name, hyperfacts):
    """
    Inserts hyperrelation facts into the Neo4j database.
    Each fact has the format:
      {
          "drug1": <drug_name_1>,
          "relation": "interactWith",
          "drug2": <drug_name_2>,
          "attributes": {
              "adverseEvent": <adverse_event>,
              "PRR": <PRR_value>
          }
      }
    """
    total_facts = len(hyperfacts)
    with driver.session(database=db_name) as session:
        for idx, fact in enumerate(hyperfacts, start=1):
            drug1 = fact.get("drug1")
            drug2 = fact.get("drug2")
            attributes = fact.get("attributes", {})
            adverse_event = attributes.get("adverseEvent")
            prr_value = attributes.get("PRR", 0)  # Default to 0 if missing
            
            # Escape apostrophes in the condition name
            safe_adverse_event = adverse_event.replace("'", "\\'")  # Proper escaping for Neo4j
            
            query = """
            MERGE (d1:Drug {name: $drug1})
            MERGE (d2:Drug {name: $drug2})
            MERGE (d1)-[r:INTERACT_WITH {adverseEvent: $adverse_event, PRR: $prr_value}]->(d2)
            MERGE (d2)-[r2:INTERACT_WITH {adverseEvent: $adverse_event, PRR: $prr_value}]->(d1)
            RETURN d1, d2, r, r2
            """
            
            session.run(query, 
                        drug1=drug1, 
                        drug2=drug2, 
                        adverse_event=adverse_event, 
                        prr_value=prr_value)
            
            print(f"[{idx}/{total_facts}] Inserted: {drug1} ↔ {drug2} → {adverse_event} (PRR: {prr_value})")

def insert_hyperfacts_from_json(json_path):
    """
    Given a JSON file containing hyperrelation facts, this function:
      1. Derives the target database name from the JSON file's folder.
      2. Connects to a local Neo4j instance.
      3. Creates the database if it doesn't exist.
      4. Inserts hyperrelation facts into the database with progress messages.
    """
    # Derive the database name from the JSON file path.
    output_path = os.path.dirname(json_path)
    db_name = os.path.basename(os.path.normpath(output_path))
    print(f"Derived database name from JSON path: '{db_name}'")

    # Load hyperrelation facts from the JSON file.
    with open(json_path, "r") as f:
        hyperfacts = json.load(f)
    print(f"Loaded {len(hyperfacts)} hyperrelation facts from '{json_path}'.")

    # Create a Neo4j driver instance.
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    print(f"Connected to Neo4j at {NEO4J_URI}")

    # Create the target database if it does not already exist.
    create_database_if_not_exists(driver, db_name)

    # Insert hyperrelation facts with progress output.
    insert_hyperfacts(driver, db_name, hyperfacts)

    driver.close()
    print("Neo4j connection closed.")

if __name__ == "__main__":
    # Specify the path to your hyperfacts JSON file.
    json_file_path = "./output/test/hyperfacts.json"

    # json_file_path = "./output/split_raw_twosides/hyperfacts.json"
    insert_hyperfacts_from_json(json_file_path)
