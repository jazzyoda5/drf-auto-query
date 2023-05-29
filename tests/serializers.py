from rest_framework import serializers

from tests import models


class ParentNameSerializer(serializers.Serializer):
    name = serializers.CharField()

    class Meta:
        model = models.Parent


class ChildWithNestedParentNameSerializer(serializers.Serializer):
    parent = ParentNameSerializer()

    class Meta:
        model = models.Child


class ChildWithNestedParentModelSerializer(serializers.ModelSerializer):
    parent = ParentNameSerializer()

    class Meta:
        model = models.Child
        fields = "__all__"


class ChildModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Child
        fields = "__all__"


class GrandChildSerializer(serializers.Serializer):
    name = serializers.CharField()
    age = serializers.IntegerField()

    class Meta:
        model = models.GrandChild


class GrandChildNameSerializer(serializers.Serializer):
    name = serializers.CharField()

    class Meta:
        model = models.GrandChild


class FullChildSerializer(serializers.Serializer):
    grand_children = GrandChildSerializer(many=True)
    name = serializers.CharField()

    class Meta:
        model = models.Child


class ChildWithNestedGrandChildrenNamesSerializer(serializers.Serializer):
    grand_children = GrandChildNameSerializer(many=True)

    class Meta:
        model = models.Child


class FullFamilySerializer(serializers.Serializer):
    children = FullChildSerializer(many=True)
    name = serializers.CharField()
    description = serializers.CharField()

    class Meta:
        model = models.Parent
