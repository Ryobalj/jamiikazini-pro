### 2. `accounts`

# App ya Accounts - Mradi wa Jamiikazini

## Lengo Kuu

App ya `accounts` inasimamia usajili, uingiliaji (authentication), na majukumu (roles) ya watumiaji wa mfumo wa Jamiikazini. Inazingatia utofauti wa watumiaji kulingana na taasisi zao (subdomains).

## Malengo Mahususi

- Kusimamia usajili wa watumiaji wapya kulingana na taasisi.
- Kuwezesha login, logout, na uhuishaji wa tokeni za JWT.
- Kuhifadhi taarifa muhimu za watumiaji kama role na taasisi wanazotoka.
- Kuzuia mtumiaji kuona au kufanyia kazi taarifa za taasisi nyingine.

## Majukumu Makuu

- Usajili na uingiliaji wa watumiaji.
- Kuhifadhi taarifa za mtumiaji (profile).
- Uthibitisho wa nenosiri na kubadili nenosiri.
- Kusimamia tokeni za JWT (access & refresh).
- Kulinda rasilimali kulingana na jukumu la mtumiaji.

## Mahitaji Muhimu ya Kiufundi

- **Custom User Model:** Mtumiaji anaunganishwa na `Institution`, na ana jukumu (`role`) kama `ADMIN`, `STAFF`, `CLIENT`, n.k.
- **JWT Authentication:** Mfumo unatumia tokeni za JWT kwa login, logout, na token refresh.
- **Role-Based Access Control (RBAC):** Watumiaji wana ruhusa tofauti kulingana na role walizonazo.
- **Multi-Tenancy Support:** Kila mtumiaji anaweza kuona na kushughulikia data za taasisi yake tu.
- **Decorators na Permissions:** Kutumia decorators na permission classes kulinda views dhidi ya access zisizoruhusiwa.
- **Endpoints Muhimu:**
  - `/api/accounts/register/`
  - `/api/accounts/login/`
  - `/api/accounts/logout/`
  - `/api/accounts/token/refresh/`
  - `/api/accounts/profile/`
  - `/api/accounts/password/change/`

## Uhusiano na Apps Nyingine

- **Core:** Inapata `Institution` ya mtumiaji kupitia model kutoka core.
- **Institutions:** Inahakikisha kuwa watumiaji wanaweza kufanyia kazi taasisi zao tu.
- **Education, Health, Logistics, Businesses:** Hutegemea data ya user na roles kwa ajili ya authorization.
- **Gov_Integration:** Inaweza kuunganishwa na mifumo ya serikali kwa ajili ya identity verification (KYC).
- **Payments:** Hutumia taarifa za akaunti ili kudhibiti upatikanaji wa huduma za malipo.

## Faida kwa Mfumo

- Ulinzi wa hali ya juu kwa watumiaji kwa kutumia JWT na RBAC.
- Usajili wa watumiaji wenye ufanisi kulingana na taasisi.
- Rahisi kuunganisha na mifumo ya serikali au third-party auth.
- Inasaidia separation ya data kwa taasisi kupitia subdomain.

## Muundo wa Mafaili

```plaintext
accounts/
├── __init__.py
├── admin.py
├── apps.py
├── models/
│   ├── __init__.py
│   └── user.py
├── serializers/
│   ├── __init__.py
│   └── user.py
├── views/
│   ├── __init__.py
│   └── user.py
├── urls.py
├── permissions.py
├── decorators.py
├── helpers.py
├── tokens.py
├── backends.py
├── tests/
│   ├── __init__.py
│   ├── test_user_model.py
│   ├── test_user_auth.py
│   └── test_permissions.py
```
