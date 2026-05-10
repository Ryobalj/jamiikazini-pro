### 3. `kiini`

# kiini App

## Lengo Kuu
App ya `kiini` ni **nguzo kuu ya utawala na udhibiti wa mfumo wa Jamiikazini**. Inahusiana moja kwa moja na taasisi (institutions), watumiaji (users), majukumu (roles), na usalama wa mawasiliano (authentication & authorization).

## Majukumu Mahususi
- Kuweka msingi wa data ya watumiaji, taasisi, majukumu, na vibali
- Kusimamia uhusiano wa mtumiaji na taasisi (user-institution isolation)
- Kutoa njia ya kusimamia JWT authentication na token refresh
- Kuhakikisha mfumo wa roles-based access control unafanya kazi ipasavyo
- Kuhifadhi rekodi za login/logout, password reset, na user activity
- Kuhusisha watumiaji wa aina tofauti: admin, institution admin, staff, client

## Mahitaji Muhimu ya Kiufundi
- Custom User model (`AbstractUser`) yenye field ya `role`, `institution`, n.k
- Authentication na `djangorestframework-simplejwt`
- Custom permission classes na decorators
- Subdomain-based data isolation kupitia middleware (`InstitutionMiddleware`)
- Token refresh, revoke, blacklist n.k
- Kuweka helper functions kwa usimamizi wa users na institutions

## Uhusiano na Apps Nyingine
- `accounts`: Inapokea na kurudi JWT tokens kwa login/logout
- `institutions`: Inahusisha taasisi na user profiles
- `education`, `businesses`, `health`: Zinahitaji uthibitisho wa roles na taasisi
- `gov_integration`: Hutumia taarifa za user au taasisi kwa kufanya verification
- `payments`, `logistics`: Zinahitaji user authentication na taasisi context

## Muundo wa Mafaili

```bas
kiini/
├── __init__.py
├── admin.py
├── apps.py
├── models/
│   ├── __init__.py
│   ├── user.py                # Custom user model with roles
│   ├── institution.py         # Institution model (centralized here)
│   └── role.py                # Optional: extendable roles structure
├── serializers/
│   ├── __init__.py
│   ├── user.py
│   ├── institution.py
│   └── auth.py                # JWT login/logout/register serializers
├── views/
│   ├── __init__.py
│   ├── user.py
│   ├── institution.py
│   └── auth.py
├── urls.py
├── middleware/
│   └── institution_middleware.py   # Detect subdomain and set institution context
├── decorators.py              # User-in-institution, role-based restrictions
├── permissions.py            # Custom permissions for different roles
├── helpers/
│   ├── user_helpers.py
│   └── institution_helpers.py
├── tests/
│   ├── __init__.py
│   ├── test_user.py
│   ├── test_auth.py
│   └── test_institution.py
└── utils.py                  # General helpers, if needed
```
