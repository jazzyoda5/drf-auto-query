from unittest.mock import MagicMock

from rest_framework import serializers

from drf_auto_query.field_tree_builder import FieldNode
from tests.models import Author


def get_selected_fields_on_queryset(queryset):
    """
    Get all fields that were passed in the 'only' method on the queryset.
    """

    fields, is_deferred_from_query = queryset.query.deferred_loading
    assert is_deferred_from_query is False, "Fields were deferred instead of specified"
    return fields


def test_serializer_class(name, fields):
    return type(name, (serializers.Serializer,), fields)


def test_serializer(fields, data=None, name="", required=False, **kwargs):
    serializer_class = test_serializer_class(name=name, fields=fields)
    if data is not None:
        return serializer_class(data=data, required=required, **kwargs)
    return serializer_class(required=required, **kwargs)


def author_field_node():
    return FieldNode(
        field_name="author",
        source="author",
        serializer_field=MagicMock(),
        model=Author,
    )
