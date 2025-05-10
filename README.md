# Query Library  

A query library for executing and managing EKG aggregation queries.  

## 🛠️ Setup  

First, create a virtual environment and activate it:  

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

## 🔧 Configuration
Before running the application, you need to customize the YAML configuration files:

* `ekg_config.yaml`: Defines database connections, and EKG properties.

* `log_config.yaml`: Manages event data configurations (paths, attributes, etc.).

## 📦 Package Structure  

```
query_library/
├── src/
│   ├── lib/
│   │   ├── aggregate_ekg.py    
│   │   ├── grammar.py         
│   │   └── init_ekg.py               
│   ├── __init__.py               
│   ├── config.py
│   ├── ekg_config.yaml
│   └── log_config.yaml 
├── setup.py                  # Setup configuration
└── README.md                 # This file
```