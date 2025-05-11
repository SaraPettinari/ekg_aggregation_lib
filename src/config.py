import os
import yaml
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class NodeConfig:
    path: str
    attr: List[str]
    type: Optional[str] = None

@dataclass
class LogReferences:
    event_id: str
    event_activity: str
    event_timestamp: str
    entity_id: str
    events: NodeConfig
    entities: Dict[str, NodeConfig]

    
@dataclass
class Neo4jConfig:
    URI: str
    username: str
    password: str

@dataclass
class EKGReferences:
    type_tag: str
    neo4j: Neo4jConfig
    
    
# Load YAML files
curr_path = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(curr_path,'log_config.yaml'), 'r') as file:
    log_data = yaml.safe_load(file)

with open(os.path.join(curr_path, 'ekg_config.yaml'), 'r') as file:
    ekg_data = yaml.safe_load(file)

log_data['events'] = NodeConfig(**log_data['events'])

log_data['entities'] = {
    k: NodeConfig(**v) for k, v in log_data['entities'].items()
}

ekg_data['neo4j'] = Neo4jConfig(**ekg_data['neo4j'])

# Instantiate configurations
LOG_REFERENCES = LogReferences(**log_data)
EKG_REFERENCES = EKGReferences(**ekg_data)
