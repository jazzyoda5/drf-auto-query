# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`drf-auto-query` is a Python package that automatically generates optimized Django ORM querysets from Django REST Framework serializers to prevent N+1 query problems. It analyzes serializer structure and automatically adds `select_related()` and `prefetch_related()` calls.

## Development Commands

### Environment Setup
```bash
# Install dependencies using poetry
poetry install

# Activate virtual environment (if not auto-activated)
poetry shell
```

### Testing
```bash
# Run all tests
python runtests.py

# Run specific test file
python runtests.py tests.test_query_builder

# Run specific test class or method
python runtests.py tests.test_query_builder.TestQueryBuilder
python runtests.py tests.test_query_builder.TestQueryBuilder.test_method_name
```

### Code Formatting
```bash
# Check formatting (CI uses line length 100)
black --line-length 100 --check --diff .

# Auto-format code
black --line-length 100 .
```

### Package Building
```bash
# Build distribution packages
poetry build

# Publish to PyPI
poetry publish
```

## Architecture

### Core Components

1. **`build_queryset(queryset, serializer, fields=None)`** (`drf_auto_query/query.py:12`)
   - Main entry point function that optimizes a queryset for a given serializer
   - Returns a queryset with appropriate `select_related()` and `prefetch_related()` calls

2. **`QueryBuilder`** (`drf_auto_query/query.py:92`)
   - Core class that handles queryset optimization logic
   - Key methods:
     - `build_for(serializer)`: Main builder method that processes serializer and returns optimized queryset
     - `_process_node(node, parent, join_to)`: Recursively processes field nodes to determine joins vs prefetches
   - Distinguishes between:
     - **One-to-one/ForeignKey relations**: Uses `select_related()` for joins
     - **One-to-many/ManyToMany relations**: Uses `prefetch_related()` with `Prefetch` objects
   - Preserves existing queryset annotations and prefetches

3. **`build_field_tree(field, model, parent_relation)`** (`drf_auto_query/utils.py:80`)
   - Recursively analyzes serializer structure to build a tree of `FieldNode` objects
   - Determines model relations using DRF's `model_meta.get_field_info()`
   - Identifies relation types (one-to-one, one-to-many, or plain field)

4. **`FieldNode`** (`drf_auto_query/utils.py:29`)
   - Represents a field in the serializer hierarchy
   - Contains: field name, source, serializer field reference, parent relation type, and related model
   - Used to traverse and analyze the serializer structure

5. **`get_prefetched(queryset)`** (`drf_auto_query/query.py:61`)
   - Extracts existing prefetch lookups from a queryset to avoid overwriting
   - Returns a dictionary mapping prefetch paths to `PrefetchPath` objects

6. **`AutoQuerySetMixin`** (`drf_auto_query/mixins.py:4`)
   - Django QuerySet mixin that adds `prefetch_for(serializer_class)` method
   - Convenient way to use auto-querying in custom QuerySet classes

### Key Design Patterns

- **Nested Prefetch Handling**: When joining single-related fields that are nested within many-related fields, the library adds the join to the prefetch queryset instead of the top-level queryset
- **String Prefetch Normalization**: Converts string-based prefetches to `Prefetch` objects when needed to add nested joins (`_normalize_prefetch_on_queryset`)
- **Relation Detection**: Uses DRF's `model_meta` utilities to introspect model relations and field types

### Known Limitations

- Multi-nested prefetches with altered querysets might be overwritten (documented in README.md:93-118)
- The library currently does not automatically add annotations based on serializer fields

## Test Structure

- `tests/models.py`: Test models (Author, Book, Publisher with various relation types)
- `tests/factories.py`: Factory Boy factories for test data generation
- `tests/test_query_builder.py`: Main tests for QueryBuilder functionality
- `tests/test_field_tree_builder.py`: Tests for field tree construction
- `tests/test_mixins.py`: Tests for AutoQuerySetMixin
- `tests/settings.py`: Minimal Django settings for test environment (SQLite in-memory database)

## Development Notes

- Python 3.7+ support (defined in pyproject.toml)
- Django 2.2+ and Django REST Framework are core dependencies
- CI runs tests on Python 3.7, 3.8, 3.9, 3.10
- Black formatting with line length 100 is enforced in CI