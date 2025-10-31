from ..query import aggregation_query as q_lib
from ..aggregation.grammar import *
from neo4j import GraphDatabase
from ..aggregation.collect_info_decorator import collect_metrics
from ..configurator.knowledge import knowledge

class AggregateEkg:
    def __init__(self):
        self.log = knowledge.log
        self.ekg = knowledge.ekg
        self.neo4j = self.ekg.neo4j

        # init the neo4j driver
        self.driver = GraphDatabase.driver(self.neo4j.URI, auth=(self.neo4j.username, self.neo4j.password))
        self.driver.verify_connectivity()
        self.session = self.driver.session(database="neo4j")
        
        if self.ekg.entity_type_mode == "label":
            from ..configurator.handle_config import HandleConfig
            handler = HandleConfig(self.session)
            handler.load_entities_in_log_config()
            
        # store performances
        self.benchmark = {}
        self.verification = {}
    
    @collect_metrics(lambda _, step: str(step))    
    def one_step_agg(self,step: AggrStep):
        ''' Execute a single aggregation step '''
        print(f"Executing node aggregation query for {step}...")

        cypher_query = q_lib.generate_cypher_from_step_q(step)
        self.session.run(cypher_query)
        # aggregate the attributes if any
        if step.attr_aggrs:
                for attr_aggr in step.attr_aggrs:
                    self.aggregate_attributes(step.aggr_type, attr_aggr.name, attr_aggr.function)
        print("Node aggregation query executed successfully")
        
        
    @collect_metrics('FINALIZATION')    
    def finalize(self):
        ''' Finalize the aggregation by creating the Class nodes for non-aggregated nodes '''
        print("Finalizing Class nodes ...")
        
        event_singleton_query = q_lib.finalize_c_q(node_type="Event")
        self.session.run(event_singleton_query)
                
        entity_singleton_query = q_lib.finalize_c_q(node_type="Entity")
        self.session.run(entity_singleton_query)
        
        print("Node finalization aggregation query executed successfully.")
                
 
    def aggregate_attributes(self, aggr_type: str, attribute: str, agg_func: AggregationFunction):
        ''' Execute the aggregation for the given attribute '''
        print(f"Executing node attribute aggregation ...")
        query = q_lib.aggregate_attributes(aggr_type, attribute, agg_func)
        self.session.run(query)
        print("Attribute aggregation query executed successfully.")
    
    @collect_metrics('TOTAL')
    def aggregate(self, aggr_spec: AggrSpecification):
        ''' Execute the aggregation for the given specification '''
   
        for step in aggr_spec.steps:
            self.one_step_agg(step)
        self.finalize() # finalize the aggregation
        
        print("Node aggregation query executed successfully.")

    @collect_metrics('RELATIONSHIPS')
    def infer_rels(self):
        print("Inferring relationships ...")
        query = q_lib.generate_df_c_q()
        self.session.run(query)
        
        query = q_lib.generate_corr_c_q()
        self.session.run(query)
        
        print("Relationships inferred successfully.")
                    
    def verify_no_aggregated_nodes(self):
        ''' Verify the not aggregated nodes of the EKG '''
        cypher_query = q_lib.count_not_aggregated_nodes_q('Event')
        no_aggr_nodes_events = self.session.run(cypher_query).single()[0]
        cypher_query = q_lib.count_not_aggregated_nodes_q('Entity')
        no_aggr_nodes_entities = self.session.run(cypher_query).single()[0]
        return no_aggr_nodes_events, no_aggr_nodes_entities
        


    
    
