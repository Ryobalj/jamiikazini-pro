### 1. `gov_intergration`

# gov_integration App

## Lengo Kuu
App ya `gov_integration` inalenga kuwezesha **mawasiliano kati ya mfumo wa Jamiikazini na mifumo ya serikali** (kama NIDA, TRA, BRELA, TCU, NECTA, n.k) kwa madhumuni ya kuhakiki taarifa, kuhamasisha uwazi na kurahisisha taratibu za kitaasisi.

## Majukumu Mahususi
- Kuratibu na kuhifadhi maombi ya uthibitisho wa taarifa kutoka taasisi za serikali
- Kuhifadhi taarifa za API keys/token kutoka kwa mashirika ya serikali
- Kutuma na kupokea maombi (requests & responses) kutoka kwa mashirika ya serikali
- Kuwezesha uthibitisho wa:
  - Namba za utambulisho (NIDA)
  - Namba za usajili wa kampuni (BRELA)
  - TIN za walipa kodi (TRA)
  - Uhalali wa matokeo (NECTA, TCU)
- Kuweka rekodi za logi za mawasiliano na mashirika ya serikali

## Mahitaji Muhimu ya Kiufundi
- Ulinzi wa mawasiliano kwa kutumia `HTTPS` na `JWT` au `OAuth2`
- Rate-limiting na retries ili kuepuka kufungiwa na taasisi za serikali
- Audit trails na logging nzuri ya kila mawasiliano
- Background tasks kupitia Celery kwa maombi yanayochukua muda
- Uwezo wa ku-enable/disable integration fulani kupitia admin
- Uhusiano na app ya `accounts` kwa upande wa users wanaotuma maombi
- Interaction na `institutions`, `education`, `businesses`, `health` kwa lengo la uthibitisho

## Uhusiano na Apps Nyingine
- `accounts`: Inatumika kwa uthibitisho wa identity ya watumiaji kabla ya kuwasiliana na APIs za serikali
- `institutions`: Huwa zinahitaji uthibitisho wa uhalali wa usajili wao kwa mashirika ya serikali (kama TCU, BRELA)
- `education`: Huwa inahitaji kuhakiki matokeo ya mitihani (NECTA, TCU)
- `businesses`: Inahitaji kuthibitisha usajili wa biashara kutoka BRELA au TRA
- `health`: Inaweza kuhitaji kuthibitisha insured patients kupitia NHIF (ikiwa extended)

## Muundo wa Mafaili

```bas
gov_integration/
├── __init__.py
├── admin.py
├── apps.py
├── models/
│   ├── __init__.py
│   ├── api_endpoint.py          # Hifadhi endpoint za serikali
│   ├── verification_log.py      # Rekodi ya maombi yote yaliyotumwa
│   ├── service_config.py        # Settings za kila integration (token, status)
├── serializers/
│   ├── __init__.py
│   ├── verification_request.py
│   ├── service_config.py
├── views/
│   ├── __init__.py
│   ├── nida_verification.py
│   ├── tra_verification.py
│   ├── brela_verification.py
│   ├── necta_verification.py
│   ├── tcu_verification.py
├── urls.py
├── tasks.py                     # Celery tasks kwa background processing
├── helpers.py                   # Utility functions za kutuma maombi ya verification
├── permissions.py               # Ruhusa za kusimamia nani anaruhusiwa kutumia integration
└── tests/
    ├── __init__.py
    ├── test_nida.py
    ├── test_tra.py
    ├── test_brela.py
    ├── test_necta.py
    └── test_tcu.py
```
