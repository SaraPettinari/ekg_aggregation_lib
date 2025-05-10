from setuptools import setup, find_packages

setup(
    name='aggregation_lib',  # Replace with your package name
    version='0.1.0',  # Start with an initial version
    author='Your Name',  # Your name or your organization name
    author_email='your.email@example.com',  # Your email address
    description='A short description of your package',
    long_description_content_type='text/markdown',  # Can also be 'text/x-rst' for reStructuredText
    url='https://github.com/yourusername/yourpackagename',  # URL to the project, typically a GitHub repo
    install_requires=[  # List your dependencies here
        'pyyaml', 'neo4j', 'pandas', 'numpy'
    ],
    python_requires='>=3.7',  # Specify the Python version required
    packages=find_packages(
            where='src'),
        package_dir={"": "src"}
)
