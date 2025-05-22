# Aggregation Query Library  

A query library for specifying and executing EKG aggregation queries.  

## 🛠️ Setup  

Clone the repo:

```bash
git clone https://github.com/SaraPettinari/ekg_aggregation_lib.git
```

Navigate inside the repo:

```bash
cd <YOUR_PATH>/ekg_aggregation_lib
```

Create a virtual environment and activate it:  

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install python dependencies:
```bash
pip install -r requirements.txt
```

Next, install the package in editable mode:
```bash
pip install -e .
```

## ⚙️ Run
Navigate into a dataset folder:

```bash
cd datasets/<dataset_name>
``` 

Set up the aggregation steps inside `main.py`, then run it:

```bash
python main.py
```

Make sure you configure the required `.yaml` files before running the script, as described in the [Configuration](#-configuration) section.



## 🔧 Configuration

>[!IMPORTANT]
> Before running the application, you must customize the YAML configuration files with your own data.

Required Configuration Files:
* `ekg_config.yaml`: Defines database connections, and EKG properties.

* `log_config.yaml`: Manages event data configurations (paths, attributes, etc.).


### Templates

`log_config.yaml`

```yaml
event_id: "<EVENT_ID_REF>"    # unique identifier attribute for the event
event_activity: "<EVENT_ACTIVITY_REF>"   # activity attribute name of the event
event_timestamp: "<EVENT_TIME_REF>"    # timestamp attribute name of the event

entity_id: "<ENTITY_ID_REF>"   # unique identifier attribute for the entity

events:
  path: "<YOUR_PATH_TO_EVENTS_CSV>"    # path to the event table
  attr: ["<EVENT_ATTRS>"]   # attributes to retrieve from the event table
  attr_types: # not needed if the attribute is of string type
  # supported types so far: String, Integer, Datetime, Float, Boolean
    attr_1: "<TYPE_1>"
    attr_2: "<TYPE_2>"
    # add more attributes as needed
    # attr_name: "<TYPE>"

# entities data: type, path (absolute), and attributes
entities:
  entity_1:
    type: "<ENTITY_TYPE_1>"
    path: "<YOUR_PATH_TO_ENTITY_1>"
    attr: ["<ENTITY_1_ATTRS>"]
    attr_types: 
      attr_1: "<TYPE_1>"
      attr_2: "<TYPE_2>" 
  entity_2:
    type: "<ENTITY_TYPE_2>"
    path: "<YOUR_PATH_TO_ENTITY_2>"
    attr: ["<ENTITY_2_ATTRS>"]
    attr_types: 
      attr_1: "<TYPE_1>"
      attr_2: "<TYPE_2>"
```

`ekg_config.yaml`

```yaml
type_tag: "<TYPE_REF>"    # how the Type of an entity, df, class, etc. is called


# Neo4j configuration
neo4j:
  URI: "<Neo4j-URI>"
  username: "<USERNAME>"
  password: "<PASSWORD>"
```


## 📦 Package Structure  

```
query_library/
├── src/
│   ├── aggregation_lib/
│   │   ├── aggregate_ekg.py
│   │   ├── collect_info_decorator.py    
│   │   ├── grammar.py         
│   │   └── init_ekg.py               
│   ├── __init__.py  
├── datasets/
│   ├── {dataset}/
│   │   ├── config.py
│   │   ├── main.py           # Executable file
│   │   ├── ekg_config.yaml
│   │   └──  log_config.yaml 
├── setup.py                  # Python setup configuration
└── README.md                 
```

## Datasets

### Object-centric

* _OCEL2.0 Datasets_: downloaded from [ocelot](https://ocelot.pm/), based on the [ocel-standard](https://www.ocel-standard.org/event-logs/overview/) ➡️ `logistics`, `order management`, `procure-to-pay (p2p)`.

* _Soccer Matches Dataset_: available on [github](https://github.com/SaraPettinari/soccer_data_pm).

### BPIC 

* _BPIC Datasets_: imported via the [PromG library](https://github.com/PromG-dev). 