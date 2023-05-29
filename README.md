# drf-auto-query

Auto generate Django ORM query sets from serializers.

## Installation

```bash
$ pip install drf-auto-query
```

## Description

N+1 queries are a common problem in Django ORM. This package provides a `QueryBuilder` class 
that can help with building the exact `QuerySet` needed on a rest framework endpoint.

It is important to note that this package is not a silver bullet. It is meant to be used as a
tool to help with the N+1 problem in the specific case of rest framework views, not to solve 
it completely. It is still up to the developer to write efficient queries.

## Usage

```python
from rest_framework import serializers
from drf_auto_query import QueryBuilder

from my_app.models import User


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()

    class Meta:
        # The 'model' attribute is required for the QueryBuilder to work
        model = User


serializer = UserSerializer()
query_builder = QueryBuilder(serializer)
queryset = query_builder.get_queryset()
```


## Contributing

Interested in contributing? Check out the contributing guidelines. Please note that this project is released with a Code of Conduct. By contributing to this project, you agree to abide by its terms.

## License

`drf-auto-query` was created by Jakob Verlic. It is licensed under the terms of the MIT license.
