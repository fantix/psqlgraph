from setuptools import setup

setup(
    version='1.2.2',
    name='psqlgraph',
    packages=["psqlgraph"],
    install_requires=[
        'psycopg2>=2.7.3.2, <2.8',
        'sqlalchemy>=0.9.9, <1.0.0',
        'py2neo>=2.0.1, <3.0.0',
        'progressbar',
        'avro>=1.7.7, <1.8.0',
        'xlocal>=0.5, <1.0',
        'requests>=2.5.2, <=2.7.0'
    ]
)
