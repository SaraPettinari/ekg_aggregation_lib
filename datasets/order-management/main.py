import os
import config as config
from aggregation_lib.grammar import *
from aggregation_lib.aggregation_pipeline import run_pipeline

def build_aggr_spec(log, ekg):
    
    step1 = AggrStep(aggr_type="ENTITIES", ent_type= "customers", group_by=["id"], where=None, attr_aggrs=[AttrAggr(name='id', function=AggregationFunction.MULTISET)])
    step2 = AggrStep(aggr_type="ENTITIES", ent_type= "orders", group_by=[ekg.type_tag], where='price >= 1000', attr_aggrs=[AttrAggr(name='price', function=AggregationFunction.AVG)])
    step3 = AggrStep(aggr_type="ENTITIES", ent_type= "employees", group_by=['role'], where=None, attr_aggrs=None)
    step4 = AggrStep(aggr_type="EVENTS", ent_type= None, where=f'{log.event_timestamp} >= datetime("2024-03-31T00:00:00")', group_by=[log.event_activity, "customers", "orders"], attr_aggrs=[]) # I want to check all the orders after Easter
    step5 = AggrStep(aggr_type="EVENTS", ent_type= None, where=f'{log.event_timestamp} < datetime("2024-03-31T00:00:00")', group_by=[log.event_activity, "customers", "orders"], attr_aggrs=[]) # I want to check all the orders before Easter

    return AggrSpecification(steps=[step1, step2, step3,step4,step5])

if __name__ == "__main__":

    this_dir = os.path.dirname(os.path.abspath(__file__))
    run_pipeline(
        config_dir=os.path.join(this_dir),
        out_dir=os.path.join(this_dir, 'validation'),
        aggr_spec_fn=build_aggr_spec,
        first_load=False
    )


