from django.test import TestCase
from rest_framework import serializers

from tests.factories import AuthorFactory, BookFactory, PublisherFactory
from tests.models import Author
from tests.utils import test_serializer, test_serializer_class


class AutoQuerySetMixinTestCase(TestCase):
    def setUp(self) -> None:
        self.authors = AuthorFactory.create_batch(3)

    def test_num_of_queries_on_nested_serializer(self):
        # Arrange
        for author in self.authors:
            for _ in range(2):
                BookFactory.create(author=author, publisher=PublisherFactory.create())

        serializer_class = test_serializer_class(
            name="AuthorSerializer",
            fields={
                "name": serializers.CharField(),
                "books": test_serializer(
                    name="BookSerializer",
                    many=True,
                    fields={
                        "title": serializers.CharField(),
                        "publisher": test_serializer(
                            name="PublisherSerializer",
                            fields={
                                "first_name": serializers.CharField(),
                                "last_name": serializers.CharField(),
                            },
                        ),
                    },
                ),
            },
        )

        # Act
        queryset = Author.objects.prefetch_for(serializer_class)

        # Assert
        serializer = serializer_class(queryset, many=True)
        with self.assertNumQueries(2):
            self.assertIsNotNone(serializer.data)
