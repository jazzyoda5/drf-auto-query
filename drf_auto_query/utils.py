from typing import List

from django.db.models import Model
from rest_framework.fields import Field
from rest_framework.utils.model_meta import is_abstract_model


def get_model_from_serializer(serializer) -> Model:
    """Returns the model configured on a serializer."""

    serializer = _get_base_serializer(serializer)

    assert hasattr(serializer, "Meta") and hasattr(
        serializer.Meta, "model"
    ), "Serializer must have a Meta class with a model attribute."

    model = serializer.Meta.model
    assert not is_abstract_model(model), "Model must not be abstract."

    return model


def get_serializer_fields(serializer) -> List[Field]:
    base_serializer = _get_base_serializer(serializer)
    if not hasattr(base_serializer, "fields"):
        return []

    return list(getattr(base_serializer, "fields", {}).values())


def _get_base_serializer(serializer: Field) -> Field:
    """
    Return the serializer class that contains declared fields to
    avoid problems with list serializers.
    """

    if hasattr(serializer, "child"):
        return serializer.child

    return serializer
