import os
import time
import pandas as pd
from lib.init_ekg import InitEkg
from lib.aggregate_ekg import AggregateEkg
from lib.grammar import *
from config import LOG_REFERENCES as log

out_measurements_path = os.path.join(os.getcwd(), 'validation')
if not os.path.exists(out_measurements_path):
    os.makedirs(out_measurements_path)

def init_db():
    ''' Initialize the EKG by loading nodes and relationships '''
    init_ekg = InitEkg()
    init_ekg.load_all() 
    init_ekg.create_indexes()
    time.sleep(5) # wait for the session to be free
    init_ekg.create_rels()

def aggregate_ekg(aggr_spec: AggrSpecification):
    ''' Aggregate the EKG using the given specification steps'''
    aggregate_ekg = AggregateEkg()
    aggregate_ekg.aggregate(aggr_spec)
    aggregate_ekg.infer_rels()
    
    pd.DataFrame.from_dict(aggregate_ekg.benchmark, orient='index', columns=['Time (s)']).to_csv(os.path.join(out_measurements_path,'benchmark.csv'))
    pd.DataFrame.from_dict(aggregate_ekg.verification, orient='index').to_csv(os.path.join(out_measurements_path,'verification.csv'))  
        
                
        
def main(first_load : False):
    if first_load:
        init_db()
        
    ## < CONFIGURE HERE THE AGGREGATION STEPS > ##
    step1 = AggrStep(aggr_type="ENTITIES", ent_type= "teamId", group_by=["country"], where=None, attr_aggrs=[AttrAggr(name='city', function=AggregationFunction.MULTISET)])
    step2 = AggrStep(aggr_type="ENTITIES", ent_type= "playerId", group_by=["role"], where='birthYear > 1990', attr_aggrs=[])
    step3 = AggrStep(aggr_type="EVENTS", ent_type= None, where=None, group_by=[log.event_activity, "teamId","playerId"], 
                     attr_aggrs=[AttrAggr(name=log.event_timestamp, function=AggregationFunction.MINMAX),
                                 AttrAggr(name="matchId", function=AggregationFunction.MULTISET)])
    
    aggr_spec = AggrSpecification(steps=[step1,step3])
    aggregate_ekg(aggr_spec)


    
    
if __name__ == "__main__":
    main(first_load=False) # first_load = True means that the database will be initialized and the nodes/rels will be loaded