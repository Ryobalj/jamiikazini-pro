# homepage App

## Lengo Kuu
App ya `homepage` inawezesha kila **Institution** au **Business** kupata ukurasa wake wa umma (homepage) unaojitegemea, wenye sections zinazoweza kuongezwa, kuhaririwa, kupangwa upya, na kufutwa na mmiliki mwenyewe kupitia settings - bila msaada wa msanidi programu. Muundo umehamishwa (kwa marekebisho ya multi-tenant) kutoka mfumo uliothibitika wa `feevert-pro/home`.

## Majukumu Mahususi
- Kuhifadhi `HomePage` moja kwa kila Institution/Business (jina, tagline, logo, mawasiliano, mitandao ya kijamii, rangi za chapa)
- Kuhifadhi sections zinazoweza kuwashwa/kuzimwa na kupangwa (`order`, `is_active`): Hero, About (+ gallery ya picha), "Tunachofanya" (WhatWeDo, + huduma + picha), FAQ, Testimonials
- Kutoa endpoint ya umma (bila auth) inayounganisha sections zote hai za HomePage moja kwa mpangilio - tayari kuoneshwa
- Kutoa CRUD ya kila section, ikilindwa ili mmiliki wa Institution/Business pekee ndiye anaweza kuhariri

## Mahitaji Muhimu ya Kiufundi
- `HomePage` inaunganishwa na Institution AU Business kupitia Django ContentTypes (`GenericForeignKey`) - moja tu ya aina hizo kwa kila HomePage, na (content_type, object_id) ni ya kipekee
- Sections zote nyingine zinaunganishwa na `HomePage` (si moja kwa moja na Institution/Business) - hii inaifanya `HomePage` kuwa mzizi mmoja wa uhusiano wote
- Ulinzi wa uandishi: mmiliki halisi wa Institution/Business (`.owner`) pekee
- Usomaji wa umma: hauhitaji auth, unaonesha `is_active=True` tu, kwa mpangilio wa `order`

## Uhusiano na Apps Nyingine
- `kiini`: Institution ni mojawapo ya "owner" halali za HomePage
- `businesses`: Business ni "owner" nyingine halali ya HomePage
- `accounts`: uthibitisho wa `request.user` kwenye uhariri

## Muundo wa Mafaili
```
homepage/
├── models/
│   ├── home_page.py       # HomePage (generic FK owner)
│   ├── hero_section.py
│   ├── about_section.py   # AboutSection + AboutImage
│   ├── what_we_do.py       # WhatWeDo + WhatWeDoService + WhatWeDoImage
│   ├── faq.py
│   └── testimonial.py
├── serializers/
├── views/
├── urls/
└── tests/
```
