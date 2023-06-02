import enum
from typing import TypeVar, Union

from django.db.models import Model
from rest_framework.fields import Field
from rest_framework.serializers import Serializer


SerializerField = Union[Field, Serializer]


ModelType = TypeVar("ModelType", bound=Model)


class ModelRelation(enum.Enum):
    FIELD = "field"
    RELATED_MODEL = "related_model"
    MANY_RELATED_MODEL = "many_related_model"
    NONE = "none"
