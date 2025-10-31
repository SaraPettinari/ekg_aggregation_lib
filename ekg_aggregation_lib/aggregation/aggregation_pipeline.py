import os
import time, datetime
import pandas as pd
from ..configurator import config
from ..configurator.knowledge import knowledge
from ..aggregation.init_ekg import InitEkg
from ..aggregation.aggregate_ekg import AggregateEkg
from ..aggregation.grammar import *


def run_pipeline(config_dir: str, out_dir: str, aggr_spec_fn, first_load: bool = False):
    # Load config from the specified directory
    config.load_configs(config_dir)
    knowledge.log = config.get_log_config()
    knowledge.ekg = config.get_ekg_config()
    
    log = knowledge.log
    ekg = knowledge.ekg

    # Create output directory if needed
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    def init_db():
        init_ekg = InitEkg()
        init_ekg.load_all()
        init_ekg.create_indexes()
        time.sleep(5)
        init_ekg.create_rels()

    def aggregate_ekg(aggr_spec: AggrSpecification):
        curr_datetime = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        aggregator = AggregateEkg()
        aggregator.aggregate(aggr_spec)
        aggregator.infer_rels()

        df = pd.DataFrame.from_dict(aggregator.benchmark, orient='index', columns=['Time (s)'])
        df.index.name = 'step'
        df.to_csv(os.path.join(out_dir, f'benchmark_{curr_datetime}.csv'))
        
        df = pd.DataFrame.from_dict(aggregator.verification, orient='index')
        df.index.name = 'step'
        df.to_csv(os.path.join(out_dir, f'verification_{curr_datetime}.csv'))

    if first_load:
        init_db()

    aggr_spec = aggr_spec_fn(log, ekg)
    aggregate_ekg(aggr_spec)
