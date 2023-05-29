from django.db import models


class Parent(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()


class Child(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name="children")
    name = models.CharField(max_length=255)


class GrandChild(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="grand_children")
    name = models.CharField(max_length=255)
    age = models.IntegerField()
