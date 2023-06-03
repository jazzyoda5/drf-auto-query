# drf-auto-query

Auto generate Django ORM query sets from serializers.

## Installation

```bash
$ pip install drf-auto-query
```

## Description

The "drf-auto-query" package addresses the common problem of N+1 queries in Django ORM when building REST framework 
endpoints. It provides convenient helper functions and mixins to assist in generating efficient QuerySet objects 
tailored to your specific serializer requirements.

It is important to note that while "drf-auto-query" aims to alleviate the N+1 problem, it is not a comprehensive 
solution. Instead, it serves as a valuable tool to be used in conjunction with your own efforts to write efficient 
queries. By automating the process of prefetching related data, the package helps reduce the number of database 
queries required, resulting in improved performance and responsiveness for your Django-based APIs, while it also speeds
up development because you will not have to worry about your serializer setup firing unwanted database queries.


## Usage

### Prefetch function

The `prefetch_queryset_for_serializer` function streamlines the process of setting up the necessary `prefetch_related` 
and `select_related` calls on a `QuerySet` based on a given serializer class.

```python
from rest_framework import serializers
from drf_auto_query import prefetch_queryset_for_serializer

from my_app.models import UserGroup


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()

    
class UserGroupSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    users = UserSerializer(many=True)
    
    
queryset = UserGroup.objects.all()
queryset = prefetch_queryset_for_serializer(queryset, UserGroupSerializer)
```

### QuerySet mixin

The `AutoQuerySetMixin` offers a convenient way to automatically prefetch the required relations on a `QuerySet`.

```python
from django.db import models

from drf_auto_query.mixins import AutoQuerySetMixin


class MyModelQuerySet(AutoQuerySetMixin, models.Model):
    ...
    
    
class MyModel(models.Model):
    ...
    
    objects = models.Manager.from_queryset(MyModelQuerySet)()
```

This can then be used in a class based view.

```python
from rest_framework import generics

from my_app.models import MyModel
from my_app.serializers import MyModelSerializer


class MyModelList(generics.ListAPIView):
    serializer_class = MyModelSerializer
    queryset = MyModel.objects.prefetch_for(serializer_class)
```

Using the both the mixin and the prefetch function ensures that any annotations, joins, or other modifications to the 
QuerySet are preserved while automatically prefetching the necessary data for efficient serialization.

> :warning: Any multi-nested prefetches that have altered querysets might be 
> overwritten. This is a known issue and will be addressed in a future release.
> 
> Example of a multi-nested prefetch:
> ```python
> MyModel.objects.prefetch_related(
>     Prefetch(
>         'my_related_model',
>         queryset=MyRelatedModel.objects.prefetch_related(
>             Prefetch(
>                 'my_other_related_model',
>                 # This queryset might not be preserved.
>                 queryset=MyOtherRelatedModel.objects.annotate(count_something=Count('something'))
>             )
>         )
>     )
> )
> 
> MyModel.objects.prefetch_related(
>     Prefetch(
>         'my_related_model__my_other_related_model',
>         # This will be preserved.
>         queryset=MyOtherRelatedModel.objects.annotate(count_something=Count('something'))
>     )
> )
> ```

## Contributing

Interested in contributing? Check out the contributing guidelines. Please note that this project is released with a 
Code of Conduct. By contributing to this project, you agree to abide by its terms.


## License

`drf-auto-query` was created by Jakob Verlic. It is licensed under the terms of the MIT license.
