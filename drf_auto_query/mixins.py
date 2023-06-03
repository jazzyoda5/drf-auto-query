from drf_auto_query import prefetch_queryset_for_serializer


class AutoQuerySetMixin:
    """
    Django QuerySet mixin that provides a method to the class that
    can be used to prefetch correct related objects for a drf
    serializer.
    """

    def prefetch_for(self, serializer_class):
        return prefetch_queryset_for_serializer(self, serializer_class)
