# search/utils/db_fallback.py
#
# Shared stand-in for elasticsearch_dsl's Search/Hit objects, used by every
# document in search/documents/ when Elasticsearch is disabled (dev, or any
# environment with ELASTICSEARCH_ENABLED=False) so /search/ endpoints degrade
# to a plain Postgres query instead of crashing. Supports the subset of the
# ES DSL Search API actually used across search/views/*.py: query(), filter(),
# sort(), slicing, count(), update_from_dict(), execute(). Matching is
# best-effort (icontains/exact on the underlying queryset, no relevance
# scoring, no geo-distance filtering/sorting) - this is a fallback only. The
# real Document.search() (used when ELASTICSEARCH_ENABLED=True and a live
# cluster is reachable) is untouched by any of this and behaves exactly as
# django_elasticsearch_dsl intends.

from collections.abc import Mapping
from django.db.models import Q as DjangoQ


class FallbackHit(Mapping):
    """Wraps a plain dict (produced by Document().prepare(instance), so the
    field shape is identical to what a real ES hit would carry) so it can be
    read like a real elasticsearch_dsl Hit: attribute access (hit.field),
    item access (hit['field']), AND the full dict/Mapping protocol
    (.items()/.keys()/.values()) - DRF's DictField.to_representation() calls
    .items() directly on nested field values, which a plain attribute-only
    wrapper doesn't support. Nested dicts/lists are wrapped the same way."""

    def __init__(self, data, instance=None):
        self._data = data
        self._instance = instance

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            value = self._data[name]
        except KeyError:
            raise AttributeError(name)
        return self._wrap(value)

    def __getitem__(self, name):
        return self._wrap(self._data[name])

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __contains__(self, name):
        return name in self._data

    @staticmethod
    def _wrap(value):
        if isinstance(value, dict):
            return FallbackHit(value)
        if isinstance(value, list):
            return [FallbackHit._wrap(v) for v in value]
        return value

    def to_dict(self):
        return self._data

    @property
    def meta(self):
        return _FallbackMeta(id=str(getattr(self._instance, "pk", "")), sort=[], index="")

    def __repr__(self):
        return f"<FallbackHit {self._data.get('id', '')}>"


class _FallbackMeta(Mapping):
    """Stand-in for elasticsearch_dsl's Hit.meta (HitMeta) - supports both
    attribute access (hit.meta.id) and dict-style .get() (hit.meta.get('sort')),
    since real ES code uses both conventions interchangeably."""

    def __init__(self, **kwargs):
        self._data = kwargs

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(name)

    def __getitem__(self, name):
        return self._data[name]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)


class _HitsTotal:
    def __init__(self, value):
        self.value = value
        self.relation = "eq"


class _HitsWrapper:
    def __init__(self, hits_list, total):
        self._hits_list = hits_list
        self.total = _HitsTotal(total)

    def __iter__(self):
        return iter(self._hits_list)

    def __len__(self):
        return len(self._hits_list)

    def __getitem__(self, idx):
        return self._hits_list[idx]


class FallbackResponse:
    """Mimics enough of elasticsearch_dsl's Response: iterable of hits,
    len(), indexing/slicing, and .hits.total.value - several views report a
    total count (before pagination) separately from the returned page."""

    def __init__(self, hits_list, total):
        self._hits_list = hits_list
        self.hits = _HitsWrapper(hits_list, total)

    def __iter__(self):
        return iter(self._hits_list)

    def __len__(self):
        return len(self._hits_list)

    def __getitem__(self, idx):
        return self._hits_list[idx]

    def __bool__(self):
        return bool(self._hits_list)


class DBFallbackSearch:
    """Drop-in stand-in for an elasticsearch_dsl Search object."""

    def __init__(self, document_cls, queryset, search_fields=()):
        self.document_cls = document_cls
        self.queryset = queryset
        self.search_fields = search_fields
        self._slice = None

    def _clone(self, queryset=None):
        new = DBFallbackSearch(self.document_cls, queryset if queryset is not None else self.queryset, self.search_fields)
        new._slice = self._slice
        return new

    # -- ES DSL Search API subset --

    def query(self, *args, **kwargs):
        if args and isinstance(args[0], str):
            # ES shorthand: .query('multi_match', query=..., fields=[...])
            q_dict = {args[0]: kwargs}
            return self._clone(self._apply_q_dict(self.queryset, q_dict))
        q = args[0] if args else None
        return self._clone(self._apply_query(self.queryset, q))

    def filter(self, *args, **kwargs):
        if args and isinstance(args[0], str):
            # ES shorthand: .filter('term', field=value)
            if kwargs:
                field, value = next(iter(kwargs.items()))
                return self._clone(self._apply_term(self.queryset, field, value))
            return self
        if args:
            return self._clone(self._apply_query(self.queryset, args[0]))
        return self

    def sort(self, *args):
        qs = self.queryset
        order_fields = [a for a in args if isinstance(a, str)]
        # dict-based sorts (e.g. geo-distance) have no equivalent without a
        # spatial index in this fallback - best-effort skip, not an error.
        if order_fields:
            try:
                qs = qs.order_by(*order_fields)
            except Exception:
                pass
        return self._clone(qs)

    def update_from_dict(self, query_dict):
        try:
            must = query_dict.get("query", {}).get("bool", {}).get("must", [])
            for clause in must:
                mm = clause.get("multi_match")
                if mm and mm.get("query"):
                    return self._clone(self._apply_text(self.queryset, mm["query"]))
        except Exception:
            pass
        return self

    def count(self):
        return self.queryset.count()

    def __getitem__(self, key):
        new = self._clone()
        new._slice = key
        return new

    def execute(self):
        total = self.queryset.count()
        qs = self.queryset
        if self._slice is not None:
            qs = qs[self._slice]
        doc = self.document_cls()
        hits = []
        for instance in qs:
            try:
                data = doc.prepare(instance)
            except Exception:
                continue
            hits.append(FallbackHit(data, instance))
        return FallbackResponse(hits, total)

    # -- best-effort ES Q -> ORM translation --

    def _apply_query(self, qs, q):
        if q is None:
            return qs
        q_dict = q.to_dict() if hasattr(q, "to_dict") else q
        return self._apply_q_dict(qs, q_dict)

    def _apply_q_dict(self, qs, q_dict):
        if not q_dict:
            return qs
        # bool must/filter clauses are often real elasticsearch_dsl Query
        # objects (e.g. Q("term", ...)), not plain dicts - normalize first.
        if hasattr(q_dict, "to_dict"):
            q_dict = q_dict.to_dict()
        if "match_all" in q_dict:
            return qs
        if "multi_match" in q_dict:
            return self._apply_text(qs, q_dict["multi_match"].get("query", ""))
        if "match" in q_dict:
            for _field, value in q_dict["match"].items():
                qs = self._apply_text(qs, value if isinstance(value, str) else value.get("query", ""))
            return qs
        if "term" in q_dict:
            for field, value in q_dict["term"].items():
                qs = self._apply_term(qs, field, value)
            return qs
        if "bool" in q_dict:
            for clause in q_dict["bool"].get("must", []):
                qs = self._apply_q_dict(qs, clause)
            for clause in q_dict["bool"].get("filter", []):
                qs = self._apply_q_dict(qs, clause)
            return qs
        if "geo_distance" in q_dict:
            # Not supported without a spatial index equivalent - no-op.
            return qs
        return qs

    def _apply_text(self, qs, query):
        if not query or not self.search_fields:
            return qs
        condition = DjangoQ()
        for field in self.search_fields:
            condition |= DjangoQ(**{f"{field.replace('.', '__')}__icontains": query})
        return qs.filter(condition)

    def _apply_term(self, qs, field, value):
        orm_field = field.replace(".", "__")
        try:
            return qs.filter(**{orm_field: value})
        except Exception:
            return qs
