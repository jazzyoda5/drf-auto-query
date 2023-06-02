from typing import List

from rest_framework.serializers import Serializer

from drf_auto_query.types import ModelType, SerializerField


def get_serializer_fields(serializer: Serializer) -> List[SerializerField]:
    base_serializer = _get_base_serializer(serializer)
    if not hasattr(base_serializer, "fields"):
        return []

    return list(getattr(base_serializer, "fields", {}).values())


def _get_base_serializer(serializer: Serializer) -> Serializer:
    """
    Return the serializer class that contains declared fields to
    avoid problems with list serializers.
    """

    if hasattr(serializer, "child"):
        return serializer.child

    return serializer


def has_field_relation_to_model(model: ModelType, field: SerializerField) -> bool:
    """
    Returns True if the source of a serializer field is in any way related
    to the model class.
    """
    """
    Returns True if the source of a serializer field is in any way related
    to the model class of this node.
    """

    if not model:
        return False

    model_meta = model_meta.get_field_info(model)
    return field.source in self.model_meta.fields or field_source in self.model_meta.relations

    return field.source in model_meta.get_field_info(model).relations
