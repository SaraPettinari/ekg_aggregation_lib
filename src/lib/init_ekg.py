from config import LOG_REFERENCES as log, EKG_REFERENCES as ekg
from neo4j import GraphDatabase

with GraphDatabase.driver(ekg.neo4j.URI, auth=(ekg.neo4j.username,ekg.neo4j.password)) as driver:
    driver.verify_connectivity()
session = driver.session(database="neo4j")
        
def load_query_generator(node_type, path : str, log_name: str, header_data : list, type = None) -> str:
    data_list = ''
    for data in header_data:
        if 'time' in data:
            data_list += ', {}: datetime(line.{})'.format(
                data,data)
        else:
            data_list += ', {}: line.{}'.format(data, data)
    
    if type:
        data_list += f', {ekg.type_tag}: "{type}"'

    load_query = f'LOAD CSV WITH HEADERS FROM "file:///{path}" as line CREATE (e:{node_type} {{Log: "{log_name}" {data_list} }})'

    data = data_list.split(', ')
    data.pop(0)  # the first occurrence is empty
    data_dict = {}
    for el in data:
        res = el.split(': ')
        data_dict[res[0]] = res[1]

    return load_query


def create_entity_index():
    indexes = session.run("SHOW INDEXES")

        # Iterate over each index and drop it
    for index in indexes:
        index_name = index['name']
        drop_query = f"DROP INDEX {index_name}"
        session.run(drop_query)
        #print(f"Dropped index: {index_name}")
            
    query = (f""" CREATE INDEX FOR (t:Entity) ON (t.{log.entity_id}) """)

    session.run(query)
    
    query = (f""" CREATE INDEX ent_type FOR (t:Entity) ON (t.{ekg.type_tag})  """)
    session.run(query)


def create_event_index() -> str:
    query = (f""" CREATE INDEX FOR (e:Event) ON (e.{log.event_activity}) """)
    session.run(query)
    for entity in log.entities.keys():
        query = (f""" CREATE INDEX FOR (e:Event) ON (e.{entity}) """)
        session.run(query)
        
def infer_corr(entity : str) -> str:
    return (f"""
        MATCH (e:Event)
        WHERE e.{entity} IS NOT NULL AND e.{entity} <> "null"
        WITH split(e.{entity}, ',') AS items, e
        UNWIND items AS entity_id
        WITH entity_id, e
        MATCH (t:Entity {{{log.entity_id}: entity_id}})
        MERGE (e)-[:CORR {{{ekg.type_tag}: '{entity}'}}]->(t)
    """)
    

def infer_df(entity : str):
    return (f"""
        MATCH (n:Entity {{{ekg.type_tag}: '{entity}'}})<-[:CORR]-(e)
        WITH n, e AS nodes ORDER BY e.eventDatetime, ID(e)
        WITH n, collect(nodes) AS event_node_list
        UNWIND range(0, size(event_node_list)-2) AS i
        WITH n, event_node_list[i] AS e1, event_node_list[i+1] AS e2
        MERGE (e1)-[df:DF {{Type:n.{ekg.type_tag}, ID:n.{log.entity_id}, edge_weight: 1}}]->(e2)
        """)
    
    
    
def create_rels():
    for entity in log.entities.keys():
        corr_query = infer_corr(entity)  
        try:
            with session.begin_transaction() as tx:
                print("Executing CORR query...") 
                tx.run(corr_query)
                print("CORR query executed successfully.")
                
        except Exception as e:
            print(f"Error executing query: {e}")
            
        df_query = infer_df(entity)
        try:
            with session.begin_transaction() as tx:
                print("Executing DF query...") 
                tx.run(df_query)
                print("DF query executed successfully.")
        except Exception as e:
            print(f"Error executing query: {e}")
        
        
def all_load() -> str:
    log_name = "oced_ekg"
    
    event_load = load_query_generator(node_type='Event', 
                                      path=log.events.path, 
                                      log_name=log_name, 
                                      header_data=log.events.attr)
    session.run(event_load)
    
    for entity in log.entities.keys():
        entity_load = load_query_generator(node_type='Entity', 
                                            path=log.entities[entity].path, 
                                            log_name=log_name, 
                                            header_data=log.entities[entity].attr,
                                            type=entity)
        #print(f'Entity Query LOAD for {entity}:\n', entity_load)
        session.run(entity_load)

if __name__ == "__main__":
    ## Load Queries
    #all_load()
    print("All LOAD queries executed successfully.")
    ## Index Query
    #create_entity_index()
    #create_event_index()
    print("All INDEX queries executed successfully.")
    ## :CORR Query
    create_rels()
    
    print("All queries executed successfully.")
        
    session.close()
    driver.close()