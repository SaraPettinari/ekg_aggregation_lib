from grammar import *
from config import LOG_REFERENCES as log, EKG_REFERENCES as ekg
from neo4j import GraphDatabase


with GraphDatabase.driver(ekg.neo4j.URI, auth=(ekg.neo4j.username,ekg.neo4j.password)) as driver:
    driver.verify_connectivity()
session = driver.session(database="neo4j")

def translate_aggr_function(attr: str, func: AggregationFunction):
    '''
    Translate aggregation functions to Neo4j Cypher syntax
    '''
    if func == AggregationFunction.SUM:
        return f"sum({attr})"
    elif func == AggregationFunction.AVG:
        return f"avg({attr})"
    elif func == AggregationFunction.MIN:
        return f"min({attr})"
    elif func == AggregationFunction.MAX:
        return f"max({attr})"
    elif AggregationFunction.MINMAX:
        return [f"min({attr})",f"max({attr})"]
    elif AggregationFunction.MULTISET: # TODO
        return f"({attr})"
    else:
        raise ValueError(f"Unsupported function: {func}")


def generate_cypher_from_step(step: AggrStep) -> str:
    '''
    Convert an aggregation step to a Cypher query
    '''
    node_type = "Event" if step.aggr_type == "EVENTS" else "Entity"
    match_clause = f"MATCH (n:{node_type})"
    
    of_clause = f"WHERE n.{ekg.type_tag} = '{step.ent_type}'" if step.ent_type else ""
    
    where_clause = f"WHERE {step.where}" if step.where else ""
    
    class_query = aggregate_nodes(step.aggr_type.capitalize(), step.group_by, step.attr_aggrs)
    
    aggr_parts = []
    for attr_aggr in step.attr_aggrs:
        aggr_parts.extend(translate_aggr_function(attr_aggr.name, attr_aggr.function))
                
    clauses = [match_clause, of_clause, where_clause, class_query]
    cypher_query = "\n".join(clause for clause in clauses if clause)
    return cypher_query.strip()


def aggregate_nodes(node_type: str, group_by: List[str], attr_aggrs: List[str]) -> str:
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

    if attr_aggrs:
        for attr_aggr in attr_aggrs:
            group_keys_clause += f", n.{attr_aggr.name} AS {attr_aggr.name}"
            exprs = translate_aggr_function(attr_aggr.name, attr_aggr.function)

            # Handle both lists and strings
            if isinstance(exprs, list):
                expr = f"[{', '.join(exprs)}] AS {attr_aggr.name}"
                aggr_expressions.append(expr)
                merge_props.append(f"{attr_aggr.name.capitalize()}: {attr_aggr.name}")
            else:
                expr = f"{exprs} AS {attr_aggr.name}"
                aggr_expressions.append(expr)
                merge_props.append(f"{attr_aggr.name.capitalize()}: {attr_aggr.name}")

    # add values aggregations in WITH clause
    if aggr_expressions:
        with_aggr = (
            f"WITH {new_val}, " + ", ".join(aggr_expressions)
        )
    else:
        with_aggr = f"WITH n, {new_val}"

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


def generate_df_c_query():
    return f'''
        MATCH ( c1 : Class ) <-[:OBS]- ( e1 : Event ) -[df:DF]-> ( e2 : Event ) -[:OBS]-> ( c2 : Class )
        MATCH (e1) -[:CORR] -> (n) <-[:CORR]- (e2)
        WHERE c1.{ekg.type_tag} = c2.{ekg.type_tag} AND n.{ekg.type_tag} = df.{ekg.type_tag}
        WITH n.{ekg.type_tag} as EType,c1,count(df) AS df_freq,c2
        MERGE ( c1 ) -[rel2:DF_C {{EntityType:EType}}]-> ( c2 ) 
        ON CREATE SET rel2.count=df_freq
        '''

def generate_corr_c_query():
    return f'''
        MATCH ( c1 : Class ) <-[:OBS]- ( e1 : Event ) -[df:DF]-> ( e2 : Event ) -[:OBS]-> ( c2 : Class )
        MATCH (e1) -[:CORR] -> (n) <-[:CORR]- (e2)
        WHERE c1.{ekg.type_tag} = c2.{ekg.type_tag} AND n.{ekg.type_tag} = df.{ekg.type_tag}
        WITH n.{ekg.type_tag} as EType,c1,count(df) AS df_freq,c2
        MERGE ( c1 ) -[rel2:DF_C {{EntityType:EType}}]-> ( c2 ) 
        ON CREATE SET rel2.count=df_freq
        '''

def finalize_c_query():
    print("Finalizing Class nodes ...")
    event_singleton_query = f'''
                        MATCH (n:Event)
                        WHERE  NOT EXISTS((n)-[:OBS]->())
                        WITH n
                        CREATE (c:Class {{ Name: n.{log.event_activity}, Origin: 'Events', ID: n.{log.event_id}, Agg: "singleton"}})
                        WITH n,c
                        MERGE (n)-[:OBS]->(c)
                        '''
    session.run(event_singleton_query)
    
    entity_singleton_query =f'''
                        MATCH (n:Entity)
                        WHERE  NOT EXISTS((n)-[:OBS]->())
                        WITH n
                        CREATE (c:Class {{ Name: n.{log.entity_id}, {ekg.type_tag}: n.{ekg.type_tag}, Origin: 'Entities', ID: n.{log.entity_id}, Agg: "singleton"}})
                        WITH n,c
                        MERGE (n)-[:OBS]->(c)
    '''
    session.run(entity_singleton_query)
    print("Node finalization aggregation query executed successfully.")
    

def one_step_agg(step: AggrStep) -> str:
    '''
    Execute a single aggregation step
    '''
    cypher_query = generate_cypher_from_step(step)
    #print(cypher_query)
    print(f"Executing node aggregation query for {step}...")
    session.run(cypher_query)
    print("Node aggregation query executed successfully.")
    
def aggregate(aggr_spec: AggrSpecification) -> str:
    for step in aggr_spec.steps:
        one_step_agg(step)
    finalize_c_query()
    return "\n\nUNION\n\n".join(generate_cypher_from_step(step) for step in aggr_spec.steps)


if __name__ == "__main__":
    # Example 
    step1 = AggrStep(aggr_type="ENTITIES", ent_type= "teamId", group_by=["country"], where=None, attr_aggrs=[])
    step2 = AggrStep(aggr_type="ENTITIES", ent_type= "playerId", group_by=["role"], where=None, attr_aggrs=[])
    step3 = AggrStep(aggr_type="EVENTS", ent_type= None, where=None, group_by=[log.event_activity, "teamId","playerId"], 
                     attr_aggrs=[AttrAggr(name=log.event_timestamp, function=AggregationFunction.MINMAX)])
    
    aggr_spec = AggrSpecification(steps=[step1])
    
    cypher_query = aggregate(aggr_spec)
    #print(cypher_query)
    
    session.close()
    driver.close()