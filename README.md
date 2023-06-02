# drf-auto-query

Auto generate Django ORM query sets from serializers.

## Installation

```bash
$ pip install drf-auto-query
```

## Description

N+1 queries are a common problem in Django ORM. This package provides helper functions
that can help with building the exact `QuerySet` needed on a rest framework endpoint.

It is important to note that this package is not a silver bullet. It is meant to be used as a
tool to help with the N+1 problem in the specific case of rest framework views, not to solve 
it completely. It is still up to the developer to write efficient queries.

## Usage

### Prefetch function

The `prefetch_queryset_for_serializer` function takes a `QuerySet` and a `Serializer` class
and returns a `QuerySet` with all the needed `prefetch_related` and `select_related` calls.

Any annotations, joins or other modifications to the `QuerySet` will be preserved.

```python
from rest_framework import serializers
from drf_auto_query import prefetch_queryset_for_serializer

from my_app.models import User


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()

    
class UserGroupSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    users = UserSerializer(many=True)
    
    
queryset = User.objects.all()
queryset = prefetch_queryset_for_serializer(queryset, UserSerializer)
```


## Contributing

Interested in contributing? Check out the contributing guidelines. Please note that this project is released with a Code of Conduct. By contributing to this project, you agree to abide by its terms.

## License

`drf-auto-query` was created by Jakob Verlic. It is licensed under the terms of the MIT license.
