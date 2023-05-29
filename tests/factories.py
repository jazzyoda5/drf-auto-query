from factory.django import DjangoModelFactory

from tests.models import Parent


class ParentFactory(DjangoModelFactory):
    class Meta:
        model = Parent
