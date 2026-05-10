# Jamiikazini Enterprises 🌍

**Jamiikazini** ni jukwaa la kidijitali kwa taasisi, biashara, mafundi,
na wananchi binafsi Afrika Mashariki. Linalenga kuwa kitovu cha huduma 
muhimu kama elimu, afya, usafirishaji, na malipo kwa kutumia teknolojia 
ya kisasa — inayojali lugha, maeneo, na mahitaji ya jamii.

> *"Build the infrastructure of opportunity — digitally."*

---

## 📌 Vipengele Muhimu

* ✅ Multi-tenant architecture (subdomain per institution)
* 🌍 Lugha nyingi (i18n): Kiswahili, Kiingereza, Kinyarwanda, Kiganda
* 📍 Tafutaji la kijiografia kwa kutumia PostGIS
* 🔐 JWT authentication + Access control kwa nafasi (roles)
* 🧠 Core logic abstraction kupitia `kiini` app
* 💬 Ujumbe wa papo kwa papo (Redis + Celery)
* 📱 Malipo ya simu: M-Pesa, PawaPay (kupitia `jamiiwallet`)
* 🏥 Huduma za jamii: Elimu, afya, biashara, usafirishaji
* 🿲️ Uunganishaji wa taasisi zote: mashule, hospitali, SMEs, Saccos
* 🌐 Ushirikiano na mifumo ya serikali: NIDA, TRA, NECTA

---

## 🚣️ Mpango Kazi: Vision 2030

### 🥇 Awamu ya I (2025–2026): Kujenga Msingi

* Usajili wa Taasisi
* Mfumo wa majina kupitia subdomains
* Utambulisho salama: JWT, 2FA
* Lugha nyingi kwa watumiaji
* Ramani na utafutaji wa huduma za karibu

### 🥈 Awamu ya II (2026–2027): Ushirikiano, Malipo na Taarifa

* Wallet na loyalty systems
* Ujumbe wa moja kwa moja (jamiichat)
* Ushirika wa kijamii (chamas, kura, kampeni)
* Ulinganishaji wa taarifa za serikali
* Dashibodi za uongozi na taarifa

### 🥉 Awamu ya III (2028–2030): Ajira, Maarifa, Ujasiriamali

* Soko la ajira na freelancers
* Elimu huria na maudhui ya ndani
* AI kwa mapendekezo ya huduma
* Tafiti na whitepapers za maendeleo
* Ushirikiano na NGOs na jamii

---

## 🧪 Majaribio na CI/CD

* `pytest` kwa unit & integration tests
* PostGIS tests kwa tafutaji
* Rate limiting, roles, permission, na 2FA
* GitHub Actions kwa CI/CD

---

## 🚀 Mwongozo wa Uendeshaji (Deployment)

* Backend: Gunicorn + NGINX
* Async tasks: Redis + Celery
* Static/media files: Whitenoise au AWS S3
* Secrets: `.env` files zinasimamiwa na `.jamiienv_export.sh`

---

## 🔐 Usalama & Uzingatiaji wa Sheria

* HTTPS + AES encryption
* JWT na rotating refresh tokens
* Two-factor authentication (2FA)
* GDPR & Data Anonymization
* Bandit + IP throttling + Audit Logs

---

## 🤝 Mchango wa Jamii

Mchango wowote unakaribishwa:

* Kurekebisha bugs
* Kutoa mapendekezo ya features mpya
* Kutafsiri kwa lugha za Kiafrika
* Kushiriki tafiti au data za kisheria

---

## 🛠️ Kuanzisha Project (Local Development)

1. `git clone https://github.com/username/jamiikazini.git`
2. `cd jamiikazini`
3. `python -m venv env`
4. `source env/bin/activate`
5. `pip install -r requirements.txt`
6. `python manage.py migrate`
7. `python manage.py runserver`

---

## 📄 Leseni

Mradi huu uko chini ya **MIT License**. Angalia faili la `LICENSE` kwa maelezo zaidi.

---

## ✨ Asante!

Tunaamini kwamba kwa kutumia teknolojia jumuishi, tunaweza kuunganisha watu, kuboresha maisha yao, na kujenga Afrika Mashariki iliyo tayari kwa mabadiliko ya kidijitali.
**Karibu Jamiikazini — Mahali pa Fursa kwa Kila Mtu.**

---

## 📁 Muundo wa Mradi

* Backend: Django + PostGIS (inaweza kukimbia Termux)
* Frontend: Next.js + Tailwind (inaweza kukimbia GitHub Codespaces)

### Mahitaji ya Awali

**Backend (kwenye Termux):**

* Python 3.12+
* PostgreSQL 16 + PostGIS
* Virtualenv
* Django 5.x
* `.jamiienv_export.sh` na `.env` zimesetiwa

**Frontend (kwenye Codespaces):**

* Node.js 20+
* Yarn/npm
* Next.js 14+
* TailwindCSS

### Kuanzisha Frontend:

1. `git clone https://github.com/jamiikazini/jamiikazini-pro.git`
2. `cd jamiikazini-pro/frontend`
3. `cp .env.local.example .env.local`
4. Weka `API_BASE_URL` yako kwa backend ya Termux
5. `npm install`
6. `npm run dev`

---

## 📂 Muundo wa Mafaili

jamiikazini/
├── jamiikazini/       → Django main project settings & URLs
│  ├── settings/      → base, dev, prod settings
│  └── utils/         → domain-based routing logic
├── accounts/          → Usimamizi wa watumiaji na roles
├── kiini/             → Core logic ya taasisi (middleware, context)
├── institutions/      → Usimamizi wa mashule, hospitali, n.k
├── education/         → Elimu
├── health/            → Afya
├── businesses/        → Biashara na huduma zake
├── logistics/         → Usafirishaji na deliveries
├── payments/          → Malipo na API zake
├── jamiiwallet/       → Wallet & Transactions
├── jamiichat/         → Chat ya papo kwa papo
├── jamiitasks/        → Celery tasks & background jobs
├── search/            → Smart search kwa huduma/bidhaa
├── security/          → Usalama (2FA, roles, audit logs)
├── syllabus/          → Elimu ya baadaye (under dev)
├── templates/         → HTML templates
├── locale/            → Faili za tafsiri za lugha
├── frontend/
├── start\_jamiikazini.sh
├── manage.py
└── requirements.txt
