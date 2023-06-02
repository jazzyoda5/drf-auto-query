from rest_framework import serializers


def get_selected_fields_on_queryset(queryset):
    """
    Get all fields that were passed in the 'only' method on the queryset.
    """

    fields, is_deferred_from_query = queryset.query.deferred_loading
    assert is_deferred_from_query is False, "Fields were deferred instead of specified"
    return fields


def create_test_serializer_class(name, fields):
    return type(name, (serializers.Serializer,), fields)


def test_serializer(fields, data=None, name="", required=False, **kwargs):
    serializer_class = create_test_serializer_class(name=name, fields=fields)
    if data is not None:
        return serializer_class(data=data, required=required, **kwargs)
    return serializer_class(required=required, **kwargs)
