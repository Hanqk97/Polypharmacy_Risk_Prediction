import requests as rq

def run_node_normalizer(curie):

    curie_url = curie.replace(":","%3A")

    URL = f"https://nodenormalization-sri.renci.org/1.5/get_normalized_nodes?curie={curie_url}&conflation=true&drug_chemical_conflation=true&description=false"
    response =rq.get(url = URL)
    try:
        if response.status_code == 200:
            response_json = response.json()
            identifier = response_json[curie]["id"]["identifier"]
            name = response_json[curie]["id"]["label"]
        else: 
            identifier = None
            name = None
    except:
        identifier = "None"
        name = "None"
    return identifier, name
    
twosides_df = pd.read_csv('TWOSIDES.csv')
rxcui_list_1 = ["RXCUI:"+str(x) for x in twosides_df['drug_1_rxnorm_id'].to_list()]
rxcui_list_2 = ["RXCUI:"+str(x) for x in twosides_df['drug_2_rxnorm_id'].to_list()]
meddra_list_3 = ["MEDDRA:"+str(x) for x in twosides_df['condition_meddra_id'].to_list()]
normalizedIDs = []
normalizedNames = []
for rxcui_1, rxcui_2, meddra in zip(rxcui_list_1,rxcui_list_2,meddra_list_3):
    normalized_drug_1_info = run_node_normalizer(rxcui_1)
    normalized_drug_2_info = run_node_normalizer(rxcui_2)
    normalized_meddra_info = run_node_normalizer(meddra)
    normalizedIDs.append((normalized_drug_1_info[0],normalized_drug_2_info[0],normalized_meddra_info[0]))
    normalizedNames.append((normalized_drug_1_info[1],normalized_drug_2_info[1],normalized_meddra_info[1]))
    time.sleep(0.1)
twosides_df['normalized_drug_1_rxnorm_id'] = [x[0] for x in normalizedIDs]
twosides_df['normalized_drug_2_rxnorm_id'] = [x[1] for x in normalizedIDs]
twosides_df['normalized_condition_meddra_id'] = [x[2] for x in normalizedIDs]
twosides_df['normalized_drug_1_concept_name'] = [x[0] for x in normalizedNames]
twosides_df['normalized_drug_2_concept_name'] = [x[1] for x in normalizedNames]
twosides_df['normalized_condition_concept_name'] = [x[2] for x in normalizedNames]
    
file_path = "normalized_TWOSIDES.csv"
twosides_df.to_csv(file_path)

