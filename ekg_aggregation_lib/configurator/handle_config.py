from ..configurator.knowledge import knowledge

class HandleConfig:
    def __init__(self, session):
        self.log = knowledge.log
        self.ekg = knowledge.ekg
        
        self.session = session

                
    def load_entities_in_log_config(self):
        query = "MATCH (e:Entity) WITH DISTINCT e.Type as EType RETURN EType" if self.ekg.entity_type_mode == "property" \
            else "MATCH (e:Entity) WITH DISTINCT labels(e)[1] as EType RETURN EType"
        self.log.entities = []
        
        resp = self.session.run(query).data()
        for record in resp:
            self.log.entities.append(record['EType'])
        
        knowledge.log = self.log
        
  