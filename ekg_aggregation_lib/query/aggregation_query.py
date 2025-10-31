from ..aggregation.grammar import *
from ..configurator.knowledge import knowledge

def EKG():
    return knowledge.ekg

def LOG():
    return knowledge.log


def translate_aggr_function(attr: str, func: AggregationFunction):
    ''' Translate aggregation functions to Neo4j Cypher syntax 
    (Note that some attributes types are not compatible with aggregation functions. E.g., _sum_ or _avg_ does not work with timestamps) '''
    if func == AggregationFunction.SUM:
        return f"sum(n.{attr})"
    elif func == AggregationFunction.AVG:
        return f"avg(n.{attr})"
    elif func == AggregationFunction.MIN:
        return f"min(n.{attr})"
    elif func == AggregationFunction.MAX:
        return f"max(n.{attr})"
    elif func == AggregationFunction.MINMAX:
        return [f"min(n.{attr})",f"max(n.{attr})"]
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
    
    if EKG().entity_type_mode == "label" and node_type == "Entity":
        match_clause = f"MATCH (n:{node_type}:{EKG().type_tag})"
    
    else:
        match_clause = f"MATCH (n:{node_type})"
        
        of_clause = f"WHERE n.{EKG().type_tag} = '{step.ent_type}'" if step.ent_type else ""
       
    prefix = "WHERE" if (node_type == "Event" or EKG().entity_type_mode == 'label') else "AND"
    where_clause = f" {prefix} n.{step.where}" if step.where else ""
    
    class_query = aggregate_nodes(node_type, step.group_by, step.where)
              
    clauses = [match_clause, of_clause, where_clause, class_query]
    cypher_query = "\n".join(clause for clause in clauses if clause)
    #print(cypher_query)
    return cypher_query.strip()


def aggregate_nodes(node_type: str, group_by: List[str], where: str) -> str:
    '''
    Cypher query construction for _nodes_ aggregation
    '''
    if node_type not in ["Event", "Entity"]:    
        raise ValueError(f"Unsupported node type: {node_type}. Supported types are 'Event' and 'Entity'.")
    
    agg_type = "_".join(group_by) # will be used to create a type for the node
    cypher_query_parts = []
    aggr_expressions = []
    
    if node_type == "Event":
        get_query = aggregate_events_with_entities_q(group_by, where) # create a query to aggregate events also considering if entities have already been aggregated
        id = LOG().event_id
        merge_clause = (
            f'MERGE (c:Class {{ Name: val, Origin: "{node_type}", ID: val, Agg: "{agg_type}"'
            + f", Where: '{where if where else ''}'"
            + " })"
        )
        cypher_query_parts = [get_query, merge_clause]
    elif node_type == "Entity":
        aliased_attrs = [f"n.{attr} AS {attr}" for attr in group_by]
        group_keys_clause = "WITH DISTINCT n, " + ", ".join(aliased_attrs)

        # Build a value based on distinct values of the group_by attributes
        val_expr = ' + "_" + '.join([f'COALESCE({field}, "unknown")' for field in group_by]) # will be used to create a unique value for the node
        new_val = ', '.join(group_by) + f", {val_expr} AS val"
        
        with_aggr = f"WITH n, {new_val}"
        id = LOG().entity_id
        merge_clause = (
            f'MERGE (c:Class {{ Name: val, {EKG().type_tag}: n.{EKG().type_tag}, Origin: "{node_type}", ID: val, Agg: "{agg_type}"'
            + f", Where: '{where if where else ''}'"
            + " })"
        )
        with_aggr += f", COLLECT(n.{id}) as ids" # store all ids of the nodes that are aggregated
        cypher_query_parts = [group_keys_clause, with_aggr, merge_clause]
    
    
    create_set = (
    "ON CREATE SET c.Ids = ids, c.Count = size(ids)\n"
    "ON MATCH SET c.Ids = COALESCE(c.Ids, []) + ids, "
    "c.Count = size(COALESCE(c.Ids, []) + ids)"
    )
    
    obs_clause = 'WITH n,c \nMERGE (n)-[:OBS]->(c)'

    # Build the query
    cypher_query_parts.append(create_set)

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

def aggregate_events_with_entities_q(group_by: List[str], where: str):
    entities = []
    for attr in group_by:
        if attr in LOG().entities:
            entities.append(attr)
    
    match = "MATCH (n:Event)"
    variables = 'WITH n'
    coalesce_clause = f", COALESCE(n.{LOG().event_activity}, 'unknown') AS rawEventName"
    var_tags = ['rawEventName']
    for index,entity in enumerate(entities):
        match += f"\nOPTIONAL MATCH (n)-[:CORR]->(e{index}:Entity {{{EKG().type_tag}: '{entity}'}})-[:OBS]->(c{index}:Class)" \
            if EKG().entity_type_mode == 'property' \
                else f"\nOPTIONAL MATCH (n)-[:CORR]->(e{index}:Entity:{entity})-[:OBS]->(c{index}:Class)"
        variables += f', c{index}'
        coalesce_clause += f', COALESCE(c{index}.ID, n.{entity}, "unknown") AS resolved{entity}'
        var_tags.append(f'resolved{entity}')
        
    init_query = '\n'.join([match,variables,coalesce_clause])
    
    coalesced_parts = [f'COALESCE({col}, "unknown")' for col in var_tags]
    coalesced_expression = ' + "_" + '.join(coalesced_parts)
    with_clause = f'WITH n, {coalesced_expression} AS val, COLLECT(n.{LOG().event_id}) AS ids'
    
    return '\n'.join([init_query, with_clause])
    


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
                CREATE (c:Class {{ Name: n.{LOG().event_activity}, Origin: 'Event', ID: n.{LOG().event_id}, Agg: "singleton"}})
                WITH n,c
                MERGE (n)-[:OBS]->(c)
                ''')
    elif node_type == "Entity":
        create_clause = f'''
        CREATE (c:Class {{ Name: n.{LOG().entity_id}, {EKG().type_tag}: n.{EKG().type_tag}, Origin: 'Entity', ID: n.{LOG().entity_id}, Agg: "singleton"}})
        '''    if EKG().entity_type_mode == "property" else f'''
        CREATE (c:Class {{ Name: n.{LOG().entity_id}, {EKG().type_tag}: labels(n)[1], Origin: 'Entity', ID: n.{LOG().entity_id}, Agg: "singleton"}})
        '''
        return(f'''
                MATCH (n:Entity)
                WHERE  NOT EXISTS((n)-[:OBS]->())
                WITH n
                {create_clause}
                WITH n,c
                MERGE (n)-[:OBS]->(c)
                ''')
        
        
def generate_df_c_q():
    where_with_clause = f'''
        WHERE c1.Agg = c2.Agg AND n.{EKG().type_tag} = df.{EKG().type_tag}
        WITH n.{EKG().type_tag} as EType,c1,count(df) AS df_freq,c2
    ''' if EKG().entity_type_mode == "property" \
        else f'''
        WHERE c1.Agg = c2.Agg AND labels(n)[1] = df.{EKG().type_tag}
        WITH labels(n)[1] as EType,c1,count(df) AS df_freq,c2
    '''
    
    return (f'''
        MATCH ( c1 : Class ) <-[:OBS]- ( e1 : Event ) -[df:DF]-> ( e2 : Event ) -[:OBS]-> ( c2 : Class )
        MATCH (e1) -[:CORR] -> (n) <-[:CORR]- (e2)
        {where_with_clause} 
        MERGE ( c1 ) -[rel2:DF_C {{EntityType:EType}}]-> ( c2 ) 
        ON CREATE SET rel2.count=df_freq
        ''')

def generate_corr_c_q():
    return (f'''
        MATCH ( ce : Class ) <-[:OBS]- ( e : Event ) -[corr:CORR]-> ( t : Entity ) -[:OBS]-> ( ct : Class )
        MERGE ( ce ) -[rel2:CORR_C]-> ( ct ) 
        ''')
    

def count_not_aggregated_nodes_q(node_type : str):
    return (f'''
        MATCH (n:{node_type})
        WHERE NOT EXISTS((n)-[:OBS]->())
        RETURN COUNT(n) AS count
        ''')
    
    
    
############# WiP #############
def finalize_c_noobs_q(node_type: str):
    if node_type == "Event":
        return(f'''
                MATCH (class:Class)
                UNWIND class.Ids AS id
                WITH collect(DISTINCT id) AS allIds
                MATCH (n:Event)
                WHERE NOT n.id IN allIds
                CREATE (c:Class {{ Name: n.{LOG().event_activity}, Origin: 'Event', ID: n.{LOG().event_id}, Agg: "singleton", Ids: [n.id]}})
                ''')
    elif node_type == "Entity":    
        return(f'''
               MATCH (class:Class)
                UNWIND class.Ids AS id
                WITH collect(DISTINCT id) AS allIds
                MATCH (n:Entity)
                WHERE NOT n.id IN allIds
                CREATE (c:Class {{ Name: n.{LOG().entity_id}, {EKG().type_tag}: n.{EKG().type_tag}, Origin: 'Entity', ID: n.{LOG().entity_id}, Agg: "singleton", Ids: [n.id]}})
                ''')