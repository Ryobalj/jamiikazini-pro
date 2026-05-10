### 7. `Business (Businesses App)`

# businesses App

## Lengo Kuu
App ya `businesses` inasimamia taarifa na shughuli za kibiashara ndani ya mfumo wa jamiikazini. Inaruhusu wafanyabiashara kusajili biashara zao, kusimamia bidhaa, huduma, matawi, na kufuatilia wateja wao.

## Majukumu Mahususi
- Kuwezesha usajili wa biashara na kudhibiti taarifa zake (`Business`)
- Kusimamia bidhaa na huduma zinazotolewa na biashara (`Product`, `Service`)
- Kuratibu matawi au maeneo ya biashara (`Branch`)
- Kusimamia aina za biashara na sekta mbalimbali (`BusinessCategory`)
- Kufuatilia maoni na viwango kutoka kwa wateja (`Review`)
- Kuweka taarifa za mawasiliano, maeneo ya biashara, na saa za kazi

## Mahitaji Muhimu ya Kiufundi
- Model ya `Business` lazima iwe na uhusiano na taasisi au mmiliki aliye kwenye `User` (kutoka `kiini`)
- Location field kwa kila biashara (PostGIS) kwa ajili ya kutafuta zilizo karibu
- Support kwa lugha nyingi (multilingual support)
- CRUD views zenye permission kwa biashara husika pekee
- Mteja anaweza kuona huduma au bidhaa kwa urahisi, na kuwasiliana na mmiliki
- Search feature kwa bidhaa/huduma zilizopo katika biashara zote

## Uhusiano na Apps Nyingine
- `accounts`: Hutoa mmiliki wa biashara au mteja
- `kiini`: Huwezesha kufuatilia mtumiaji na taasisi
- `payments`: Kwa ajili ya kushughulikia malipo ya huduma au bidhaa
- `logistics`: Usafirishaji wa bidhaa kwa wateja
- `gov_integration`: Kusajili biashara rasmi na kuripoti kwa mamlaka
- `kiini`: Inabeba lugha, nchi, na location zinazotumika kwenye biashara

## Muundo wa Mafaili

```bas
businesses/
├── __init__.py
├── admin.py
├── apps.py
├── models/
│   ├── __init__.py
│   ├── business.py          # Biashara yenyewe
│   ├── branch.py            # Matawi ya biashara
│   ├── product.py           # Bidhaa zinazouzwa
│   ├── service.py           # Huduma zinazotolewa
│   ├── review.py            # Tathmini na maoni ya wateja
│   └── category.py          # Aina za biashara/huduma
├── serializers/
│   ├── __init__.py
│   ├── business.py
│   ├── branch.py
│   ├── product.py
│   ├── service.py
│   ├── review.py
│   └── category.py
├── views/
│   ├── __init__.py
│   ├── business.py
│   ├── branch.py
│   ├── product.py
│   ├── service.py
│   ├── review.py
│   └── category.py
├── urls.py
├── tests/
│   ├── __init__.py
│   ├── test_business.py
│   ├── test_branch.py
│   ├── test_product.py
│   ├── test_service.py
│   ├── test_review.py
│   └── test_category.py
└── permissions.py
```

# 🌍 Jamiikazini API Route Tree (Nested URLs)

> Version: v1  
> Base Path: `/api/v1/businesses/`  
> Mahusiano kulingana na models:  
> - `Business` ➜ `Branches`, `Products`, `Services`
> - `Branch` ➜ `Services` (M2M)
> - `Product` ➜ `Orders`, `Reviews`
> - `Service` ➜ `Bookings`, `Reviews`

---

## 🔹 Business Endpoints

- `GET /businesses/`
- `POST /businesses/`
- `GET /businesses/{business_pk}/`
- `PUT/PATCH /businesses/{business_pk}/`
- `DELETE /businesses/{business_pk}/`

---

## 🏢 Branches (under Business)

- `GET /businesses/{business_pk}/branches/`
- `POST /businesses/{business_pk}/branches/`
- `GET /businesses/{business_pk}/branches/{branch_pk}/`
- `PUT/PATCH /businesses/{business_pk}/branches/{branch_pk}/`
- `DELETE /businesses/{business_pk}/branches/{branch_pk}/`

---

## 🧰 Services (under Business)

- `GET /businesses/{business_pk}/services/`
- `POST /businesses/{business_pk}/services/`
- `GET /businesses/{business_pk}/services/{service_pk}/`
- `PUT/PATCH /businesses/{business_pk}/services/{service_pk}/`
- `DELETE /businesses/{business_pk}/services/{service_pk}/`

---

## 🛍️ Products (under Business)

- `GET /businesses/{business_pk}/products/`
- `POST /businesses/{business_pk}/products/`
- `GET /businesses/{business_pk}/products/{product_pk}/`
- `PUT/PATCH /businesses/{business_pk}/products/{product_pk}/`
- `DELETE /businesses/{business_pk}/products/{product_pk}/`

---

### 📦 Orders (under Product)

- `GET /businesses/{business_pk}/products/{product_pk}/orders/`
- `POST /businesses/{business_pk}/products/{product_pk}/orders/`

---

### 🌟 Reviews (under Product)

- `GET /businesses/{business_pk}/products/{product_pk}/reviews/`
- `POST /businesses/{business_pk}/products/{product_pk}/reviews/`

---

## 🏬 Services at Branch (for Bookings & Reviews)

> `Branch` ➜ `services` (Many-to-Many)

---

### 📅 Bookings (under Branch ➜ Service)

- `GET /businesses/{business_pk}/branches/{branch_pk}/services/{service_pk}/bookings/`
- `POST /businesses/{business_pk}/branches/{branch_pk}/services/{service_pk}/bookings/`

---

### 📝 Reviews (under Branch ➜ Service)

- `GET /businesses/{business_pk}/branches/{branch_pk}/services/{service_pk}/reviews/`
- `POST /businesses/{business_pk}/branches/{branch_pk}/services/{service_pk}/reviews/`

# 🌍 Jamiikazini API - Public & Non-Nested Endpoints

> Version: v1  
> Base Path: `/api/v1/businesses/`

---

## 🛍️ Public Products

- `GET /products/nearby-list/`  
  🔎 Rudisha bidhaa zilizo karibu na mtumiaji (GeoDjango support).

- `GET /products/{slug}/url/`  
  🔗 Rudisha URL ya bidhaa kwa matumizi ya client/share.

---

## 📚 Business Categories

- `GET /categories/`  
  ✅ Pata orodha ya aina za biashara.

- `POST /categories/` *(Admin or staff only)*  
  ➕ Unda aina mpya ya biashara.

- `GET /categories/{slug}/`  
  🔎 Angalia taarifa kamili ya aina ya biashara.

---

## 📦 Orders (Non-nested version)

- `GET /orders/`  
  📜 Orodha ya orders za mteja (authenticated user).

- `POST /orders/`  
  🛒 Tuma oda mpya (mteja akichagua bidhaa/huduma).

- `GET /orders/{uuid}/`  
  🔍 Angalia oda moja.

---

## 📅 Bookings

- `GET /bookings/`  
  📆 Orodha ya bookings za mtumiaji.

- `POST /bookings/`  
  ➕ Booking ya huduma (if outside nested route).

- `GET /bookings/{uuid}/`  
  🔍 Angalia taarifa ya booking moja.

---

## 📑 Booking Logs

- `GET /booking-logs/`  
  📜 Orodha ya mabadiliko kwenye booking (status changes, etc).

- `POST /booking-logs/`  
  ➕ Rekodi tukio jipya la booking (admin use or system).

---

## 🔓 Public Info (Static & Readonly)

- `GET /public/featured-products/`  
  ⭐ Bidhaa zilizochaguliwa mbele ya wateja.

- `GET /public/top-services/`  
  💎 Huduma bora zinazopendekezwa.

- `GET /public/business-of-the-week/`  
  🏆 Biashara inayopendekezwa wiki hii.

---

## ✅ Notes

- All routes under this file are under: `/api/v1/businesses/`
- `Authentication` required for `POST`, optional for most `GET`s.
- Rate-limiting, pagination, search, and filtering enabled on most list routes.


/api/v1/businesses/                                # List, create businesses
/api/v1/businesses/{business_id}/                  # Retrieve, update, delete a business

├── branches/                                      # Nested: Business Branches
│   /api/v1/businesses/{business_id}/branches/         # List, create branches
│   /api/v1/businesses/{business_id}/branches/{branch_id}/
│
│   ├── products/                                  # Products under a branch
│   │   /api/v1/businesses/{business_id}/branches/{branch_id}/products/
│   │   /api/v1/businesses/{business_id}/branches/{branch_id}/products/{product_id}/
│   │
│   │   ├── orders/                                # Orders per product
│   │   │   /api/v1/businesses/{business_id}/branches/{branch_id}/products/{product_id}/orders/
│   │   └── reviews/                               # Reviews per product
│   │       /api/v1/businesses/{business_id}/branches/{branch_id}/products/{product_id}/reviews/
│   │
│   └── services/                                  # Services under a branch
│       /api/v1/businesses/{business_id}/branches/{branch_id}/services/
│       /api/v1/businesses/{business_id}/branches/{branch_id}/services/{service_id}/
│
│       ├── bookings/                              # Bookings per service
│       │   /api/v1/businesses/{business_id}/branches/{branch_id}/services/{service_id}/bookings/
│       └── reviews/                               # Reviews per service
│           /api/v1/businesses/{business_id}/branches/{branch_id}/services/{service_id}/reviews/
