import os
import time
import pandas as pd
import config as config

from aggregation_lib.init_ekg import InitEkg
from aggregation_lib.aggregate_ekg import AggregateEkg
from aggregation_lib.grammar import *

def run_pipeline(config_dir: str, out_dir: str, aggr_spec_fn, first_load: bool = False):
    # Load config from the specified directory
    config.load_configs(config_dir)
    log = config.get_log_config()
    ekg = config.get_ekg_config()

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
        aggregator = AggregateEkg()
        aggregator.aggregate(aggr_spec)
        aggregator.infer_rels()

        df = pd.DataFrame.from_dict(aggregator.benchmark, orient='index', columns=['Time (s)'])
        df.index.name = 'step'
        df.to_csv(os.path.join(out_dir, 'benchmark.csv'))
        
        df = pd.DataFrame.from_dict(aggregator.verification, orient='index')
        df.index.name = 'step'
        df.to_csv(os.path.join(out_dir, 'verification.csv'))

    if first_load:
        init_db()

    aggr_spec = aggr_spec_fn(log, ekg)
    aggregate_ekg(aggr_spec)
