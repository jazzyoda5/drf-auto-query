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
