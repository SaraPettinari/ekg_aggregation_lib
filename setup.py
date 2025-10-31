from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name='ekg_aggregation_lib',  
    version='0.1.0',  
    author='Sara Pettinari',  
    author_email='sara.pettinari@gssi.it',  
    description='An aggregation query library for Event Knowledge Graphs',  
    python_requires='>=3.7',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
)