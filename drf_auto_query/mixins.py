from drf_auto_query import build_queryset


class AutoQuerySetMixin:
    """
    Django QuerySet mixin that provides a method to the class that
    can be used to prefetch correct related objects for a drf
    serializer.
    """

    def prefetch_for(self, serializer_class):
        return build_queryset(self, serializer_class)
