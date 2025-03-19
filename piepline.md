
#  Polypharmacy Risk Prediction Pipeline using HRKG & HINGE

##  Overview
This pipeline takes a **list of drugs** as input, checks for **existing hyper-relations** in a **Hyper-Relational Knowledge Graph (HRKG)**, and if no match is found, it **predicts missing hyper-relations** using **HINGE (Hyper-Relational KG Embeddings)**.

---

##  Input: User Provides a List of Drugs
Example input:
```python
["DrugA", "DrugB", "DrugC"]
```
Extract all **drug pairs**:

```python
from itertools import combinations

drug_list = ["DrugA", "DrugB", "DrugC"]
drug_pairs = list(combinations(drug_list, 2))
print(drug_pairs)  # [('DrugA', 'DrugB'), ('DrugA', 'DrugC'), ('DrugB', 'DrugC')]
```

------

## Query Neo4j to Find Existing Hyper-Relations

- **If (DrugA, DrugB) exists in HRKG, return it.**
- **Query for hyper-relations with qualifiers in Neo4j:**

```cypher
MATCH (d1:Drug)-[:INTERACTS_WITH]->(d2:Drug)-[:HAS_ATTRIBUTE]->(attr)
WHERE d1.name = "DrugA" AND d2.name = "DrugB"
RETURN d1, d2, attr.adverseEvent AS AdverseEvent
```

**Python function to query Neo4j:**

```python
from neo4j import GraphDatabase

class HRKGQuery:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def find_hyper_relation(self, drugA, drugB):
        query = """
        MATCH (d1:Drug)-[:INTERACTS_WITH]->(d2:Drug)-[:HAS_ATTRIBUTE]->(attr)
        WHERE d1.name = $drugA AND d2.name = $drugB
        RETURN attr.adverseEvent AS AdverseEvent
        """
        with self.driver.session() as session:
            result = session.run(query, drugA=drugA, drugB=drugB)
            return [record["AdverseEvent"] for record in result]

neo4j_query = HRKGQuery("bolt://localhost:7687", "neo4j", "password")
existing_relations = neo4j_query.find_hyper_relation("DrugA", "DrugB")
print(existing_relations)  # If found, return existing adverse events
```

**If a hyper-relation exists, return it immediately.** ✖ **If not, move to HINGE for prediction.**

------

##  Predict Missing Hyper-Relations with HINGE

- **HINGE needs:** (DrugA, DrugB) + **AdverseEvent candidates**
- Use a **set of known adverse events** .
- **HINGE iterates over each adverse event as a key-value pair** and ranks the most probable hyper-relations.

### ** Train the HINGE Model**

```python
from hinge.model import HINGE
from hinge.data import load_data

dataset = load_data("polypharmacy_hrkg")
hinge_model = HINGE()
hinge_model.train(dataset)
```

### ** Predict New Hyper-Relations Using HINGE**

```python
adverse_events = ["Arthralgia", "Nausea", "Hypertension", "Bleeding Risk", "Headache"]

def predict_hyper_relation(drugA, drugB):
    predictions = []
    for event in adverse_events:
        score = hinge_model.predict((drugA, "interactWith", drugB, {"adverseEvent": event}))
        predictions.append((event, score))
    predictions.sort(key=lambda x: x[1], reverse=True)
    return predictions[:10]

# Example
top_predictions = predict_hyper_relation("DrugA", "DrugB")
print(top_predictions)  # Return top 10 most probable hyper-relations
```

**HINGE scores each possible adverse event** and returns the top-ranked ones. The higher the score, the more likely that **(DrugA, DrugB, {AdverseEvent})** is a real interaction.

------

## **Return the Results**

- **If an exact match exists in Neo4j**, return it.
- **Otherwise, use HINGE predictions.**
- Display the **top 10 possible hyper-relations** with scores.

```python
for drugA, drugB in drug_pairs:
    existing = neo4j_query.find_hyper_relation(drugA, drugB)
    if existing:
        print(f"Existing hyper-relation: ( {drugA}, interactWith, {drugB}, {{adverseEvent: {existing}}} )")
    else:
        predicted = predict_hyper_relation(drugA, drugB)
        print(f"Predicted hyper-relations for ({drugA}, {drugB}): {predicted}")
```

**Final Output Example:**

```
Existing hyper-relation: ( DrugA, interactWith, DrugB, {adverseEvent: Arthralgia} )
Predicted hyper-relations for (DrugA, DrugC):
  - (DrugA, interactWith, DrugC, {adverseEvent: Nausea}, score=0.85)
  - (DrugA, interactWith, DrugC, {adverseEvent: Hypertension}, score=0.81)
  - (DrugA, interactWith, DrugC, {adverseEvent: Bleeding Risk}, score=0.78)
```

------

## TWOSIDES ReadMe


TwoSIDES is a database of drug-drug interaction safety signals mined from the FDA's Adverse Event Reporting System using the same approach as is used to generate OffSIDES. 
```bash
drug_1_rxnorn_id	RxNORM identifier for drug 1
drug_1_concept_name	RxNORM name string for drug 1
drug_2_rxnorm_id	RxNORM identifier for drug 2
drug_2_concept_name	RxNORM name string for drug 3
condition_meddra_id	MedDRA identifier for the side effect
condition_concpet_name	MedDRA name string for the side effect
A			The number of reports for the pair of drugs that report the side effect
B			The number of reports for the pair of drugs that do not report the side effect
C			The number of reports for other PSM matched drugs (including perhaps the single versions of drug 1 or drug 2) that report the side effect
D			The number of reports for other PSM matched drugs and other side effects
PRR			Proportional reporting ratio, PRR=(A/(A+B))/(C/(C+D))
PRR_error      		Error estimate of the PRR
mean_reporting_frequency Proportion of reports for the drug that report the side effect, A/(A+B)
```
------