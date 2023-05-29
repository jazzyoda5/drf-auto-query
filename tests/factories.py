from factory.django import DjangoModelFactory

from tests.models import Child, Parent


class ParentFactory(DjangoModelFactory):
    class Meta:
        model = Parent


class ChildFactory(DjangoModelFactory):
    class Meta:
        model = Child
