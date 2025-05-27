import os
import config as config
from aggregation_lib.grammar import *
from aggregation_lib.aggregation_pipeline import run_pipeline

def build_aggr_spec(log, ekg):
    
    step1 = AggrStep(aggr_type="ENTITIES", ent_type= "Container", group_by=["Status"], where=None, attr_aggrs=[AttrAggr(name='id', function=AggregationFunction.MULTISET), AttrAggr(name='Weight', function=AggregationFunction.AVG), 
                                                                                                               AttrAggr(name='Amount_of_Handling_Units', function=AggregationFunction.MINMAX)])
    step2 = AggrStep(aggr_type="EVENTS", ent_type= None, where=None, group_by=[log.event_activity, "Customer_Order"], attr_aggrs=[AttrAggr(name=f'{log.event_timestamp}', function=AggregationFunction.MINMAX)]) 
    step3 = AggrStep(aggr_type="ENTITIES", ent_type= "Vehicle", where='Departure_Date > datetime("2023-12-31T23:59:59")', group_by=[ekg.type_tag], attr_aggrs=[]) # I want to check all the orders after Easter

    return AggrSpecification(steps=[step1, step2,step3])

if __name__ == "__main__":

    this_dir = os.path.dirname(os.path.abspath(__file__))
    run_pipeline(
        config_dir=os.path.join(this_dir),
        out_dir=os.path.join(this_dir, 'validation'),
        aggr_spec_fn=build_aggr_spec,
        first_load=False
    )


