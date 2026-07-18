# App: institutions

Hii ni app ndogo ya urithi (legacy shim). Muundo halisi wa taasisi (models,
serializers, views, middleware, tests) upo kwenye app ya **`kiini`**
(`kiini/models/institution.py`, `kiini/views/institution_views.py`, n.k.) -
haujawahi kujengwa hapa licha ya toleo la awali la faili hii kudai hivyo.

Kinachopo hapa ni kipande kimoja tu: `MyInstitutionsList`
(`institutions/views.py`), inayohudumia `GET /institutions/my/`
(imesajiliwa moja kwa moja kwenye `jamiikazini/api_urls.py`, si kupitia
`institutions/urls.py`). Inauliza data kutoka `kiini.models.institution.Institution`
moja kwa moja, sio kutoka modeli yoyote ndani ya app hii.

Kwa kazi yoyote mpya inayohusu taasisi (models, API, subdomain, staff, n.k.),
anza kwenye `kiini/`, sio hapa.
