import py2neo
import psqlgraph
from datetime import datetime


class PsqlGraph2Neo4j(object):

    def __init__(self):
        self.psqlgraphDriver = None
        self.neo4jDriver = None
        self.indexed_keys = [
            'id'
        ]

    def connect_to_psql(self, host, user, password, database):
        self.psqlgraphDriver = psqlgraph.PsqlGraphDriver(
            host, user, password, database
        )

    def connect_to_neo4j(self, host, port=7474, user=None, password=None):
        self.neo4jDriver = py2neo.Graph(
            'http://{host}:{port}/db/data'.format(host=host, port=port)
        )

    def datetime2ms_epoch(self, dt):
        epoch = datetime.utcfromtimestamp(0)
        delta = dt - epoch
        return int(delta.total_seconds() * 1000)

    def try_parse_doc(self, doc):
        for key, val in doc.iteritems():
            try:
                ts = datetime.strptime(val, "%Y-%m-%d %H:%M:%S.%f")
                doc[key] = self.datetime2ms_epoch(ts)
            except:
                pass

    def convert_node(self, node):
            node.properties['id'] = node.node_id
            self.try_parse_doc(node.properties)

    def get_distinct_labels(self):
        conn = self.psqlgraphDriver.engine.connect()
        conn.execute('commit')
        labels = conn.execute('select distinct label from nodes').fetchall()
        conn.close()
        return [l[0] for l in labels]

    def create_indexes(self):
        labels = self.get_distinct_labels()
        for label in labels:
            for key in self.indexed_keys:
                self.neo4jDriver.schema.create_index(label, key)

    def export(self):
        try:
            self.create_indexes()
        except Exception, msg:
            print "unable to create indexes", str(msg)

        for node in self.psqlgraphDriver.get_nodes():
            self.convert_node(node)
            self.neo4jDriver.create(py2neo.Node(node.label, **node.properties))

        for edge in self.psqlgraphDriver.get_edges():
            self.neo4jDriver.cypher.execute(
                'CREATE'
            )
