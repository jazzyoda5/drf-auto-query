from django.db import models


class Parent(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()


class Author(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    publisher_friends = models.ManyToManyField("Publisher", related_name="author_friends")
    favourite_book = models.ForeignKey(
        "Book", on_delete=models.CASCADE, related_name="authors_where_favourite_book", null=True
    )


class Book(models.Model):
    title = models.CharField(max_length=255)
    num_of_pages = models.IntegerField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books", null=True)
    publisher = models.ForeignKey(
        "Publisher", on_delete=models.CASCADE, related_name="books", null=True
    )


class Publisher(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)


class TwinBrotherAuthor(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    author = models.OneToOneField(Author, on_delete=models.CASCADE, related_name="twin_brother")
