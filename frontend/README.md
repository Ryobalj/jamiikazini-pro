# frontend/README.md

rsync -av --exclude 'node_modules' /storage/emulated/0/Movies/jamiikazini-pro/frontend/ ~/frontend/


# 🌍 Jamiikazini-Pro Frontend (React → Next.js Ready)

## 📌 Dhima ya Mradi

Huu ni mradi wa frontend wa mfumo wa **Jamiikazini-Pro** — jukwaa la kidijitali 
kwa ajili ya taasisi, biashara, mafundi na wananchi wa Afrika Mashariki.  
Frontend hii imeundwa kwa kutumia **React + Tailwind CSS**, kwa kuzingatia 
muundo wa kipekee unaofanana na Acode App:  

- 📂 Sidebar yenye navigation ya apps zote  
- 🖥️ Main content panel inayobadilika kwa route  
- 🌘 Dark mode na usability nyepesi  

> Lengo kuu ni kutoa UI iliyo safi, nyepesi na scalable — **tayari kabisa kwa 
kuhamia Next.js bila mabadiliko makubwa.**

---

## 🚧 Maendeleo kwa Njia ya Next.js-Ready Structure

Frontend hii haitumii `create-react-app` bali **Vite**, ambayo ni nyepesi na 
inaruhusu migration rahisi.  
Tunafuata mbinu zifuatazo:

- `src/pages/` badala ya routes ndani ya App.js
- Hakuna `index.html` yenye logic nzito — meta tag zitawekwa kupitia Helmet 
(tayari kwa SSR)
- Hakuna `react-router-dom` complex hooks — routing ni rahisi, route-level
- Asset ziko ndani ya `/public/` kama ilivyo Next.js
- State management ni local/component-based, si redux nzito (ili migration 
iwe smooth)


# Jamiikazini Brand Identity

Jamiikazini-Pro inafuata utambulisho wa rangi na fonti zifuatazo ili kudumisha umoja wa mwonekano kwenye bidhaa zake zote.

## 🎨 Rangi Rasmi

| Rangi             | Hex      | Maana                              |
|-------------------|----------|-------------------------------------|
| 🌿 Nyasi Kijani    | #2E7D32  | Ukuaji, maendeleo, matumaini       |
| 🌊 Bahari Bluu     | #1976D2  | Uwazi, kuaminika, teknolojia       |
| 🔥 Chungwa Moto    | #F57C00  | Nguvu za jamii, ujasiriamali       |
| ⚪ Nyeupe           | #FFFFFF  | Uadilifu, usafi, uwazi            |
| 🪨 Makaa Kijivu    | #424242  | Msingi wa uthabiti, maandiko      |

## 🅰️ Fonti Rasmi

Sans-serif fonti: **Poppins**, **Roboto**, **Inter**

## ℹ️ Maelezo

Rangi na fonti hizi zinatakiwa zitumike katika:
- Tovuti na apps zote za Jamiikazini
- Vifaa vya marketing na documentation
- Muundo wa Tailwind au SCSS

> "Build the infrastructure of opportunity — digitally."

---

## ✅ Milestone ya Maendeleo

### 🧱 Msingi wa Frontend
- [x] Sanidi React App kwa Vite
- [x] Sanidi Tailwind CSS
- [x] Ongeza light/dark mode switch # "imewekwa lakini haibadili"
- [x] Tengeneza Sidebar (navigation ya apps)
- [x] Tengeneza TopBar (profile, search)
- [x] Tengeneza AppLayout.jsx (wrapper ya layout)

### 🗂️ Pages & Content
- [ ] index.jsx (Dashboard)
- [ ] education.jsx
- [ ] payments.jsx
- [ ] health.jsx
- [ ] settings.jsx
- [ ] 404.jsx

### 🔌 API & Services
- [ ] Sanidi `services/api.js` kwa fetch/axios
- [ ] Ongeza mfano wa API call kwenye page moja
- [ ] Weka `.env` ya API_URL configurable

---



## 🎯 Milestone 1: User Context & Menu Infrastructure
**Lengo:** Kujenga msingi wa menyu unaotumia `AppContext` kupata menyu sahihi kulingana na role, app, na access ya mtumiaji.

### ✅ Tasks
- [x] Unda `AppContext` (React Context).
- [x] Fafanua `AppContextProvider`:
    - [x] Kutunza `user`, `user.roles`, `user.institution`.
    - [x] Kutunza `user.institution.domain`.
- [x] Endpoint Backend:
    - [x] `GET /api/auth/me` (user data).
    - [x] `GET /api/auth/menu` (menu data).
- [x] Menu Configuration:
    - [x] Andika schema ya menyu (`menu.config.js`) kwa apps:
        - `business`
        - `institution`
        - `user`
        - `service`
        - `portifolio`
    - [x] Weka icons, labels, urls, role-based visibility.
- [x] Badilisha `Sidebar.jsx`:
    - [x] Kutumia `AppContext` + `userMenu`.
    - [x] Dynamic menu rendering.
- [ ] Testing:
    - [ ] Unit/integration test (`AppContext`, Endpoints, Sidebar).
- [ ] Documentation:
    - [x] `README` ya AppContext.
    - [ ] Role & permission mapping.
- [ ] Done:
    - [ ] QA review.
    - [ ] PR review & merge.

---

## 🔐 Milestone 2: Authentication & Session Hardening
**Lengo:** Kuimarisha usalama wa mtumiaji, kudhibiti 2FA, roles, na session.

### ✅ Tasks
- [ ] Integrate `2FA` (`user.get_2fa_secret()` + verify).
- [ ] Implement MFA setup & recovery.
- [x] Session expiry & auto-logout.
- [ ] Test `user.roles` mapping.
- [ ] Admin settings for role assignment.
- [ ] Endpoints for role & permission management.

---

## 🛍️ Milestone 3: Business & Service Contextual Menus
**Lengo:** Kutengeneza menyu za kiutendaji kwa Business/Service roles.

### ✅ Tasks
- [ ] Kutengeneza `business/menu.config.js`.
- [ ] Kutengeneza `service/menu.config.js`.
- [ ] Endpoint `GET /api/auth/menu` irudishe menyu sahihi.
- [ ] Kutumia `AppContext` kudhibiti rendering.

---

## 🏢 Milestone 4: Institution Contextual Menus
**Lengo:** Kutengeneza menyu kwa Institution Admin & Users.

### ✅ Tasks
- [ ] Kutengeneza `institution/menu.config.js`.
- [ ] Endpoint `GET /api/auth/menu` kurudisha menyu sahihi.
- [ ] Testing na role tofauti.

---

## 🌐 Milestone 5: Public Portifolio & Landing Pages
**Lengo:** Kutengeneza menu & layout kwa portifolio na public view.

### ✅ Tasks
- [ ] Kutengeneza `portifolio/menu.config.js`.
- [ ] Endpoint `GET /api/auth/menu` kurudisha public menu.
- [ ] Kutengeneza Landing pages & links.

---

## 🐞 Milestone 6: Testing, Optimization & Final QA
**Lengo:** Kuhakikisha kila menu, role & context vinafanya kazi inavyotakiwa.

### ✅ Tasks
- [ ] Final review ya `AppContext`.
- [ ] Final review ya menu generation.
- [ ] Testing:
    - [ ] User roles.
    - [ ] Institution roles.
    - [ ] Business roles.
    - [ ] Service roles.
- [ ] Optimization:
    - [ ] Caching menu results.
    - [ ] Lazy loading.
- [ ] Final QA & Documentation:
    - [ ] `README`.
    - [ ] Architecture Diagram.
    - [ ] User Guide.

---

**👊 Done:**  
- [ ] All Milestones Checked & Deployed.  
- [ ] PR Final Merge.  
- [ ] Announcement & Demo.


## 🔄 Next.js Migration Checklist (Baada ya MVP)

| Kipengele           | Tayari? | Maelezo |
|----------------------|---------|---------|
| `pages/` routing     | ✅      | Tayari kwenye `src/pages/` |
| Layout component     | ✅      | Tayari AppLayout wrapper |
| Tailwind setup       | ✅      | Fully compatible |
| `public/` assets     | ✅      | Hakuna kubadilisha structure |
| Meta tags            | ⚠️      | Helmet inatumika badala ya `<head>` |
| API consumption      | ✅      | Axios/fetch based |
| Routing logic        | ✅      | Route-level, rahisi kuhamia Next.js |
| SSR compatibility    | ✅      | No browser-only logic |

---

## 📁 Muundo wa Folda

```bash
frontend/
├── public/                 # Static assets (favicon, images, etc)
├── src/
│   ├── components/         # Sidebar, Topbar, Layout, etc.
│   ├── pages/              # index.jsx, education.jsx, etc. (Next.js ready)
│   ├── services/           # api.js - base URL and request helpers
│   ├── styles/             # globals.css, tailwind.css
│   ├── App.jsx             # Main app wrapper
│   └── main.jsx            # Entry point
├── tailwind.config.js
├── postcss.config.js
├── vite.config.js
├── package.json
└── README.md               # (hii hapa)
```

## 📁 Muundo wa Backend Dashboard
```
jamiikazini/
├─ accounts/
│  └─ views/
├─ businesses/
│  └─ views/
│     └─ dashboards.py           # Dashboard endpoints for businesses
├─ education/
│  └─ views/
│     └─ dashboards.py           # Dashboard endpoints for education
├─ health/
│  └─ views/
│     └─ dashboards.py           # Dashboard endpoints for health
├─ logistics/
│  └─ views/
│     └─ dashboards.py
├─ kiini/
│  └─ views/
│     └─ dashboards.py
├─ payments/
│  └─ views/
│     └─ dashboards.py
├─ jamiichat/
│  └─ views/
│     └─ dashboards.py
├─ ...

```

## 📁 Muundo wa Frontend Dashboard
```
src/
│
├── App.jsx
├── main.jsx
├── context/
│   └── AppContext.jsx
│
├── lib/
│   └── axios.js
│
├── components/
│   ├── Sidebar.jsx
│   ├── TopBar.jsx
│   └── AppLayout.jsx
│   ├── InputField.jsx
│   ├── SelectInput.jsx
│   └── LocationPicker.jsx
│
├── pages/
│   └── auth/
│       ├── Login.jsx
│       ├── Register.jsx
│       └── VerifyEmail.jsx
│
├── app/
│   ├── businesses/
│   │   ├── pages/
│   │   │   └── BusinessRegistrationPage.jsx
│   │   └── components/
│   │       ├── StageOneBasicInfo.jsx
│   │       ├── StageTwoInstitutionSelectOrCreate.jsx
│   │       ├── StageThreeSelectCategory.jsx
│   │       ├── StageFourLocationPicker.jsx
│   │       └── StageFiveReviewSubmit.jsx

```
