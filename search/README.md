### 10. `search`

# search App

## Lengo Kuu
App ya `search` inahusika na kutafuta bidhaa, huduma, biashara, au taasisi kwenye mfumo wa jamiikazini. Inatumia Elasticsearch kufanya utafutaji wa haraka na wa kiwango cha juu unaozingatia `relevance`, `location`, `category`, `rating`, na `lugha`.

## Majukumu Mahususi
- Kuruhusu watumiaji kutafuta bidhaa au huduma kwa jina, maelezo, au kategoria
- Kufanya search kwa kutumia lugha ya mtumiaji (multilingual search)
- Kutumia geolocation ili kutoa matokeo yaliyo karibu zaidi na mtumiaji
- Kuwezesha filters kwa bei, aina, location, taasisi, au biashara
- Kuunganisha na apps nyingine kupitia indexing (kama `products`, `institutions`, `businesses`)
- Kufanya search scaling kupitia Elasticsearch cluster

## Mahitaji Muhimu ya Kiufundi
- Elasticsearch 8.x au zaidi (inaweza kuwa hosted au local)
- Django-Haystack au django-elasticsearch-dsl kama bridge
- Model za Elasticsearch index (kwa bidhaa, huduma, taasisi, n.k)
- JWT authentication kwa watumiaji waliologin
- Query filters: `term`, `match`, `geo_distance`, `range`, `multi_match`
- Uwezo wa `autocomplete` na `search suggestions`
- Real-time indexing kwa mabadiliko kwenye data muhimu

## Uhusiano na Apps Nyingine
- `products`: Kutafuta bidhaa kwa jina, maelezo, bei
- `institutions`: Kutafuta taasisi kwa jina au huduma
- `businesses`: Kutafuta biashara kulingana na eneo au huduma
- `education`, `health`, `logistics`: Kutoa search za ndani kulingana na domain
- `accounts`: Kutumia preferences za mtumiaji kuboresha relevance ya search

## Muundo wa Mafaili

```bas
search/
├── __init__.py
├── apps.py
├── urls.py
├── views/
│   ├── __init__.py
│   └── search.py             # Main search logic
├── documents/
│   ├── __init__.py
│   ├── product.py            # Elasticsearch indexing ya bidhaa
│   ├── business.py           # Indexing ya biashara
│   └── institution.py        # Indexing ya taasisi
├── serializers/
│   └── search.py             # Serializer ya matokeo
├── utils/
│   └── query_builder.py      # Query construction logic ya Elasticsearch
├── tests/
│   ├── __init__.py
│   └── test_search.py
└── permissions.py
```

---

## Centralized Search

Search functionality on `jamiikazini.com` includes:
- Auto-detect location (via IP, browser, GPS)
- Display sorted results by distance
- Paginated view (10–20 per page)
- Filter by category, rating, keywords
- Distance and location handled using PostGIS

---

## Search Template Example

**`search_results.html` includes:**
- Search bar at top
- Filters (category, rating, etc.)
- Sort options: Nearest | Popular | Recent
- Paginated grid of results
