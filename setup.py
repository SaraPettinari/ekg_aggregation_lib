from setuptools import setup, find_packages

setup(
    name='aggregation_lib',  
    version='0.1.0',  
    author='Sara Pettinari',  
    author_email='sara.pettinari@gssi.it',  
    description='An aggregation query library for Event Knowledge Graphs',  
    long_description_content_type='text/markdown',  
    url='https://github.com/SaraPettinari/ekg_aggregation_lib', 
    install_requires=[  
        'pyyaml', 'neo4j', 'pandas', 'numpy'
    ],
    python_requires='>=3.7', 
    packages=find_packages(
            where='src'),
        package_dir={"": "src"}
)
