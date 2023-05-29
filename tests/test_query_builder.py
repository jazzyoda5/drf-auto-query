from unittest.mock import patch

from django.db.models import Prefetch, QuerySet
from django.test import TestCase

from drf_auto_query.query_builder import get_queryset_from_serializer
from tests.factories import ChildFactory, ParentFactory
from tests.serializers import (
    ChildModelSerializer,
    ChildWithNestedGrandChildrenNamesSerializer,
    ChildWithNestedParentModelSerializer,
    ChildWithNestedParentNameSerializer,
    FullChildSerializer,
    ParentNameSerializer,
)
from tests.utils import _get_selected_fields_on_queryset


class SingleFieldQueryTestCase(TestCase):
    def test_select_only_used_field(self):
        # Act
        queryset = get_queryset_from_serializer(ParentNameSerializer)

        # Assert
        self.assertCountEqual({"name"}, _get_selected_fields_on_queryset(queryset))


class JoinSingleRelatedFieldTableTestCase(TestCase):
    @patch.object(QuerySet, "select_related")
    def test_add_select_related_statement(self, mock_select_related):
        # Act
        get_queryset_from_serializer(ChildWithNestedParentNameSerializer)

        # Assert
        mock_select_related.assert_called_once_with("parent")

    @patch.object(QuerySet, "only")
    def test_select_only_used_fields(self, mock_only):
        # Act
        get_queryset_from_serializer(ChildWithNestedParentNameSerializer)

        # Assert
        mock_only.assert_called_once_with("parent__name")


class PrefetchManyRelatedFieldTableTestCase(TestCase):
    @patch.object(QuerySet, "prefetch_related")
    def test_prefetch_related_model(self, mock_prefetch_related):
        # Act
        get_queryset_from_serializer(FullChildSerializer)

        # Assert
        mock_prefetch_related.assert_called_once()

        call_args = mock_prefetch_related.call_args[0]
        self.assertEqual(len(call_args), 1)

        prefetch_call_arg = call_args[0]
        self.assertIsInstance(prefetch_call_arg, Prefetch)
        self.assertEqual(prefetch_call_arg.prefetch_through, "grand_children")

    @patch.object(QuerySet, "prefetch_related")
    def test_select_only_used_fields_on_prefetch_queryset(self, mock_prefetch_related):
        # Act
        get_queryset_from_serializer(ChildWithNestedGrandChildrenNamesSerializer)

        # Assert
        mock_prefetch_related.assert_called_once()

        prefetch_obj: Prefetch = mock_prefetch_related.call_args[0][0]
        prefetch_queryset = prefetch_obj.queryset
        selected_fields = _get_selected_fields_on_queryset(prefetch_queryset)
        self.assertCountEqual({"name"}, selected_fields)


class SelectRelatedWithModelSerializerTestCase(TestCase):
    def setUp(self) -> None:
        self.parent = ParentFactory.create()
        self.child = ChildFactory.create(parent=self.parent)

    def test_get_queryset_from_model_serializer(self):
        # Arrange
        serializer_class = ChildWithNestedParentModelSerializer

        # Act
        queryset = get_queryset_from_serializer(serializer_class)

        # Assert
        with self.assertNumQueries(1):
            serializer = serializer_class(queryset, many=True)
            self.assertEqual(len(serializer.data), 1)

    def test_get_queryset_from_model_serializer_with_prefetch(self):
        # Arrange
        serializer_class = ChildModelSerializer

        # Act
        queryset = get_queryset_from_serializer(serializer_class)

        # Assert
        with self.assertNumQueries(1):
            serializer = serializer_class(queryset, many=True)
            self.assertEqual(len(serializer.data), 1)
