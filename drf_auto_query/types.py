import enum
from dataclasses import dataclass
from typing import TypeVar, Union

from django.db.models import Model, QuerySet, Prefetch
from rest_framework.fields import Field
from rest_framework.serializers import Serializer


SerializerField = Union[Field, Serializer]


ModelType = TypeVar("ModelType", bound=Model)


class Relation(enum.Enum):
    FIELD = 0
    ONE_TO_ONE = 1
    ONE_TO_MANY = 2
    NONE = 3


@dataclass(frozen=True)
class PrefetchInfo:
    prefetch: Prefetch | str
    # The full path from the root queryset being serialized to the field being prefetched.
    # This should correspond with the serializer field source exactly.
    path: str
    # The queryset instance to which the prefetch is applied.
    base_queryset: QuerySet
    # Path to the queryset instance to which the prefetch is applied.
    base_queryset_path: str = ""


@dataclass
class QuerySetInfo:
    prefetches: dict[str, PrefetchInfo]
