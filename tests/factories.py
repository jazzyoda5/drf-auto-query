import factory
from factory.django import DjangoModelFactory

from tests.models import Author, Book, Publisher, TwinBrotherAuthor


class AuthorFactory(DjangoModelFactory):
    name = factory.Faker("name")
    description = factory.Faker("text")

    class Meta:
        model = Author


class BookFactory(DjangoModelFactory):
    title = factory.Faker("sentence")
    num_of_pages = factory.Faker("pyint")

    class Meta:
        model = Book


class PublisherFactory(DjangoModelFactory):
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")

    class Meta:
        model = Publisher


class TwinBrotherAuthorFactory(DjangoModelFactory):
    name = factory.Faker("name")
    description = factory.Faker("text")

    class Meta:
        model = TwinBrotherAuthor
