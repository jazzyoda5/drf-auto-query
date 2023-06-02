from typing import List, Type

from django.db.models import Prefetch, QuerySet
from django.db.models.constants import LOOKUP_SEP
from rest_framework.serializers import Serializer

from drf_auto_query.exceptions import QueryBuilderError
from drf_auto_query.field_tree_builder import FieldNode, build_serializer_field_tree
from drf_auto_query.types import ModelRelation


def prefetch_queryset_for_serializer(
    queryset: QuerySet,
    serializer_class: Type[Serializer],
    only_required_fields: bool = False,
):
    """
    Given a serializer class and a queryset, join and select all the fields
    that are needed to serialize the queryset and prefetch all the related
    models.

    :param serializer_class: The serializer class that will be used to serialize the queryset.
    :param queryset: Queryset that will be serialized.
    :param only_required_fields: If True, only the fields that are required to serialize the
      queryset will be selected in the query using the 'only' method of the queryset.
    """

    serializer = serializer_class()
    query_builder = QueryBuilder(
        queryset=queryset,
        only_required_fields=only_required_fields,
    )
    return query_builder.get_queryset(serializer)


class QueryBuilder:
    def __init__(self, queryset: QuerySet, only_required_fields: bool = False):
        self.queryset = queryset
        self.only_required_fields = only_required_fields
        self.field_tree = None

    def get_queryset(self, serializer: Serializer):
        """
        Return a copy of the queryset with all the fields needed to serialize
        the queryset selected and all the related models prefetched for the
        given serializer instance.
        """

        self.field_tree = build_serializer_field_tree(serializer, self.queryset.model)
        return self._build_queryset_from_node(self.queryset, self.field_tree)

    def _build_queryset_from_node(self, queryset: QuerySet, field_node: FieldNode):
        selected_fields = _get_selected_fields(field_node)
        if self.only_required_fields:
            queryset = queryset.only(*selected_fields)

        # Get all tables that should be joined to the queryset
        joined_tables = _get_select_related_args(selected_fields)
        if joined_tables:
            queryset = queryset.select_related(*joined_tables)

        prefetch_objects = self._get_prefetch_objects(field_node)
        if prefetch_objects:
            queryset = queryset.prefetch_related(*prefetch_objects)

        return queryset

    def get_prefetched_queryset(self):
        prefetch_objects = self._get_prefetch_objects(self.field_tree)
        return self.queryset.prefetch_related(*prefetch_objects)

    def _get_prefetch_objects(
        self, field_node: FieldNode, related_name: str = ""
    ) -> List[Prefetch]:
        """
        Traverse the field tree and return a set of all the prefetch objects that
        should be used to prefetch the queryset.
        """

        prefetch_objects = []
        for child_node in field_node.children:
            relation = child_node.parent_relation
            if relation == ModelRelation.NONE or child_node.parent_relation == ModelRelation.FIELD:
                continue

            lookup = (
                f"{related_name}{LOOKUP_SEP}{child_node.source}"
                if related_name
                else child_node.source
            )
            if child_node.parent_relation == ModelRelation.RELATED_MODEL:
                child_prefetch_objects = self._get_prefetch_objects(child_node, lookup)
                if child_prefetch_objects:
                    prefetch_objects.extend(child_prefetch_objects)
                continue

            queryset = self._get_prefetch_queryset(child_node, lookup)
            if child_node.children:
                queryset = self._build_queryset_from_node(queryset, child_node)

            prefetch_objects.append(Prefetch(lookup, queryset=queryset))

        return prefetch_objects

    def _get_prefetch_queryset(self, field_node: FieldNode, lookup: str) -> QuerySet:
        """
        Return the queryset instance that should be used for the `Prefetch` object.
        If the original queryset already has a `Prefetch` object for the given lookup,
        return the queryset that is used in that `Prefetch` object to not overwrite
        any possible customizations.
        """

        if not field_node.model:
            raise QueryBuilderError(
                "Tried to prefetch a serializer field that "
                "does not correspond to a related model."
            )

        for prefetch in self.queryset._prefetch_related_lookups:
            if not isinstance(prefetch, Prefetch):
                continue

            if prefetch.queryset and prefetch.prefetch_through == lookup:
                return prefetch.queryset

        return field_node.model.objects.all() if field_node.model else None


def _get_selected_fields(field_node: FieldNode) -> List[str]:
    """
    Traverse the field tree and return a set of all the field names that
    the query for a model of a specific field node should select.
    """

    selected_fields = []
    for child_node in field_node.children:
        relation = child_node.parent_relation
        if relation == ModelRelation.NONE or relation == ModelRelation.MANY_RELATED_MODEL:
            continue

        if child_node.parent_relation == ModelRelation.FIELD:
            # Serializer field that corresponds to a model field, but does not
            # represent a relation to another model.
            selected_fields.append(child_node.source)
            continue

        # This is a serializer field that corresponds to a model field that
        # represents a relation to another model.
        pk_field_name = child_node.model._meta.pk.name  # noqa
        if not child_node.children:
            selected_fields.append(child_node.source + LOOKUP_SEP + pk_field_name)
            continue

        child_node_selected_fields = {
            f"{child_node.source}{LOOKUP_SEP}{field}" for field in _get_selected_fields(child_node)
        }
        selected_fields.extend(child_node_selected_fields)

    return selected_fields


def _get_select_related_args(selected_fields: List[str]):
    """
    Parse all the related names from the selected fields and return a list of
    all the related names that should be used in the `select_related` method
    of the queryset.
    """

    select_related_args = []
    for field in selected_fields:
        if LOOKUP_SEP not in field:
            continue

        table_related_name = field.rsplit(LOOKUP_SEP, maxsplit=1)[0]
        select_related_args.append(table_related_name)

    return select_related_args
