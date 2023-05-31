from django.test import TestCase
from rest_framework import serializers

from drf_auto_query.field_tree_builder import FieldNode, build_serializer_field_tree
from drf_auto_query.types import ModelRelation
from tests.factories import AuthorFactory, BookFactory, PublisherFactory
from tests.models import Author, Book
from tests.utils import test_serializer


class BuildSerializerFieldTreeTestCase(TestCase):
    def setUp(self) -> None:
        self.author = AuthorFactory.create()
        self.books = BookFactory.create_batch(3, author=self.author)
        self.publishers = PublisherFactory.create_batch(3)

        self.author.publisher_friends.add(*self.publishers)

    def test_model_field(self):
        # Arrange
        serializer = test_serializer(
            fields={
                "name": serializers.CharField(),
            }
        )

        # Act
        field_tree = build_serializer_field_tree(serializer, Author)

        # Assert
        self.assertEqual(len(field_tree.children), 1)
        self.assertEqual(field_tree.children[0].field_name, "name")
        self.assertEqual(field_tree.children[0].parent_relation, ModelRelation.FIELD)

    def test_unrelated_model_field(self):
        # Arrange
        serializer = test_serializer(
            fields={
                "unrelated_field": serializers.CharField(),
            }
        )

        # Act
        field_tree = build_serializer_field_tree(serializer, Author)

        # Assert
        self.assertEqual(len(field_tree.children), 1)
        self.assertEqual(field_tree.children[0].field_name, "unrelated_field")
        self.assertEqual(field_tree.children[0].parent_relation, ModelRelation.NONE)

    def test_single_related_field(self):
        # Arrange
        serializer = test_serializer(
            fields={
                "favourite_book": test_serializer(
                    fields={
                        "title": serializers.CharField(),
                        "num_of_pages": serializers.IntegerField(),
                    }
                )
            }
        )

        # Act
        field_tree = build_serializer_field_tree(serializer, Author)

        # Assert
        self.assertEqual(len(field_tree.children), 1)

        child_node = field_tree.children[0]
        self.assertEqual(child_node.field_name, "favourite_book")
        self.assertEqual(child_node.parent_relation, ModelRelation.RELATED_MODEL)
        self.assertEqual(len(child_node.children), 2)

    def test_reverse_single_related_field(self):
        # Arrange
        serializer = test_serializer(
            fields={
                "authors": test_serializer(
                    fields={
                        "name": serializers.CharField(),
                        "description": serializers.IntegerField(),
                    },
                    many=True,
                    source="authors_where_favourite_book",
                ),
            }
        )

        # Act
        field_tree = build_serializer_field_tree(serializer, Book)

        # Assert
        self.assertEqual(len(field_tree.children), 1)

        child_node = field_tree.children[0]
        self.assertEqual(child_node.field_name, "authors")
        self.assertEqual(child_node.source, "authors_where_favourite_book")
        self.assertEqual(child_node.parent_relation, ModelRelation.MANY_RELATED_MODEL)
        self.assertEqual(len(child_node.children), 2)

    def test_many_to_many_field(self):
        # Arrange
        serializer = test_serializer(
            fields={
                "publisher_friends": test_serializer(
                    fields={
                        "first_name": serializers.CharField(),
                    },
                    many=True,
                ),
            }
        )

        # Act
        field_tree = build_serializer_field_tree(serializer, Author)

        # Assert
        self.assertEqual(len(field_tree.children), 1)

        child_node = field_tree.children[0]
        self.assertEqual(child_node.field_name, "publisher_friends")
        self.assertEqual(child_node.parent_relation, ModelRelation.MANY_RELATED_MODEL)
        self.assertEqual(len(child_node.children), 1)
