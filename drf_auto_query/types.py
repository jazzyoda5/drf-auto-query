import enum
from typing import TypeVar, Union

from django.db.models import Model
from rest_framework.fields import Field
from rest_framework.serializers import Serializer


SerializerField = Union[Field, Serializer]


ModelType = TypeVar("ModelType", bound=Model)


class Relation(enum.Enum):
    FIELD = 0
    X_TO_ONE = 1  # TODO [jakob]: rename to X_TO_ONE
    X_TO_MANY = 2  # TODO [jakob]: rename to X_TO_MANY
    NONE = 3
