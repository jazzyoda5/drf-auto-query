from typing import List, Type

from rest_framework.serializers import Serializer
from rest_framework.utils import model_meta

from drf_auto_query.types import ModelType, SerializerField, Relation


def get_serializer_fields(serializer: Serializer) -> List[SerializerField]:
    base_serializer = _get_base_serializer(serializer)
    return (
        list(getattr(base_serializer, "fields", {}).values())
        if hasattr(base_serializer, "fields")
        else []
    )


def _get_base_serializer(serializer: Serializer) -> Serializer:
    """
    Return the serializer class that contains declared fields to
    avoid problems with list serializers.
    """

    return serializer.child if hasattr(serializer, "child") else serializer


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
        relation_to_parent: Relation = Relation.NONE,
        model: Type[ModelType] = None,
    ):
        self.field_name = field_name
        self.source = source
        self.serializer_field = serializer_field
        self.relation_to_parent = relation_to_parent
        self.model = model

        # self.children: List[FieldNode] = []

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

        return bool(self.model) and field_source in self.model_meta.relations

    def is_field(self, field_source: str):
        return bool(self.model) and field_source in self.model_meta.fields

    def __repr__(self):
        return f"<FieldNode {self.field_name}>"

    @classmethod
    def from_field(cls, field: SerializerField, **kwargs):
        kwargs.setdefault("field_name", field.field_name)
        kwargs.setdefault("source", field.source)
        return cls(serializer_field=field, **kwargs)


def build_field_map(
    field: SerializerField,
    model: Type[ModelType] = None,
    relation_to_parent: Relation = Relation.NONE,
) -> dict[str, FieldNode]:
    """
    Iterates over all the fields of a serializer and builds a flat dictionary
    mapping field paths to FieldNode objects.

    Args:
        field: The serializer field (typically a Serializer instance)
        model: The Django model class for this field
        relation_to_parent: The relation type from parent to this field

    Returns:
        A dictionary where keys are field paths (e.g., "books", "books__publisher")
        and values are FieldNode objects.

    Example:
        >>> from myapp.serializers import AuthorSerializer
        >>> from myapp.models import Author
        >>> field_map = build_field_map(AuthorSerializer(), Author)
        >>> field_map.keys()
        dict_keys(['books', 'books__publisher', 'publisher_friends', ...])
        >>> field_map['books'].relation_to_parent
        <Relation.ONE_TO_MANY: 2>
    """

    field_map = {}

    children_fields = get_serializer_fields(field)
    for child_field in children_fields:
        _inspect_serializer_field(
            child_field=child_field,
            parent_node=FieldNode.from_field(field, model=model, relation_to_parent=relation_to_parent),
            field_map=field_map,
            parent_path="",
        )

    return field_map


def _inspect_serializer_field(
    child_field: SerializerField,
    parent_node: FieldNode,
    field_map: dict[str, FieldNode],
    parent_path: str = "",
):
    """
    Recursively builds a flat field map from a serializer structure.

    Args:
        child_field: The current serializer field being processed
        parent_node: The parent FieldNode containing model info
        field_map: The dictionary to populate with field paths and nodes
        parent_path: The path from the root to the current field's parent
    """

    field_path = f"{parent_path}__{child_field.source}" if parent_path else child_field.source

    # Check if this field corresponds to a model relation
    if parent_node.model and parent_node.has_relation(child_field.source):
        # This is a relation field
        relation_info = parent_node.model_meta.relations[child_field.source]
        relation_to_parent = Relation.ONE_TO_MANY if relation_info.to_many else Relation.ONE_TO_ONE

        field_node = FieldNode.from_field(
            child_field,
            model=relation_info.related_model,
            relation_to_parent=relation_to_parent,
        )
        field_map[field_path] = field_node

        for nested_field in get_serializer_fields(child_field):
            _inspect_serializer_field(
                child_field=nested_field,
                parent_node=field_node,
                field_map=field_map,
                parent_path=field_path,
            )

    else:
        field_node = FieldNode.from_field(
            child_field,
            model=parent_node.model,
            relation_to_parent=Relation.FIELD
            if parent_node.is_field(child_field.source)
            else Relation.NONE,
        )
        field_map[field_path] = field_node
