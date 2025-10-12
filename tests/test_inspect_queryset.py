from django.db.models import Prefetch
from django.test import TestCase

from drf_auto_query.inspect import inspect_queryset
from tests.models import Author, Book, Publisher


class TestInspectQuerySet(TestCase):
    """Test the inspect_queryset function"""

    def test_no_prefetches(self):
        """Test queryset with no prefetches"""
        qs = Author.objects.all()
        info = inspect_queryset(qs)

        self.assertEqual(len(info.prefetches), 0)

    def test_simple_string_prefetch(self):
        """Test queryset with a simple string prefetch"""
        qs = Author.objects.prefetch_related("books")
        info = inspect_queryset(qs)

        self.assertEqual(len(info.prefetches), 1)
        self.assertIn("books", info.prefetches)
        self.assertEqual(info.prefetches["books"].path, "books")
        self.assertEqual(info.prefetches["books"].base_queryset_path, "")
        self.assertEqual(info.prefetches["books"].prefetch, "books")
        self.assertEqual(info.prefetches["books"].base_queryset, qs)

    def test_multiple_string_prefetches(self):
        """Test queryset with multiple string prefetches"""
        qs = Author.objects.prefetch_related("books", "publisher_friends")
        info = inspect_queryset(qs)

        self.assertEqual(len(info.prefetches), 2)
        self.assertIn("books", info.prefetches)
        self.assertIn("publisher_friends", info.prefetches)
        self.assertEqual(info.prefetches["books"].path, "books")
        self.assertEqual(info.prefetches["books"].base_queryset_path, "")
        self.assertEqual(info.prefetches["publisher_friends"].path, "publisher_friends")
        self.assertEqual(info.prefetches["publisher_friends"].base_queryset_path, "")

    def test_simple_prefetch_object(self):
        """Test queryset with a simple Prefetch object"""
        qs = Author.objects.prefetch_related(Prefetch("books", queryset=Book.objects.all()))
        info = inspect_queryset(qs)

        self.assertEqual(len(info.prefetches), 1)
        self.assertIn("books", info.prefetches)
        self.assertEqual(info.prefetches["books"].path, "books")
        self.assertEqual(info.prefetches["books"].base_queryset_path, "")
        self.assertIsInstance(info.prefetches["books"].prefetch, Prefetch)

    def test_nested_prefetch_with_base_queryset(self):
        """Test that base_queryset is correctly tracked for nested prefetches"""
        nested_qs = Book.objects.prefetch_related("publisher")
        qs = Author.objects.prefetch_related(Prefetch("books", queryset=nested_qs))
        info = inspect_queryset(qs)

        self.assertEqual(len(info.prefetches), 2)

        # First prefetch: books - base_queryset should be the Author queryset
        self.assertIn("books", info.prefetches)
        self.assertEqual(info.prefetches["books"].path, "books")
        self.assertEqual(info.prefetches["books"].base_queryset_path, "")
        self.assertIsInstance(info.prefetches["books"].prefetch, Prefetch)
        self.assertEqual(info.prefetches["books"].base_queryset, qs)

        # Second prefetch: books__publisher - base_queryset should be the nested Book queryset
        self.assertIn("books__publisher", info.prefetches)
        self.assertEqual(info.prefetches["books__publisher"].path, "books__publisher")
        self.assertEqual(info.prefetches["books__publisher"].base_queryset_path, "books")
        self.assertEqual(info.prefetches["books__publisher"].prefetch, "publisher")
        self.assertEqual(info.prefetches["books__publisher"].base_queryset, nested_qs)

    def test_deeply_nested_prefetches(self):
        """Test deeply nested prefetch chain"""
        qs = Author.objects.prefetch_related(
            Prefetch(
                "books",
                queryset=Book.objects.prefetch_related(
                    Prefetch(
                        "author", queryset=Author.objects.prefetch_related("publisher_friends")
                    )
                ),
            )
        )
        info = inspect_queryset(qs)

        self.assertEqual(len(info.prefetches), 3)

        # First level: books
        self.assertIn("books", info.prefetches)
        self.assertEqual(info.prefetches["books"].path, "books")
        self.assertEqual(info.prefetches["books"].base_queryset_path, "")

        # Second level: books__author
        self.assertIn("books__author", info.prefetches)
        self.assertEqual(info.prefetches["books__author"].path, "books__author")
        self.assertEqual(info.prefetches["books__author"].base_queryset_path, "books")

        # Third level: books__author__publisher_friends
        self.assertIn("books__author__publisher_friends", info.prefetches)
        self.assertEqual(
            info.prefetches["books__author__publisher_friends"].path,
            "books__author__publisher_friends",
        )
        self.assertEqual(
            info.prefetches["books__author__publisher_friends"].base_queryset_path,
            "books__author",
        )

    def test_mixed_string_and_prefetch_objects(self):
        """Test queryset with both string prefetches and Prefetch objects"""
        qs = Author.objects.prefetch_related(
            "publisher_friends",
            Prefetch("books", queryset=Book.objects.prefetch_related("publisher")),
        )
        info = inspect_queryset(qs)

        self.assertEqual(len(info.prefetches), 3)

        # String prefetch
        self.assertIn("publisher_friends", info.prefetches)
        self.assertEqual(info.prefetches["publisher_friends"].path, "publisher_friends")
        self.assertEqual(info.prefetches["publisher_friends"].base_queryset_path, "")

        # Prefetch object
        self.assertIn("books", info.prefetches)
        self.assertEqual(info.prefetches["books"].path, "books")
        self.assertEqual(info.prefetches["books"].base_queryset_path, "")

        # Nested in Prefetch object
        self.assertIn("books__publisher", info.prefetches)
        self.assertEqual(info.prefetches["books__publisher"].path, "books__publisher")
        self.assertEqual(info.prefetches["books__publisher"].base_queryset_path, "books")

    def test_prefetch_without_custom_queryset(self):
        """Test Prefetch object without a custom queryset"""
        qs = Author.objects.prefetch_related(Prefetch("books"))
        info = inspect_queryset(qs)

        self.assertEqual(len(info.prefetches), 1)
        self.assertIn("books", info.prefetches)
        self.assertEqual(info.prefetches["books"].path, "books")
        self.assertEqual(info.prefetches["books"].base_queryset_path, "")
        self.assertIsInstance(info.prefetches["books"].prefetch, Prefetch)

    def test_multiple_nested_branches(self):
        """Test queryset with multiple nested prefetch branches"""
        qs = Author.objects.prefetch_related(
            Prefetch("books", queryset=Book.objects.prefetch_related("publisher")),
            Prefetch("publisher_friends", queryset=Publisher.objects.all()),
        )
        info = inspect_queryset(qs)

        self.assertEqual(len(info.prefetches), 3)

        # First branch: books
        self.assertIn("books", info.prefetches)
        self.assertEqual(info.prefetches["books"].path, "books")
        self.assertEqual(info.prefetches["books"].base_queryset_path, "")

        # First branch nested: books__publisher
        self.assertIn("books__publisher", info.prefetches)
        self.assertEqual(info.prefetches["books__publisher"].path, "books__publisher")
        self.assertEqual(info.prefetches["books__publisher"].base_queryset_path, "books")

        # Second branch: publisher_friends
        self.assertIn("publisher_friends", info.prefetches)
        self.assertEqual(info.prefetches["publisher_friends"].path, "publisher_friends")
        self.assertEqual(info.prefetches["publisher_friends"].base_queryset_path, "")
