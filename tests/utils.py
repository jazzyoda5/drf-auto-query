def _get_selected_fields_on_queryset(queryset):
    """
    Get all fields that were passed in the 'only' method on the queryset.
    """

    fields, is_deferred_from_query = queryset.query.deferred_loading
    assert is_deferred_from_query is False, "Fields were deferred instead of specified"
    return fields
