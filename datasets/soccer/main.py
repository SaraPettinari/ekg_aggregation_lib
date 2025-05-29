import os
import config as config
from aggregation_lib.grammar import *
from aggregation_lib.aggregation_pipeline import run_pipeline


def build_aggr_spec(log, ekg):
    # example 
    aggr_example = [AggrStep(aggr_type="ENTITIES", ent_type= "teamId", group_by=["country"], where=None, attr_aggrs=[AttrAggr(name='city', function=AggregationFunction.MULTISET)]),
                    AggrStep(aggr_type="ENTITIES", ent_type= "playerId", group_by=["role"], where='birthYear > 1990', attr_aggrs=[]),
                    AggrStep(aggr_type="EVENTS", ent_type= None, where=None, group_by=[log.event_activity, "teamId","playerId"], 
                                    attr_aggrs=[AttrAggr(name=log.event_timestamp, function=AggregationFunction.MINMAX),
                                                AttrAggr(name="matchId", function=AggregationFunction.MULTISET)])]
    # running example:
    aggr_running = [AggrStep(aggr_type="ENTITIES", ent_type= "playerId", group_by=["role"], where=None, attr_aggrs=[]),
                    AggrStep(aggr_type="EVENTS", ent_type= None, where=None, group_by=[log.event_activity, "teamId","playerId"], 
                                    attr_aggrs=[AttrAggr(name=log.event_timestamp, function=AggregationFunction.MINMAX),
                                                AttrAggr(name="matchId", function=AggregationFunction.MULTISET)])]
    
    # 4-step:
    aggr_example_2 =[
    AggrStep(aggr_type="ENTITIES", ent_type= "playerId", group_by=["role"], where='birthYear > 1990', attr_aggrs=[]),
    AggrStep(aggr_type="ENTITIES", ent_type= "pos_orig", group_by=["zone"], where=None, attr_aggrs=[]),
    AggrStep(aggr_type="EVENTS", ent_type= None, where='matchId = "2575959"', group_by=[log.event_activity, "teamId","playerId"], 
                     attr_aggrs=[AttrAggr(name=log.event_timestamp, function=AggregationFunction.MINMAX),
                                 AttrAggr(name="teamId", function=AggregationFunction.MULTISET)]),
    AggrStep(aggr_type="EVENTS", ent_type= None, where='matchId <> "2575959"', group_by=[log.event_activity, "teamId","playerId"], 
                     attr_aggrs=[AttrAggr(name=log.event_timestamp, function=AggregationFunction.MINMAX),
                                 AttrAggr(name="teamId", function=AggregationFunction.MULTISET)]) ]
    
    return AggrSpecification(aggr_running)

if __name__ == "__main__":

    this_dir = os.path.dirname(os.path.abspath(__file__))
    run_pipeline(
        config_dir=os.path.join(this_dir),
        out_dir=os.path.join(this_dir, 'validation'),
        aggr_spec_fn=build_aggr_spec,
        first_load=False # True, if it's the first time running the pipeline (to load the data from the source files
    )
