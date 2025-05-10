from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class AggregationFunction(Enum):
    SUM = "SUM"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"
    MINMAX = "MINMAX"
    MULTISET = "MULTISET"

@dataclass
class AttrAggr:
    name: str
    function: AggregationFunction

@dataclass
class AggrStep:
    '''
    Represents a single aggregation step in the query.
    :param aggr_type: Type of aggregation (EVENTS or ENTITIES)
    :param ent_type: Type of entity (optional)
    :param group_by: List of attributes to group by
    :param where: Boolean expression as string (optional)
    :param attr_aggrs: List of attribute aggregations (WITH clause)
    '''
    aggr_type: str  # "EVENTS" or "ENTITIES"
    ent_type: Optional[str]  # Type of entity
    group_by: List[str]
    where: Optional[str]  # Boolean expression as string
    attr_aggrs: List[AttrAggr]

@dataclass
class AggrSpecification:
    steps: List[AggrStep]
