from typing import List, Type

from rest_framework.utils import model_meta

from drf_auto_query.types import ModelRelation, ModelType, SerializerField
from drf_auto_query.utils import get_serializer_fields


PARENT_FIELD_NODE = "--parent--"


class FieldNode:
    """
    Class representing either a serializer field or a nested serializer in
    a serializer configuration.
    """

    def __init__(
        self,
        field_name: str,
        source: str,
        serializer_field: SerializerField,
        parent_relation: ModelRelation = ModelRelation.NONE,
        model: Type[ModelType] = None,
    ):
        self.field_name = field_name
        self.source = source
        self.serializer_field = serializer_field
        self.parent_relation = parent_relation
        self.model = model

        self.children: List[FieldNode] = []

        self._model_meta = None

    @property
    def model_meta(self):
        if self.model and self._model_meta is None:
            self._model_meta = model_meta.get_field_info(self.model)
        return self._model_meta

    def has_relation(self, field_source: str) -> bool:
        """
        Returns True if the source of a serializer field is in any way related
        to the model class of this node.
        """

        if not self.model:
            return False

        return field_source in self.model_meta.fields or field_source in self.model_meta.relations

    def __repr__(self):
        return f"<FieldNode {self.field_name}>"

    @classmethod
    def from_field(cls, field: SerializerField, **kwargs):
        kwargs.setdefault("field_name", field.field_name)
        kwargs.setdefault("source", field.source)
        return cls(serializer_field=field, **kwargs)


def build_serializer_field_tree(
    field: SerializerField,
    model: Type[ModelType] = None,
    parent_relation: ModelRelation = ModelRelation.NONE,
) -> FieldNode:
    """
    Iterates over all the fields of a serializer node and builds a tree of
    FieldNode objects.
    """

    field_node = FieldNode.from_field(field, model=model, parent_relation=parent_relation)

    children_fields = get_serializer_fields(field)
    if not children_fields:
        return field_node

    for field in children_fields:
        if not model or not field_node.has_relation(field.source):
            # This is a serializer field that does not correspond to a model field
            # (e.g. SerializerMethodField).
            child_node = build_serializer_field_tree(field)
            field_node.children.append(child_node)
            continue

        if field.source in field_node.model_meta.fields:
            # Serializer field that corresponds to a model field, but does not
            # represent a relation to another model.
            child_node = build_serializer_field_tree(field, parent_relation=ModelRelation.FIELD)
            field_node.children.append(child_node)
            continue

        relation_info = field_node.model_meta.relations[field.source]
        parent_relation = (
            ModelRelation.MANY_RELATED_MODEL
            if relation_info.to_many
            else ModelRelation.RELATED_MODEL
        )

        child_node = build_serializer_field_tree(
            field,
            model=relation_info.related_model,
            parent_relation=parent_relation,
        )
        field_node.children.append(child_node)

    return field_node
