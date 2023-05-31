from unittest.mock import MagicMock

from django.test import TestCase

from drf_auto_query.field_tree_builder import FieldNode
from drf_auto_query.query_builder import QueryBuilder, _get_selected_fields
from drf_auto_query.types import ModelRelation
from tests.factories import AuthorFactory, BookFactory, PublisherFactory
from tests.models import Author, Book, Publisher


class GetSelectedFieldsTestCase(TestCase):
    def test_single_related_field(self):
        # Arrange
        parent_node = FieldNode(
            field_name="parent_node",
            source="parent_node",
            serializer_field=MagicMock(),
            model=Author,
        )
        child_node = FieldNode(
            field_name="book",
            source="favourite_book",
            serializer_field=MagicMock(),
            parent_relation=ModelRelation.RELATED_MODEL,
            model=Book,
        )
        parent_node.children.append(child_node)

        # Act
        selected_fields = _get_selected_fields(parent_node)

        # Assert
        self.assertEqual(len(selected_fields), 1)
        self.assertEqual(list(selected_fields)[0], "favourite_book__id")

    def test_two_level_single_related_field(self):
        # Arrange
        parent_node = FieldNode(
            field_name="parent_node",
            source="parent_node",
            serializer_field=MagicMock(),
            model=Author,
        )
        child_node = FieldNode(
            field_name="book",
            source="favourite_book",
            serializer_field=MagicMock(),
            parent_relation=ModelRelation.RELATED_MODEL,
            model=Book,
        )
        grandchild_node = FieldNode(
            field_name="title",
            source="title",
            serializer_field=MagicMock(),
            parent_relation=ModelRelation.FIELD,
            model=Book,
        )
        child_node.children.append(grandchild_node)
        parent_node.children.append(child_node)

        # Act
        selected_fields = _get_selected_fields(parent_node)

        # Assert
        self.assertEqual(len(selected_fields), 1)
        self.assertEqual(list(selected_fields)[0], "favourite_book__title")

    def test_three_level_relation(self):
        # Arrange
        parent_node = FieldNode(
            field_name="parent_node",
            source="parent_node",
            serializer_field=MagicMock(),
            model=Author,
        )
        child_node = FieldNode(
            field_name="book",
            source="favourite_book",
            serializer_field=MagicMock(),
            parent_relation=ModelRelation.RELATED_MODEL,
            model=Book,
        )
        grandchild_node = FieldNode(
            field_name="publisher",
            source="publisher",
            serializer_field=MagicMock(),
            parent_relation=ModelRelation.RELATED_MODEL,
            model=Publisher,
        )
        great_grandchild_node = FieldNode(
            field_name="name",
            source="name",
            serializer_field=MagicMock(),
            parent_relation=ModelRelation.FIELD,
        )
        grandchild_node.children.append(great_grandchild_node)
        child_node.children.append(grandchild_node)
        parent_node.children.append(child_node)

        # Act
        selected_fields = _get_selected_fields(parent_node)

        # Assert
        self.assertEqual(len(selected_fields), 1)
        self.assertEqual(list(selected_fields)[0], "favourite_book__publisher__name")

    def test_no_relation(self):
        # Arrange
        parent_node = FieldNode(
            field_name="parent_node",
            source="parent_node",
            serializer_field=MagicMock(),
            model=Author,
        )
        child_node = FieldNode(
            field_name="name",
            source="name",
            serializer_field=MagicMock(),
            parent_relation=ModelRelation.NONE,
            model=Author,
        )
        parent_node.children.append(child_node)

        # Act
        selected_fields = _get_selected_fields(parent_node)

        # Assert
        self.assertEqual(len(selected_fields), 0)


class QueryBuilderGetPrefetchObjectsTestCase(TestCase):
    def setUp(self) -> None:
        self.author = AuthorFactory.create()
        self.books = BookFactory.create_batch(3, author=self.author)
        self.publishers = PublisherFactory.create_batch(3)
        self.author.publisher_friends.add(*self.publishers)

    def test_simple_prefetch(self):
        # Arrange
        parent_node = FieldNode(
            field_name="author",
            source="author",
            serializer_field=MagicMock(),
            model=Author,
        )
        child_node = FieldNode(
            field_name="publisher_friends",
            source="publisher_friends",
            serializer_field=MagicMock(),
            parent_relation=ModelRelation.MANY_RELATED_MODEL,
            model=Publisher,
        )
        parent_node.children.append(child_node)

        # Act
        queryset = Author.objects.all()
        prefetch_objects = QueryBuilder(queryset)._get_prefetch_objects(parent_node)

        # Assert
        self.assertEqual(len(prefetch_objects), 1)
        self.assertEqual(prefetch_objects[0].prefetch_through, "publisher_friends")
