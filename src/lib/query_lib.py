from config import LOG_REFERENCES as log, EKG_REFERENCES as ekg
from lib.grammar import *
        
## GRAPH CREATION ##

def get_indexes_q():
    return "SHOW INDEXES"

def drop_index_q(index_name):
    return f"DROP INDEX {index_name}"

def create_index_q(node_type, index_name):
    return f"CREATE INDEX FOR (n:{node_type}) ON (n.{index_name})"

def infer_corr_q(entity : str):
    return (f"""
        MATCH (e:Event)
        WHERE e.{entity} IS NOT NULL AND e.{entity} <> "null"
        WITH split(e.{entity}, ',') AS items, e
        UNWIND items AS entity_id
        WITH entity_id, e
        MATCH (t:Entity {{{log.entity_id}: entity_id}})
        MERGE (e)-[:CORR {{{ekg.type_tag}: '{entity}'}}]->(t)
    """)
    
def infer_df_q(entity : str):
    return (f"""
        MATCH (n:Entity {{{ekg.type_tag}: '{entity}'}})<-[:CORR]-(e)
        WITH n, e AS nodes ORDER BY e.eventDatetime, ID(e)
        WITH n, collect(nodes) AS event_node_list
        UNWIND range(0, size(event_node_list)-2) AS i
        WITH n, event_node_list[i] AS e1, event_node_list[i+1] AS e2
        MERGE (e1)-[df:DF {{Type:n.{ekg.type_tag}, ID:n.{log.entity_id}, edge_weight: 1}}]->(e2)
        """)

def load_log_q(node_type, path : str, log_name: str, header_data : list, type = None) -> str:
    data_list = ''
    for data in header_data:
        if 'time' in data:
            data_list += ', {}: datetime(line.{})'.format(
                data,data)
        else:
            data_list += ', {}: line.{}'.format(data, data)
    
    if type:
        data_list += f', {ekg.type_tag}: "{type}"'

    load_query = f'LOAD CSV WITH HEADERS FROM "file:///{path}" as line CREATE (e:{node_type} {{Log: "{log_name}" {data_list} }})'

    data = data_list.split(', ')
    data.pop(0)  # the first occurrence is empty
    data_dict = {}
    for el in data:
        res = el.split(': ')
        data_dict[res[0]] = res[1]

    return load_query

## AGGREGATION ##

def translate_aggr_function(attr: str, func: AggregationFunction):
    ''' Translate aggregation functions to Neo4j Cypher syntax 
    (Note that some attributes types are not compatible with aggregation functions. E.g., _sum_ or _avg_ does not work with timestamps) '''
    if func == AggregationFunction.SUM:
        return f"sum({attr})"
    elif func == AggregationFunction.AVG:
        return f"avg({attr})"
    elif func == AggregationFunction.MIN:
        return f"min({attr})"
    elif func == AggregationFunction.MAX:
        return f"max({attr})"
    elif func == AggregationFunction.MINMAX:
        return [f"min({attr})",f"max({attr})"]
    elif func == AggregationFunction.MULTISET:
        return f""" COLLECT(n.{attr}) AS attrList
                UNWIND attrList AS att
                WITH c, att, COUNT(att) AS attrCount
                WITH c, COLLECT(att + ':' + attrCount) """
    else:
        raise ValueError(f"Unsupported function: {func}")


def generate_cypher_from_step_q(step: AggrStep) -> str:
    '''
    Convert an aggregation step to a Cypher query
    '''
    node_type = "Event" if step.aggr_type == "EVENTS" else "Entity"
    match_clause = f"MATCH (n:{node_type})"
    
    of_clause = f"WHERE n.{ekg.type_tag} = '{step.ent_type}'" if step.ent_type else ""
    
    where_clause = f"WHERE {step.where}" if step.where else ""
    
    class_query = aggregate_nodes(node_type, step.group_by)
              
    clauses = [match_clause, of_clause, where_clause, class_query]
    cypher_query = "\n".join(clause for clause in clauses if clause)
    print(cypher_query)
    return cypher_query.strip()


def aggregate_nodes(node_type: str, group_by: List[str]) -> str:
    '''
    Cypher query construction for _nodes_ aggregation
    '''
    aliased_attrs = [f"n.{attr} AS {attr}" for attr in group_by]
    group_keys_clause = "WITH DISTINCT n, " + ", ".join(aliased_attrs)

    # Build a value based on distinct values of the group_by attributes
    val_expr = ' + "_" + '.join(group_by) # will be used to create a unique value for the node
    agg_type = "_".join(group_by) # will be used to create a type for the node
    new_val = ', '.join(group_by) + f", {val_expr} AS val"
    
    aggr_expressions = []
    merge_props = [] 

    with_aggr = f"WITH n, {new_val}"

    merge_clause = ""
    if node_type == "Event":
        merge_clause = (
            f'MERGE (c:Class {{ Name: val, Origin: "{node_type}", ID: val, Agg: "{agg_type}"'
            + (", " + ", ".join(merge_props) if merge_props else "")
            + " })"
        )
    elif node_type == "Entity":
        merge_clause = (
            f'MERGE (c:Class {{ Name: val, {ekg.type_tag}: n.{ekg.type_tag}, Origin: "{node_type}", ID: val, Agg: "{agg_type}"'
            + (", " + ", ".join(merge_props) if merge_props else "")
            + " })"
        )
   
    obs_clause = 'WITH n,c \nMERGE (n)-[:OBS]->(c)'

    # Build the query
    cypher_query_parts = [group_keys_clause, with_aggr, merge_clause]

    # Conditionally add the match_event if aggr_expressions exist
    if aggr_expressions:
        prop_val = ", ".join(f"{attr} : {attr}" for attr in group_by)
        vars = ', '.join(group_by)
        cypher_query_parts.append(f"WITH c, {vars}")
        cypher_query_parts.append(f"MATCH (n:Event {{{prop_val}}})")

    # Add the obs_clause at the end
    cypher_query_parts.append(obs_clause)

    # Join all 
    cypher_query = "\n".join(cypher_query_parts)

    return cypher_query

def aggregate_attributes(aggr_type, attribute, agg_func):
    '''Aggregate attributes of nodes'''
    node_type = "Event" if aggr_type == "EVENTS" else "Entity"
    t_function = translate_aggr_function(attribute, agg_func)
    
    return (f'''
            MATCH (n:{node_type})-[:OBS]->(c:Class)
            WITH c, {t_function} AS val
            SET c.{attribute} = val
            ''')

def finalize_c_q(node_type: str):
    if node_type == "Event":
        return(f'''
                MATCH (n:Event)
                WHERE  NOT EXISTS((n)-[:OBS]->())
                WITH n
                CREATE (c:Class {{ Name: n.{log.event_activity}, Origin: 'Events', ID: n.{log.event_id}, Agg: "singleton"}})
                WITH n,c
                MERGE (n)-[:OBS]->(c)
                ''')
    elif node_type == "Entity":    
        return(f'''
                MATCH (n:Entity)
                WHERE  NOT EXISTS((n)-[:OBS]->())
                WITH n
                CREATE (c:Class {{ Name: n.{log.entity_id}, {ekg.type_tag}: n.{ekg.type_tag}, Origin: 'Entities', ID: n.{log.entity_id}, Agg: "singleton"}})
                WITH n,c
                MERGE (n)-[:OBS]->(c)
                ''')
        
def generate_df_c_q():
    return (f'''
        MATCH ( c1 : Class ) <-[:OBS]- ( e1 : Event ) -[df:DF]-> ( e2 : Event ) -[:OBS]-> ( c2 : Class )
        MATCH (e1) -[:CORR] -> (n) <-[:CORR]- (e2)
        WHERE c1.{ekg.type_tag} = c2.{ekg.type_tag} AND n.{ekg.type_tag} = df.{ekg.type_tag}
        WITH n.{ekg.type_tag} as EType,c1,count(df) AS df_freq,c2
        MERGE ( c1 ) -[rel2:DF_C {{EntityType:EType}}]-> ( c2 ) 
        ON CREATE SET rel2.count=df_freq
        ''')

def generate_corr_c_q():
    return (f'''
        MATCH ( c1 : Class ) <-[:OBS]- ( e1 : Event ) -[df:DF]-> ( e2 : Event ) -[:OBS]-> ( c2 : Class )
        MATCH (e1) -[:CORR] -> (n) <-[:CORR]- (e2)
        WHERE c1.{ekg.type_tag} = c2.{ekg.type_tag} AND n.{ekg.type_tag} = df.{ekg.type_tag}
        WITH n.{ekg.type_tag} as EType,c1,count(df) AS df_freq,c2
        MERGE ( c1 ) -[rel2:DF_C {{EntityType:EType}}]-> ( c2 ) 
        ON CREATE SET rel2.count=df_freq
        ''')