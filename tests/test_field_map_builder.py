from django.test import TestCase
from rest_framework import serializers

from drf_auto_query.types import Relation
from drf_auto_query.utils import build_field_map
from tests.factories import AuthorFactory, BookFactory, PublisherFactory
from tests.models import Author, Book
from tests.utils import test_serializer


class BuildSerializerFieldMapTestCase(TestCase):
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
        field_map = build_field_map(serializer, Author)

        # Assert
        self.assertEqual(len(field_map), 1)
        self.assertIn("name", field_map)
        self.assertEqual(field_map["name"].field_name, "name")
        self.assertEqual(field_map["name"].relation_to_parent, Relation.FIELD)

    def test_unrelated_model_field(self):
        # Arrange
        serializer = test_serializer(
            fields={
                "unrelated_field": serializers.CharField(),
            }
        )

        # Act
        field_map = build_field_map(serializer, Author)

        # Assert - unrelated fields are still added to the map with Relation.NONE
        self.assertEqual(len(field_map), 1)
        self.assertIn("unrelated_field", field_map)
        self.assertEqual(field_map["unrelated_field"].relation_to_parent, Relation.NONE)

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
        field_map = build_field_map(serializer, Author)

        # Assert
        # Should have: favourite_book, favourite_book__title, favourite_book__num_of_pages
        self.assertEqual(len(field_map), 3)

        self.assertIn("favourite_book", field_map)
        self.assertEqual(field_map["favourite_book"].field_name, "favourite_book")
        self.assertEqual(field_map["favourite_book"].relation_to_parent, Relation.ONE_TO_ONE)

        self.assertIn("favourite_book__title", field_map)
        self.assertEqual(field_map["favourite_book__title"].field_name, "title")

        self.assertIn("favourite_book__num_of_pages", field_map)
        self.assertEqual(field_map["favourite_book__num_of_pages"].field_name, "num_of_pages")

    def test_reverse_single_related_field(self):
        # Arrange
        serializer = test_serializer(
            fields={
                "authors": test_serializer(
                    fields={
                        "name": serializers.CharField(),
                        "description": serializers.CharField(),
                    },
                    many=True,
                    source="authors_where_favourite_book",
                ),
            }
        )

        # Act
        field_map = build_field_map(serializer, Book)

        # Assert
        # Should have: authors_where_favourite_book, authors_where_favourite_book__name, authors_where_favourite_book__description
        self.assertEqual(len(field_map), 3)

        self.assertIn("authors_where_favourite_book", field_map)
        self.assertEqual(field_map["authors_where_favourite_book"].field_name, "authors")
        self.assertEqual(field_map["authors_where_favourite_book"].source, "authors_where_favourite_book")
        self.assertEqual(field_map["authors_where_favourite_book"].relation_to_parent, Relation.ONE_TO_MANY)

        self.assertIn("authors_where_favourite_book__name", field_map)
        self.assertIn("authors_where_favourite_book__description", field_map)

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
        field_map = build_field_map(serializer, Author)

        # Assert
        # Should have: publisher_friends, publisher_friends__first_name
        self.assertEqual(len(field_map), 2)

        self.assertIn("publisher_friends", field_map)
        self.assertEqual(field_map["publisher_friends"].field_name, "publisher_friends")
        self.assertEqual(field_map["publisher_friends"].relation_to_parent, Relation.ONE_TO_MANY)

        self.assertIn("publisher_friends__first_name", field_map)
        self.assertEqual(field_map["publisher_friends__first_name"].field_name, "first_name")

    def test_deeply_nested_fields(self):
        # Arrange
        serializer = test_serializer(
            fields={
                "books": test_serializer(
                    fields={
                        "title": serializers.CharField(),
                        "publisher": test_serializer(
                            fields={
                                "first_name": serializers.CharField(),
                                "last_name": serializers.CharField(),
                            }
                        ),
                    },
                    many=True,
                )
            }
        )

        # Act
        field_map = build_field_map(serializer, Author)

        # Assert
        # Should have: books, books__title, books__publisher, books__publisher__first_name, books__publisher__last_name
        self.assertEqual(len(field_map), 5)

        self.assertIn("books", field_map)
        self.assertEqual(field_map["books"].relation_to_parent, Relation.ONE_TO_MANY)

        self.assertIn("books__title", field_map)
        self.assertIn("books__publisher", field_map)
        self.assertEqual(field_map["books__publisher"].relation_to_parent, Relation.ONE_TO_ONE)

        self.assertIn("books__publisher__first_name", field_map)
        self.assertIn("books__publisher__last_name", field_map)

    def test_multiple_relations_at_same_level(self):
        # Arrange
        serializer = test_serializer(
            fields={
                "books": test_serializer(
                    fields={
                        "title": serializers.CharField(),
                    },
                    many=True,
                ),
                "publisher_friends": test_serializer(
                    fields={
                        "first_name": serializers.CharField(),
                    },
                    many=True,
                ),
            }
        )

        # Act
        field_map = build_field_map(serializer, Author)

        # Assert
        # Should have: books, books__title, publisher_friends, publisher_friends__first_name
        self.assertEqual(len(field_map), 4)

        self.assertIn("books", field_map)
        self.assertIn("books__title", field_map)
        self.assertIn("publisher_friends", field_map)
        self.assertIn("publisher_friends__first_name", field_map)