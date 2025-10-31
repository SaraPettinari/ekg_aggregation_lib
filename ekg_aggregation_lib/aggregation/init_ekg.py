from ..configurator.config import get_log_config, get_ekg_config
from neo4j import GraphDatabase
import time
from ..query import init_query as q_lib

class InitEkg:
    def __init__(self):
        log = get_log_config()
        ekg = get_ekg_config()
        self.neo4j = ekg.neo4j
        self.log = log
        self.ekg = ekg
        
        # init the neo4j driver
        self.driver = GraphDatabase.driver(self.neo4j.URI, auth=(self.neo4j.username, self.neo4j.password))
        self.driver.verify_connectivity()
        self.session = self.driver.session(database="neo4j")
    
    def load_all(self):
        ''' Load all the data into the graph '''
        log_name = "oced_ekg"
        
        print("Loading Events and Entities...")
        
        event_load = q_lib.load_log_q(node_type='Event', 
                                        path=self.log.events.path, 
                                        log_name=log_name, 
                                        header_data=self.log.events.attr)
        self.session.run(event_load)
        
        for entity in self.log.entities.keys():
            entity_load = q_lib.load_log_q(node_type='Entity', 
                                                path=self.log.entities[entity].path, 
                                                log_name=log_name, 
                                                header_data=self.log.entities[entity].attr,
                                                type=entity)
            self.session.run(entity_load)
        
        print("All LOAD queries executed successfully.")

        
    def create_indexes(self):
        ''' Create indexes to speed graph searching and manipulation '''
        print("Creating indexes...")
        # first remove all the indexes
        res = self.session.run(q_lib.get_indexes_q()) 
        indexes = res.data()
        
        for index in indexes:
            index_name = index['name']
            self.session.run(q_lib.drop_index_q(index_name))
        
        # create new indexes
        self.session.run(q_lib.create_index_q('Entity', self.log.entity_id))
        self.session.run(q_lib.create_index_q('Entity', self.ekg.type_tag))
        self.session.run(q_lib.create_index_q('Event', self.log.event_activity))
        for entity in self.log.entities.keys():
            self.session.run(q_lib.create_index_q('Event', entity))
            
        query = q_lib.create_index_q('Class', 'Name')
        self.session.run(query)
            
        print("All INDEX queries executed successfully.")
    
    def create_rels(self):
        ''' Create relationships between events and entities '''
        for entity in self.log.entities.keys():
            corr_query = q_lib.infer_corr_q(entity)  
            try:
                with self.session.begin_transaction() as tx:
                    print("Executing CORR query...") 
                    tx.run(corr_query)
                    print("CORR query executed successfully.")
                    
            except Exception as e:
                print(f"Error executing query: {e}")
                
            df_query = q_lib.infer_df_q(entity)
            try:
                with self.session.begin_transaction() as tx:
                    print("Executing DF query...") 
                    tx.run(df_query)
                    print("DF query executed successfully.")
            except Exception as e:
                print(f"Error executing query: {e}")
            
        
if __name__ == "__main__":
    init_ekg = InitEkg()
    init_ekg.load_all() 
    init_ekg.create_indexes()
    time.sleep(5) # wait for the session to be free
    init_ekg.create_rels()
    
    print("All queries executed successfully.")
        
