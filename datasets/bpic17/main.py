import os
from ekg_aggregation_lib import run_pipeline, AggrSpecification, AggrStep

def build_aggr_spec(log, ekg):
    aggr_basic0 = [
        AggrStep(aggr_type="EVENTS", ent_type= None, group_by=[log.event_activity], where=None, attr_aggrs=[])]
    
    return AggrSpecification(aggr_basic0)

if __name__ == "__main__":

    this_dir = os.path.dirname(os.path.abspath(__file__))
    run_pipeline(
        config_dir=os.path.join(this_dir),
        out_dir=os.path.join(this_dir, 'validation'),
        aggr_spec_fn=build_aggr_spec,
        first_load=False # True, if it's the first time running the pipeline (to load the data from the source files
    )
