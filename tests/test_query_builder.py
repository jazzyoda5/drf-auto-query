from unittest.mock import MagicMock

from django.db.models import Prefetch, Value
from django.test import TestCase
from rest_framework import serializers

from drf_auto_query.field_tree_builder import FieldNode
from drf_auto_query.query_builder import (
    QueryBuilder,
    _get_selected_fields,
    prefetch_queryset_for_serializer,
)
from drf_auto_query.types import ModelRelation
from tests.factories import AuthorFactory, BookFactory, PublisherFactory, TwinBrotherAuthorFactory
from tests.models import Author, Book, Publisher, TwinSisterAuthor
from tests.utils import author_field_node, test_serializer, test_serializer_class


class GetSelectedFieldsTestCase(TestCase):
    def test_single_related_field(self):
        # Arrange
        parent_node = author_field_node()
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
        parent_node = author_field_node()
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
        parent_node = author_field_node()
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
        parent_node = author_field_node()
        child_node = FieldNode(
            field_name="name",
            source="name",
            serializer_field=MagicMock(),
            model=Author,
        )
        parent_node.children.append(child_node)

        # Act
        selected_fields = _get_selected_fields(parent_node)

        # Assert
        self.assertEqual(len(selected_fields), 0)

    def test_overriden_primary_key_field(self):
        # Arrange
        parent_node = author_field_node()
        child_node = FieldNode(
            field_name="twin_sister",
            source="twin_sister",
            serializer_field=MagicMock(),
            parent_relation=ModelRelation.RELATED_MODEL,
            model=TwinSisterAuthor,
        )
        parent_node.children.append(child_node)

        # Act
        selected_fields = _get_selected_fields(parent_node)

        # Assert
        self.assertEqual(len(selected_fields), 1)
        self.assertEqual(list(selected_fields)[0], "twin_sister__uuid")


class QueryBuilderGetPrefetchObjectsTestCase(TestCase):
    def setUp(self) -> None:
        self.author = AuthorFactory.create()
        self.books = BookFactory.create_batch(3, author=self.author)
        self.publishers = PublisherFactory.create_batch(3)
        self.author.publisher_friends.add(*self.publishers)

    def test_simple_prefetch(self):
        # Arrange
        parent_node = author_field_node()
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

    def test_select_to_nested_prefetch(self):
        # Arrange
        parent_node = author_field_node()
        child_node = FieldNode(
            field_name="books",
            source="books",
            serializer_field=MagicMock(),
            parent_relation=ModelRelation.MANY_RELATED_MODEL,
            model=Book,
        )
        grandchild_node = FieldNode(
            field_name="publisher",
            source="publisher",
            serializer_field=MagicMock(),
            parent_relation=ModelRelation.RELATED_MODEL,
            model=Publisher,
        )
        parent_node.children.append(child_node)
        child_node.children.append(grandchild_node)

        # Act
        queryset = Author.objects.all()
        prefetch_objects = QueryBuilder(queryset)._get_prefetch_objects(parent_node)

        # Assert
        self.assertEqual(len(prefetch_objects), 1)
        self.assertEqual(prefetch_objects[0].prefetch_through, "books")

        prefetch_queryset = prefetch_objects[0].queryset
        self.assertIn("publisher", prefetch_queryset.query.select_related)

    def test_do_not_overwrite_existing_prefetch(self):
        # Arrange
        parent_node = author_field_node()
        child_node = FieldNode(
            field_name="books",
            source="books",
            serializer_field=MagicMock(),
            parent_relation=ModelRelation.MANY_RELATED_MODEL,
            model=Book,
        )
        parent_node.children.append(child_node)

        # Act
        queryset = Author.objects.prefetch_related(
            Prefetch("books", queryset=Book.objects.annotate(test_annotation=Value(True)))
        )
        prefetch_objects = QueryBuilder(queryset)._get_prefetch_objects(parent_node)

        # Assert
        self.assertEqual(len(prefetch_objects), 1)
        prefetch_queryset = prefetch_objects[0].queryset
        self.assertIn("test_annotation", prefetch_queryset.query.annotations)

    def test_prefetch_on_nested_model(self):
        # Arrange
        parent_node = author_field_node()
        child_node = FieldNode(
            field_name="twin_sister",
            source="twin_sister",
            serializer_field=MagicMock(),
            parent_relation=ModelRelation.RELATED_MODEL,
            model=TwinSisterAuthor,
        )
        grandchild_node = FieldNode(
            field_name="publisher_friends",
            source="publisher_friends",
            serializer_field=MagicMock(),
            parent_relation=ModelRelation.MANY_RELATED_MODEL,
            model=Publisher,
        )
        parent_node.children.append(child_node)
        child_node.children.append(grandchild_node)

        # Act
        queryset = Author.objects.all()
        prefetch_objects = QueryBuilder(queryset)._get_prefetch_objects(parent_node)

        # Assert
        self.assertEqual(len(prefetch_objects), 1)
        self.assertEqual(prefetch_objects[0].prefetch_through, "twin_sister__publisher_friends")


class PrefetchQuerysetForSerializerTestCase(TestCase):
    def setUp(self) -> None:
        self.authors = AuthorFactory.create_batch(2)

    def test_num_of_queries_for_many_relation(self):
        # Arrange
        for author in self.authors:
            BookFactory.create_batch(3, author=author)

        serializer_class = test_serializer_class(
            name="AuthorSerializer",
            fields={
                "books": test_serializer(
                    fields={
                        "title": serializers.CharField(),
                    },
                    many=True,
                )
            },
        )

        # Act
        queryset = prefetch_queryset_for_serializer(Author.objects.all(), serializer_class)

        # Assert
        serializer = serializer_class(queryset, many=True)
        with self.assertNumQueries(2):
            # 1 query for the authors
            # 1 query for the books
            self.assertIsNotNone(serializer.data)

    def test_num_of_queries_for_single_relation(self):
        # Arrange
        for author in self.authors:
            TwinBrotherAuthorFactory.create(author=author)

        serializer_class = test_serializer_class(
            name="AuthorSerializer",
            fields={
                "twin_brother": test_serializer(
                    fields={
                        "name": serializers.CharField(),
                    },
                )
            },
        )

        # Act
        queryset = prefetch_queryset_for_serializer(Author.objects.all(), serializer_class)

        # Assert
        serializer = serializer_class(queryset, many=True)
        with self.assertNumQueries(1):
            self.assertIsNotNone(serializer.data)
