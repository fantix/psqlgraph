from edge import Edge
from node import Node
from sqlalchemy.orm import Query
from sqlalchemy import or_, not_


class GraphQuery(Query):
    """Query subclass implementing graph specific operations."""

    # ======== Edges ========
    def with_edge_to_node(self, edge_label, target_node):
        """Returns a new query that filters the query to just those nodes that
        have an edge with label ``edge_label`` to ``target_node``.

        :param str edge_label: label of the edge to use for restricting
        :param Node target_node: node used to filter the result set such
        that each result node must be the source of an edge whose
        destination is ``target_node``

        """

        assert self._entity_zero().type == Node
        # first we construct a subquery for edges of the correct label
        # to the target_node
        session = self.session
        sq = session.query(Edge).filter(Edge.label == edge_label)\
                                .filter(Edge.dst_id == target_node.node_id)\
                                .subquery()
        return self.filter(Node.node_id == sq.c.src_id)

    def with_edge_from_node(self, edge_label, source_node):
        """Like ``with_edge_to_node``, but in the opposite direction.  Filters
        the query such that ``source_node`` must have an edge pointing
        to a node in the result set.

        :param str edge_label: label of the edge to use for
        restricting :param Node source_node: node used to filter
        the result set such that each result node must be the dst of an edge that
        originates at ``source_node``.

        """

        assert self._entity_zero().type == Node
        # first we construct a subquery for edges of the correct label
        # to the target_node
        session = self.session
        sq = session.query(Edge).filter(Edge.label == edge_label)\
                                .filter(Edge.src_id == source_node.node_id)\
                                .subquery()
        return self.filter(Node.node_id == sq.c.dst_id)

    def src(self, src_id):
        """

        """
        return self.filter(Edge.src_id == src_id)

    # ======== Nodes ========
    def has_edges(self):
        """Adds filter to query to return only nodes with edges

        """
        return self.filter(
            or_(Node.edges_in.any(), Node.edges_out.any()))

    def has_no_edges(self):
        """Adds filter to query to return only nodes without edges

        """
        return self.\
            filter(not_(Node.edges_in.any())).\
            filter(not_(Node.edges_out.any()))

    def path_out(self, labels, reset=False):
        """Takes a list of labels and filters on nodes that have that path out
        from source node.  If `reset` is False, then this filter
        leaves you at the end of the path. You can at any point
        manually add a .reset_joinpoint to the query to bring it back
        to the path source.

        :param list labels: list of labels in path
        :param bool reset: reset the join point to the source node

        """
        for label in labels:
            self = self.outerjoin(
                'edges_out', 'dst', aliased=True, from_joinpoint=True
            ).filter(Node.label == label)
            if reset:
                self = self.reset_joinpoint()
                return self

    def path_in(self, labels, reset=False):
        """Takes a list of labels and filters on nodes that have that path into
        the source node.  If `reset` is False, then this filter
        leaves you at the end of the path. You can at any point
        manually add a .reset_joinpoint to the query to bring it back
        to the path source.

        :param list labels: list of labels in path
        :param bool reset: reset the join point to the source node

        """
        for label in labels:
            self = self.outerjoin(
                'edges_in', 'src', aliased=True, from_joinpoint=True
            ).filter(Node.label == label)
            if reset:
                self = self.reset_joinpoint()
                return self

    def ids(self, ids):
        """Filter on nodes with either specific id, or nodes with ids in a
        provided list

        """
        if isinstance(ids, str):
            return self.filter(Node.node_id == ids)
        else:
            return self.filter(Node.node_id.in_(ids))

    def not_ids(self, ids):
        if isinstance(ids, str):
            return self.filter(Node.node_id != ids)
        else:
            return self.filter(not_(Node.node_id.in_(ids)))

    # ======== Labels ========
    def labels(self, labels):
        """With (Node.label in labels).  If label is type `str` then
        filter will check for equality.

        """
        if isinstance(labels, str):
            return self.filter(Node.label == labels)
        else:
            return self.filter(Node.label.in_(labels))

    def not_labels(self, labels):
        """With (Node.label not in labels).  If label is type `str` then
        filter will check for equality.

        """
        if isinstance(labels, str):
            return self.filter(Node.label != labels)
        else:
            return self.filter(not_(Node.label.in_(labels)))

    # ======== Properties ========
    def props(self, props):
        """With properties. Subset props in properties.

        :param dict props:
            kv dictionary to filter with. Results are nodes with
        properties which are superset of `props`

        """
        assert isinstance(props, dict)
        return self.filter(Node.properties.contains(props))

    def not_props(self, props):
        """Without properties. Subset props not in properties.

        :param dict props:
            kv dictionary to filter with. Results are nodes with
        properties which are not superset of `props`

        """
        assert isinstance(props, dict)
        return self.filter(not_(Node.properties.contains(props)))

    def prop_in(self, key, values):
        """With (properties[key] in values).

        :param str key: the property key
        :param list values: a list of possible properties

        """
        assert isinstance(key, str) and isinstance(values, list)
        return self.filter(Node.properties[key].astext.in_([
            str(v) for v in values]))

    def prop(self, key, value):
        """With (properties[key] in values).

        :param str key: the property key
        :param list values: a list of possible properties

        """
        return self.filter(Node.properties[key].astext == str(value))

    def null_props(self, keys):
        """

        """
        if isinstance(keys, str):
            keys = [keys]
            return self.filter(Node.properties.contains(
                {key: None for key in keys}))

    # ======== System Annotations ========
    def sysan(self, sysans):
        """With system_annotations. Subset sysans in system_annotations.

        """
        assert isinstance(sysans, dict)
        return self.filter(Node.system_annotations.contains(sysans))

    def not_sysan(self, sysans):
        """Without system_annotations. Subset sysans not in system_annotations.

        """
        assert isinstance(sysans, dict)
        return self.filter(not_(Node.system_annotations.contains(sysans)))

    def not_sysan_in(self, key, values):
        """With (system_annotations[key] in values).

        """
        assert isinstance(key, str) and isinstance(values, list)
        return self.filter(Node.system_annotations[key].astext.in_([
            str(v) for v in values]))
