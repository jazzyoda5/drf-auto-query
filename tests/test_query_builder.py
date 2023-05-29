from unittest.mock import patch

from django.db.models import Prefetch, QuerySet
from django.test import TestCase

from drf_auto_query.query_builder import QueryBuilder
from tests.serializers import (
    ChildWithNestedGrandChildrenNamesSerializer,
    ChildWithNestedParentNameSerializer,
    FullChildSerializer,
    ParentNameSerializer,
)
from tests.utils import _get_selected_fields_on_queryset


class SingleFieldQueryTestCase(TestCase):
    def test_select_only_used_field(self):
        # Arrange
        serializer = ParentNameSerializer()

        # Act
        queryset = QueryBuilder(serializer).queryset

        # Assert
        self.assertCountEqual({"name"}, _get_selected_fields_on_queryset(queryset))


class JoinSingleRelatedFieldTableTestCase(TestCase):
    def setUp(self) -> None:
        self.serializer = ChildWithNestedParentNameSerializer()

    @patch.object(QuerySet, "select_related")
    def test_add_select_related_statement(self, mock_select_related):
        # Act
        _ = QueryBuilder(self.serializer).queryset

        # Assert
        mock_select_related.assert_called_once_with("parent")

    @patch.object(QuerySet, "only")
    def test_select_only_used_fields(self, mock_only):
        # Act
        _ = QueryBuilder(self.serializer).queryset

        # Assert
        mock_only.assert_called_once_with("parent__name")


class PrefetchManyRelatedFieldTableTestCase(TestCase):
    @patch.object(QuerySet, "prefetch_related")
    def test_prefetch_related_model(self, mock_prefetch_related):
        # Arrange
        serializer = FullChildSerializer()

        # Act
        _ = QueryBuilder(serializer).queryset

        # Assert
        mock_prefetch_related.assert_called_once()

        call_args = mock_prefetch_related.call_args[0]
        self.assertEqual(len(call_args), 1)

        prefetch_call_arg = call_args[0]
        self.assertIsInstance(prefetch_call_arg, Prefetch)
        self.assertEqual(prefetch_call_arg.prefetch_through, "grand_children")

    @patch.object(QuerySet, "prefetch_related")
    def test_select_only_used_fields_on_prefetch_queryset(self, mock_prefetch_related):
        # Arrange
        serializer = ChildWithNestedGrandChildrenNamesSerializer()

        # Act
        _ = QueryBuilder(serializer).queryset

        # Assert
        mock_prefetch_related.assert_called_once()

        prefetch_obj = mock_prefetch_related.call_args[0][0]
        prefetch_queryset = prefetch_obj.queryset
        selected_fields = _get_selected_fields_on_queryset(prefetch_queryset)
        self.assertCountEqual({"name"}, selected_fields)
