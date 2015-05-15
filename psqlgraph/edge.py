from sqlalchemy import Column, Text, event, ForeignKey
from sqlalchemy.ext.declarative import AbstractConcreteBase, declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from base import ORMBase
from voided_edge import VoidedEdge


def IDColumn(tablename):
    return Column(
        Text, ForeignKey(
            '{}.node_id'.format(tablename),
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ), primary_key=True, nullable=False)


def edge_attributes(name, src_class, dst_class,
                    src_table=None, dst_table=None):
    src_table = src_table or src_class.lower()
    dst_table = dst_table or dst_class.lower()
    src_id = IDColumn(src_table)
    dst_id = IDColumn(dst_table)
    src = relationship(src_class, foreign_keys=[src_id])
    dst = relationship(dst_class, foreign_keys=[dst_id])
    return (src_id, dst_id, src, dst)


class Edge(AbstractConcreteBase, ORMBase):

    __src_table__ = None
    __dst_table__ = None

    src_id, dst_id, src, dst = None, None, None, None

    @declared_attr
    def src_id(cls):
        if cls.__name__ == 'Edge':
            return
        src_table = cls.__src_table__ or cls.__src_class__.lower()
        src_id = IDColumn(src_table)
        return src_id

    @declared_attr
    def dst_id(cls):
        if cls.__name__ == 'Edge':
            return
        dst_table = cls.__dst_table__ or cls.__dst_class__.lower()
        dst_id = IDColumn(dst_table)
        return dst_id

    @classmethod
    def __declare_last__(cls):
        if cls == Edge:
            return
        assert hasattr(cls, '__src_class__'),\
            'You must declare __src_class__ for {}'.format(cls)
        assert hasattr(cls, '__dst_class__'),\
            'You must declare __dst_class__ for {}'.format(cls)
        assert hasattr(cls, '__src_dst_assoc__'),\
            'You must declare __src_dst_assoc__ for {}'.format(cls)
        assert hasattr(cls, '__dst_src_assoc__'),\
            'You must declare __dst_src_assoc__ for {}'.format(cls)

    @declared_attr
    def __table_args__(cls):
        return tuple()

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def __init__(self, src_id=None, dst_id=None, properties={},
                 acl=[], system_annotations={}, label=None,
                 src=None, dst=None, **kwargs):
        self._props = {}
        self.system_annotations = system_annotations
        self.acl = acl
        self.properties = properties
        self.properties.update(kwargs)

        if src is not None:
            if src_id is not None:
                assert src.node_id == src_id, (
                    "Edge initialized with src.node_id and src_id"
                    "that don't match.")
            self.src = src
            self.src_id = src.node_id
        else:
            self.src_id = src_id

        if dst is not None:
            if dst_id is not None:
                assert dst.node_id == dst_id, (
                    "Edge initialized with dst.node_id and dst_id"
                    "that don't match.")
            self.dst = dst
            self.dst_id = dst.node_id
        else:
            self.dst_id = dst_id

    def __repr__(self):
        return '<{}(({})-[{}]->({})>'.format(
            self.__class__.__name__, self.src_id, self.label, self.dst_id)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.src_id == other.src_id
            and self.dst_id == other.dst_id
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def get_subclass(cls, label):
        scls = cls._get_subclasses_labeled(label)
        if len(scls) > 1:
            raise KeyError(
                'More than one Edge with label {} found: {}'.format(
                    label, scls))
        if not scls:
            return None
        return scls[0]

    @classmethod
    def _get_subclasses_labeled(cls, label):
        return [c for c in cls.__subclasses__()
                if c.get_label() == label]

    @classmethod
    def _get_edges_with_src(cls, src_class_name):
        return [c for c in cls.__subclasses__()
                if c.__src_class__ == src_class_name]

    @classmethod
    def _get_edges_with_dst(cls, dst_class_name):
        return [c for c in cls.__subclasses__()
                if c.__dst_class__ == dst_class_name]

    @classmethod
    def get_subclass_table_names(label):
        return [s.__tablename__ for s in Edge.__subclasses__()]

    @classmethod
    def get_subclasses(cls):
        return [s for s in cls.__subclasses__()]

    def _snapshot_existing(self, session, old_props, old_sysan):
        temp = self.__class__(self.src_id, self.dst_id, old_props, self.acl,
                              old_sysan, self.label)
        voided = VoidedEdge(temp)
        session.add(voided)

    # ======== Label ========
    @hybrid_property
    def label(self):
        return self.get_label()

    @label.setter
    def label(self, label):
        """Custom setter as an application level ban from changing labels.

        """
        if not isinstance(self.label, Column)\
           and self.get_label() is not None\
           and self.get_label() != label:
            raise AttributeError('Cannot change label from {} to {}'.format(
                self.get_label(), label))


def PolyEdge(src_id=None, dst_id=None, label=None, acl=[],
             system_annotations={}, properties={}):
    assert label, 'You cannot create a PolyEdge without a label.'
    try:
        Type = Edge.get_subclass(label)
    except Exception as e:
        raise RuntimeError((
            "{}: Unable to determine edge type. If there are more than one "
            "edges with label {}, you need to specify src_label and dst_label"
            "using the PsqlGraphDriver.get_PolyEdge())"
        ).format(e, label))

    return Type(
        src_id=src_id,
        dst_id=dst_id,
        properties=properties,
        acl=acl,
        system_annotations=system_annotations,
        label=label
    )
