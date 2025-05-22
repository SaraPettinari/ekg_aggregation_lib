import os
import config as config
from aggregation_lib.grammar import *
from aggregation_lib.aggregation_pipeline import run_pipeline

def build_football_spec(log, ekg):
    
    step1 = AggrStep(aggr_type="ENTITIES", ent_type= "teamId", group_by=["country"], where=None, attr_aggrs=[AttrAggr(name='city', function=AggregationFunction.MULTISET)])
    step2 = AggrStep(aggr_type="ENTITIES", ent_type= "playerId", group_by=["role"], where='birthYear > 1990', attr_aggrs=[])
    step3 = AggrStep(aggr_type="EVENTS", ent_type= None, where=None, group_by=[log.event_activity, "teamId","playerId"], 
                     attr_aggrs=[AttrAggr(name=log.event_timestamp, function=AggregationFunction.MINMAX),
                                 AttrAggr(name="matchId", function=AggregationFunction.MULTISET)])

    return AggrSpecification(steps=[step1, step2, step3])

if __name__ == "__main__":

    this_dir = os.path.dirname(os.path.abspath(__file__))
    run_pipeline(
        config_dir=os.path.join(this_dir),
        out_dir=os.path.join(this_dir, 'validation'),
        aggr_spec_fn=build_football_spec,
        first_load=True
    )
