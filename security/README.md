# App: security

App ya `security` katika mfumo wa *Jamiikazini* inalenga kuhakikisha usalama wa 
data, uthibitishaji wa watumiaji, faragha, uthabiti wa mifumo dhidi ya 
mashambulizi ya mtandao, na ufuatiliaji wa shughuli zote muhimu kwa mujibu wa 
viwango vya kimataifa kama vile GDPR. App hii imeundwa kwa namna ambayo inaweza
kutumiwa na apps nyingine kama `accounts`, `jamiiwallet`, `payments`, n.k 
kupitia huduma ya shared authentication, RBAC, encryption, audit logging, na 2FA.

---

## Malengo ya App

- Kusimamia uthibitishaji na ruhusa (authentication & authorization) kwa apps zote
- Kuweka usalama wa miamala na data kwa kutumia encryption
- Kuimarisha ufuatiliaji wa shughuli, na kutuma tahadhari pale kunapotokea tukio lisilo la kawaida
- Kuwezesha uthibitisho wa hatua nyingi (2FA) kwa watumiaji wa ngazi ya juu
- Kuhakikisha mfumo unafuata sheria za ulinzi wa data kitaifa na kimataifa
- Kutoa API endpoints zinazoweza kutumiwa na apps zingine kwa ajili ya authentication na security

---

## Mahitaji Muhimu ya Kiufundi

### Uthibitishaji na Ruhusa

- JWT authentication with rotating refresh tokens (shared via central service)
- IP rate limiting & throttling using `django-ratelimit` or `drf-extensions`
- Role-based Access Control (RBAC) ikitumia mfumo wa roles wa shared `accounts` app
- Two-Factor Authentication (2FA) kwa admin, institution_admin, na roles nyeti
- Shared authentication endpoints kwa apps kama `jamiiwallet`, `payments`, `accounts`

### Usimbaji wa Data

- HTTPS/TLS kwa mawasiliano yote (ikidhibitiwa kupitia nginx na certbot)
- AES encryption kwa data nyeti iliyohifadhiwa
- Argon2 hashing kwa passwords

### Usalama wa API

- CORS policies (kwa kupitia `django-cors-headers`)
- CSRF protection kwa endpoints za forms kupitia `csrf_exempt` control
- ReCAPTCHA kwa login, register, na maombi ya sensitive

### Usalama wa Miamala

- Secure payment gateway integration (kutoka app ya `payments`)
- OTP verification kwa miamala mikubwa
- Full audit trail kwa kila shughuli ya kifedha (ikihusiana na `payments` app)

### Ufuatiliaji na Tahadhari

- Activity logging: login/logout, export, transactions
- Real-time alerting kupitia Sentry/Splunk
- Audit trail kwa admin actions & changes kwenye taasisi

### Ulinganifu na Faragha

- GDPR compliance & local laws (e.g. TCRA)
- Data retention policies & anonymization (ikitekelezwa kwa models nyeti)
- Logging ya actions zote za admin

### Usalama wa Miundombinu

- Fail2Ban kwa kukata IP zinazojaribu mashambulizi ya nguvu (brute force)
- SSH-only access kwenye servers
- CI/CD hardening: token encryption, image scanning, automatic patching
- Encrypted, redundant backups using PostgreSQL + GPG + remote S3 bucket

### Ulinzi wa Kawaida

- Penetration testing kila robo mwaka (manual + automated via OWASP ZAP)
- Tools: Bandit, safety, django-secure kwenye CI/CD pipeline

---

## Milestones na Checklist ya Utekelezaji

# Security App – Production-Grade Task Checklist

App ya `security` inatakiwa kutoa ulinzi wa kiwango cha juu kwa mfumo wa Jamiikazini. Hapa ni task checklist kamili:

---

## 1. Authentication & Authorization

- [x] JWT authentication na rotating refresh tokens
- [x] Login/Logout endpoints (`UnifiedLoginView`, `LogoutView`)
- [x] IP-based rate limiting & throttling (`JamiiThrottle`)
- [x] CSRF protection kwa web forms
- [x] Role-Based Access Control (RBAC) middleware/decorators
- [x] Two-Factor Authentication (2FA) via TOTP (Google Authenticator)
- [ ] 2FA via SMS & Email OTP (high-value transactions)
- [ ] Conditional 2FA enforcement: 
  - Payments > X amount
  - Admin/institution_admin actions
- [x] ReCAPTCHA v3 integration kwa login, register, sensitive actions
- [ ] Login alerting: multiple failed attempts, unusual IP/device

---

## 2. Data Security & Encryption

- [x] HTTPS/TLS enforcement (certbot/nginx)
- [x] AES encryption kwa sensitive fields
- [x] Argon2 hashing kwa passwords
- [x] CORS policies kwa API endpoints
- [x] Encryption helper utilities reusable across apps
- [ ] Field-level encryption for sensitive payments data
- [ ] Secrets management for keys & tokens (env vars / vault)

---

## 3. Audit Logging & Monitoring

- [x] BaseLoginLogger – logs success & failure attempts
- [x] LoginHistory API & pagination (`LoginHistoryView`)
- [ ] Full audit trail:
  - Payments transactions
  - Wallet top-up/withdrawals
  - Admin actions on institutions/businesses
- [ ] Real-time alerting (Sentry/Splunk):
  - Failed login bursts
  - Suspicious payment behavior
  - Failed 2FA attempts
- [ ] Dashboard for monitoring audit events

---

## 4. Payment Security

- [ ] OTP verification for high-value payments/withdrawals
- [ ] Webhook signature verification for all gateways (PawaPay, Card, Bank)
- [ ] Idempotency checks for all payment-related webhooks
- [ ] Rate limiting per endpoint & per transaction
- [ ] Reconciliation logic:
  - Payments ↔ Wallet ↔ Ledger
  - Audit trail consistency

---

## 5. Infrastructure & CI/CD Security

- [ ] Fail2Ban configuration for SSH/login endpoints
- [ ] SSH-only access on servers
- [ ] CI/CD hardening:
  - Token encryption
  - Image scanning
  - Automated patching
- [ ] Backup strategy:
  - Encrypted
  - Redundant (PostgreSQL + remote S3)
  - Regular testing of restore

---

## 6. Compliance & Legal

- [ ] GDPR compliance:
  - Data anonymization
  - Right to access/delete
- [ ] Local law compliance (TCRA/TRA)
- [ ] Data retention policies
- [ ] Secure PDF receipts with TIN/control numbers

---

## 7. Penetration Testing & Security Tools

- [ ] Automated tests:
  - Bandit
  - Safety
  - django-secure
- [ ] OWASP ZAP / automated pen-testing
- [ ] Manual penetration testing (quarterly)
- [ ] Incident response plan & logging of incidents
- [ ] Security documentation for developers & operators

---

## 8. Testing & Quality Assurance

- [x] Unit tests for authentication, 2FA, encryption
- [ ] Integration tests for:
  - Payment flows
  - Wallet ↔ Payment interactions
- [ ] End-to-end tests for high-value transactions & alerts
- [ ] Test all recovery/failover scenarios (rate limits, failed OTPs)

---

## 9. Documentation & Developer Guidelines

- [ ] Security guidelines for internal developers
- [ ] How to add new endpoints with correct RBAC & 2FA
- [ ] How to add new payment gateway with signature verification
- [ ] Logging & alerting procedures for ops team

---

### 🔑 Notes:

- Tasks marked `[x]` = implemented in current app.
- Tasks marked `[ ]` = pending / need implementation.
- Focus initially: **Payments + 2FA + Audit + Alerts**, then **Infrastructure & Compliance**.
---

## Ratiba ya Utekelezaji (Timeline)

| Wiki | Hatua/Milestone                         | Maelezo                                            |
|-------|---------------------------------------|----------------------------------------------------|
| 1-2   | Milestone 1: Uthibitishaji na JWT     | Sanidi JWT, API za login/logout/token, rate limit  |
| 3-4   | Milestone 2: Ruhusa na 2FA            | RBAC, middleware, 2FA kwa watumiaji wa ngazi ya juu|
| 5-6   | Milestone 3: Usimbaji na Usalama Data | HTTPS, encryption, CSRF, CORS, ReCAPTCHA           |
| 7-8   | Milestone 4: Ufuatiliaji na Tahadhari | Audit logs, alerting, middleware za audit          |
| 9-10  | Milestone 5: Usalama wa Miundombinu   | Fail2Ban, SSH, CI/CD, backups, dokumenti           |
| 11-12 | Milestone 6: Penetration Testing       | Pen testing, security tools, incident plan         |

---

## Muundo wa Folda

```plaintext
security/
├── __init__.py
├── apps.py
├── authentication/
│   ├── __init__.py
│   ├── tokens.py
│   ├── throttling.py
│   └── 2fa.py
├── encryption/
│   ├── __init__.py
│   └── aes.py
├── audit/
│   ├── __init__.py
│   ├── middleware.py
│   ├── loggers.py
│   └── alerts.py
├── compliance/
│   ├── __init__.py
│   └── policies.py
├── shared/
│   ├── __init__.py
│   ├── endpoints.py  # API endpoints used by other apps
│   └── permissions.py
├── serializers/
│   └── activity_log.py
├── views/
│   └── auth_logs.py
├── urls.py
└── tests/
    ├── __init__.py
    ├── test_tokens.py
    ├── test_2fa.py
    ├── test_audit.py
    └── test_compliance.py