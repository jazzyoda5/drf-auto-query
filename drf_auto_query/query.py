from typing import Type

from django.db.models import Prefetch, QuerySet
from django.db.models.constants import LOOKUP_SEP
from rest_framework.serializers import Serializer

from drf_auto_query.types import Relation
from drf_auto_query.utils import FieldNode, build_field_tree


# TODO: No need for this function, we can just use the QueryBuilder directly.
def build_queryset(
    queryset: QuerySet,
    # TODO [jakob]: This should allow setting both the serializer class and the serializer instance.
    serializer: Type[Serializer] | Serializer,
    fields: list[str] = None,
):
    """
    Given a serializer class and a queryset, join and select all the fields
    that are needed to serialize the queryset and prefetch all the related
    models.

    :param queryset: QuerySet instance that should be used to build the queryset.
    :param serializer: Serializer class or instance that should be used to build the queryset.
    :param fields: Only build query for specific serializer fields.

    Requirements:
    - Do not overwrite any annotations or prefetches on the queryset
    - Return nice errors, when serializer field does not match a field on the queryset. (?)
    """

    # serializer = serializer_class()
    serializer = get_serializer(serializer)
    query_builder = QueryBuilder(queryset)
    return query_builder.build_for(serializer)


class PrefetchPath:
    def __init__(self, path: list[Prefetch | str]):
        self.path = path

    def __str__(self):
        return self.full_path

    def __repr__(self):
        return f"<PrefetchPath '{self.full_path}'>"

    @property
    def full_path(self):
        return LOOKUP_SEP.join(n if isinstance(n, str) else n.prefetch_through for n in self.path)

    @property
    def queryset(self):
        return (
            self.path[-1].queryset
            if isinstance(self.path[-1], Prefetch) and self.path[-1].queryset is not None
            else None
        )


def get_prefetched(queryset: QuerySet):
    """
    Given a queryset, return a dictionary of all the prefetched paths that are
    already prefetched on the queryset.
    """

    prefetched: list[PrefetchPath] = []

    def traverse_prefetches(qs, path: list = None):
        if not path:
            path = []
        for prefetch in qs._prefetch_related_lookups:  # noqa
            node_path = path.copy() + [prefetch]
            prefetched.append(PrefetchPath(path=node_path))
            if isinstance(prefetch, Prefetch) and prefetch.queryset is not None:
                print("hello")
                traverse_prefetches(prefetch.queryset, path=node_path)

    traverse_prefetches(queryset)  # noqa

    prefetched_map = {}
    for prefetch in prefetched:
        if prefetch.full_path in prefetched_map:
            raise ValueError(
                f"Prefetch {prefetch.full_path} is prefetched multiple times. \n"
                f"\tPerhaps the order of prefetches is incorrect?"
            )
        prefetched_map[prefetch.full_path] = prefetch
    return prefetched_map


class QueryBuilder:
    def __init__(self, queryset: QuerySet):
        self.initial_queryset = queryset
        self.already_prefetched: dict[str, PrefetchPath] = get_prefetched(queryset)

        self._queryset = None
        self._added_prefetches: list[Prefetch] = []
        self._added_joins: list[str] = []

    def reset(self):
        self._queryset = self.initial_queryset.all()
        self._added_prefetches = []
        self._added_joins = []

    def build_for(
        self,
        serializer: Serializer | type[Serializer],
        fields: list[str] = None,  # TODO: This would be a nice feature
    ):
        """
        Return a copy of the queryset with all the fields needed to serialize
        the queryset selected and all the related models prefetched for the
        given serializer instance.

        :param serializer: Serializer class or instance that should be used to build the queryset.
        :param fields: Only build query for specific serializer fields.
        """

        serializer = get_serializer(serializer)

        self.reset()

        field_tree = build_field_tree(serializer, self._queryset.model)

        for node in field_tree.children:
            self._process_node(node)

        if self._added_joins:
            self._queryset = self._queryset.select_related(*self._added_joins)
        if self._added_prefetches:
            self._queryset = self._queryset.prefetch_related(*self._added_prefetches)

        return self._queryset

    def _process_node(
        self,
        node: FieldNode,
        # nearest_qs: QuerySet = None,
        # path_from_nearest_qs: str = "",
        parent: str = "",
        join_to: Prefetch | str = None,
    ):
        source = f"{parent}{LOOKUP_SEP}{node.source}" if parent else node.source

        if node.parent_relation == Relation.X_TO_MANY:
            # what if it is already prefetched?
            if source not in self.already_prefetched:
                prefetch = Prefetch(source, queryset=self._get_prefetch_queryset(node, source))
                self._added_prefetches.append(prefetch)

                # We need to track the deepest prefetch queryset, so we can use it
                # for joining single related fields.
                join_to = prefetch
            else:
                join_to = self.already_prefetched[source].path[-1]

        elif node.parent_relation == Relation.X_TO_ONE:
            if not join_to:
                self._added_joins.append(source)
            else:
                if isinstance(join_to, str):
                    # If prefetch is just defined as a string, we can not join related tables to it.
                    # What we can do is convert the prefetch to a `Prefetch` instance, and replace the
                    # defined prefetch on the queryset instance.
                    join_to = _normalize_prefetch_on_queryset(self._queryset, join_to)
                if join_to.queryset is None:
                    # If not yet defined, we define set a queryset instance to the prefetch,
                    # so that we can add `select_related` statements.
                    join_to.queryset = self._get_prefetch_queryset(node, source)

                join = source[len(join_to.prefetch_through) + len(LOOKUP_SEP) :]
                join_to.queryset = join_to.queryset.select_related(join)

        for child_node in node.children:
            self._process_node(child_node, source, join_to=join_to)

    def _get_prefetch_queryset(self, node: FieldNode, source: str):
        if source in self.already_prefetched:
            queryset = self.already_prefetched[source].queryset
            if queryset is not None:
                return queryset

        if not node.model:
            raise Exception("Could not figure out the model")  # TODO: improve this error

        return node.model.objects.all()

    # def _build_node_query(self, node: FieldNode, parent: str = "") -> list[Prefetch, str]:
    #     prefetches = []
    #     lookup = f"{parent}{LOOKUP_SEP}{node.source}" if parent else node.source
    #
    #     if node.parent_relation == ModelRelation.RELATED_MODEL:
    #         # - Single related field should be joined.
    #         # - If there is a many related field in the source path to the single related
    #         #   field, single related field should be joined at the level of the prefetch.
    #         # - If there is a prefetch already added to any of the nodes in the source path,
    #         #   add the join to the bottom most prefetch queryset.
    #         #
    #         # How can I find the queryset for which I need to add prefetches for?
    #         #
    #
    #         # For a related model
    #         ...
    #
    #     # - Many related field should be prefetched.
    #     # TODO: test adding the same prefetch but on multiple levels, Example: top level prefetch and nested prefetch. Does it clash?
    #     # - When possible, the prefetch shouldbe added to the top most level. Usually this
    #     #   will be the most optimal solution, with large datasets.
    #     # - If users would like to optimize the prefetch, they can do so manually.
    #     return []


def get_serializer(serializer: Type[Serializer] | Serializer) -> Serializer:
    # Very sad, but we need to instantiate the serializer to be able to use some DRF
    # utils to help us get info on the serializer.
    if isinstance(serializer, type):
        return serializer()
    return serializer


def _normalize_prefetch_on_queryset(queryset: QuerySet, prefetch: str) -> Prefetch:
    """
    Convert a string prefetch to a `Prefetch` object, so that we can add
    additional `select_related` statements to the queryset.
    """

    normalized_prefetch = None

    # A bit annoying that prefetches are defined as a tuple on the queryset, so we have to
    # overwrite the whole tuple, not just a single item.
    lookups = []

    for existing_prefetch in queryset._prefetch_related_lookups:
        if existing_prefetch == prefetch:
            normalized_prefetch = Prefetch(prefetch)
            lookups.append(normalized_prefetch)
        else:
            lookups.append(existing_prefetch)

    if not normalized_prefetch:
        raise ValueError(f"Could not find prefetch {prefetch} on the queryset.")

    queryset._prefetch_related_lookups = tuple(lookups)
    return normalized_prefetch
