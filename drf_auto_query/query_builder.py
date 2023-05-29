from typing import List, Set

from django.db.models import Prefetch, QuerySet
from django.db.models.constants import LOOKUP_SEP
from rest_framework.fields import Field
from rest_framework.utils import model_meta

from drf_auto_query.utils import get_model_from_serializer, get_serializer_fields


class QueryBuilder:
    """
    Class that automatically generates a queryset that efficiently fetches all the data
    needed for a DRF serializer.
    """

    def __init__(self, serializer: Field, queryset: QuerySet = None):
        self._serializer = serializer
        self._model_class = get_model_from_serializer(serializer)
        self._model_field_info = model_meta.get_field_info(self._model_class)
        self._queryset = queryset or self._model_class._base_manager.all()  # noqa

    @property
    def queryset(self):
        return self.get_queryset()

    def get_queryset(self):
        serializer_fields = get_serializer_fields(self._serializer)

        # Select only used fields
        selected_fields = _get_selected_fields(self._model_field_info, serializer_fields)
        self._queryset = self._queryset.only(*selected_fields)

        # Join all the tables used in nested serializers
        query_joins = {
            self._get_query_join(field_name)
            for field_name in selected_fields
            if LOOKUP_SEP in field_name
        }
        if query_joins:
            self._queryset = self._queryset.select_related(*query_joins)

        # Find required prefetches
        for field in serializer_fields:
            nested_fields = get_serializer_fields(field)
            if not nested_fields:
                continue

            if field.source not in self._model_field_info.relations:
                continue

            is_many_relation = self._model_field_info.relations[field.source].to_many
            if not is_many_relation:
                continue

            prefetch_queryset = QueryBuilder(field).queryset
            self._queryset = self._queryset.prefetch_related(
                Prefetch(field.source, queryset=prefetch_queryset)
            )

        return self._queryset

    @staticmethod
    def _get_query_join(field_source: str) -> str:
        return field_source.rpartition(LOOKUP_SEP)[0]


def _get_selected_fields(model_field_info: model_meta.FieldInfo, fields: List[Field]) -> Set[str]:
    """Returns all fields that should be selected in the queryset."""

    used_fields = set()
    for field in fields:
        nested_fields = get_serializer_fields(field)
        if not nested_fields:
            used_fields.add(field.source)
            continue

        if field.source not in model_field_info.relations:
            continue

        is_many_relation = model_field_info.relations[field.source].to_many
        if is_many_relation:
            continue

        nested_model = get_model_from_serializer(field)
        nested_model_field_info = model_meta.get_field_info(nested_model)
        nested_used_fields = {
            f"{field.source}{LOOKUP_SEP}{nested_field_name}"
            for nested_field_name in _get_selected_fields(nested_model_field_info, nested_fields)
        }
        used_fields.update(nested_used_fields)

    return used_fields
