import lib.query_lib as q_lib
from lib.grammar import *
from config import LOG_REFERENCES as log, EKG_REFERENCES as ekg
from neo4j import GraphDatabase


class AggregateEkg:
    def __init__(self):
        self.neo4j = ekg.neo4j
        self.log = log
        self.ekg = ekg

        # init the neo4j driver
        self.driver = GraphDatabase.driver(self.neo4j.URI, auth=(self.neo4j.username, self.neo4j.password))
        self.driver.verify_connectivity()
        self.session = self.driver.session(database="neo4j")
        
    def one_step_agg(self,step: AggrStep):
        ''' Execute a single aggregation step '''
        print(f"Executing node aggregation query for {step}...")
        cypher_query = q_lib.generate_cypher_from_step_q(step)
        self.session.run(cypher_query)
        print("Node aggregation query executed successfully.")
        
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
    
    def aggregate(self, aggr_spec: AggrSpecification):
        query = q_lib.create_index_q('Class', 'Name')
        self.session.run(query)
        
        ''' Execute the aggregation for the given specification '''
        for step in aggr_spec.steps:
            self.one_step_agg(step)
            if step.attr_aggrs:
                for attr_aggr in step.attr_aggrs:
                    self.aggregate_attributes(step.aggr_type, attr_aggr.name, attr_aggr.function)
        self.finalize() # finalize the aggregation
        
        
        print("Node aggregation query executed successfully.")


if __name__ == "__main__":
    aggregation = AggregateEkg()
    
    # Example 
    step1 = AggrStep(aggr_type="ENTITIES", ent_type= "teamId", group_by=["country"], where=None, attr_aggrs=[AttrAggr(name='city', function=AggregationFunction.MULTISET)])
    step2 = AggrStep(aggr_type="ENTITIES", ent_type= "playerId", group_by=["role"], where=None, attr_aggrs=[])
    step3 = AggrStep(aggr_type="EVENTS", ent_type= None, where=None, group_by=[log.event_activity, "teamId","playerId"], 
                     attr_aggrs=[AttrAggr(name=log.event_timestamp, function=AggregationFunction.MINMAX),
                                 AttrAggr(name="matchId", function=AggregationFunction.MULTISET)])
    
    aggr_spec = AggrSpecification(steps=[step1,step3])
    
    aggregation.aggregate(aggr_spec)
