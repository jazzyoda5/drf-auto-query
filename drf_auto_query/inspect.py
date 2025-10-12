from django.db.models import Prefetch, QuerySet
from django.db.models.constants import LOOKUP_SEP

from drf_auto_query.types import PrefetchInfo, QuerySetInfo


def inspect_queryset(queryset: QuerySet) -> QuerySetInfo:
    """
    Recursively inspects a queryset and returns all prefetches,
    including those on nested querysets within Prefetch objects.

    Args:
        queryset: The QuerySet to inspect

    Returns:
        QuerySetInfo containing a dict of PrefetchInfo objects keyed by path

    Example:
        >>> qs = Author.objects.prefetch_related(
        ...     Prefetch('books', queryset=Book.objects.prefetch_related('reviews'))
        ... )
        >>> info = inspect_queryset(qs)
        >>> # First prefetch at the base level
        >>> info.prefetches['books'].path
        'books'
        >>> info.prefetches['books'].base_queryset_path
        ''
        >>> # Nested prefetch
        >>> info.prefetches['books__reviews'].path
        'books__reviews'
        >>> info.prefetches['books__reviews'].base_queryset_path
        'books'
    """

    prefetches = {}
    _find_prefetches(queryset=queryset, prefetches=prefetches, base_path="")
    return QuerySetInfo(prefetches=prefetches)


def _find_prefetches(
    *,
    queryset: QuerySet,
    prefetches: dict[str, PrefetchInfo],
    base_path: str = "",
):
    for lookup in queryset._prefetch_related_lookups:  # noqa
        if isinstance(lookup, Prefetch):
            prefetch_field = lookup.prefetch_through
            path = f"{base_path}{LOOKUP_SEP}{prefetch_field}" if base_path else prefetch_field
            prefetches[path] = PrefetchInfo(
                prefetch=lookup,
                path=path,
                base_queryset=queryset,
                base_queryset_path=base_path,
            )
            if lookup.queryset is not None:
                _find_prefetches(
                    queryset=lookup.queryset,
                    prefetches=prefetches,
                    base_path=path,
                )
        else:
            path = f"{base_path}{LOOKUP_SEP}{lookup}" if base_path else lookup
            prefetches[path] = PrefetchInfo(
                prefetch=lookup,
                path=path,
                base_queryset=queryset,
                base_queryset_path=base_path,
            )
