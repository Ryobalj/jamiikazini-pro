# Jamiichat App (`jamiichat/`)

## Malengo
- Kuwezesha mawasiliano kati ya watoa huduma *(businesses, institutions, transporters)* na wateja.  
- Kusaidia mijadala ya **support**, maulizo ya bidhaa/huduma, na majadiliano ya jumla.  
- Kuwezesha **messaging** ya moja kwa moja *(1-1)* na ya kikundi *(group chats)*.  
- Kutumia **WebSocket** kwa *real-time chat* kupitia **Django Channels**.  

---

## Modular Structure
Kila module itakuwa na:  
- **Model**  
- **Serializer**  
- **View**  
- **URL update**  
- **Tests**  

---

## Checklist ya Hatua (kwa kila module)

### 1. Conversation Module
- [ ] `models/conversation.py`  
- [ ] `serializers/conversation_serializer.py`  
- [ ] `views/conversation_view.py`  
- [ ] Update `urls.py`  

### 2. Message Module
- [ ] `models/message.py`  
- [ ] `serializers/message_serializer.py`  
- [ ] `views/message_view.py`  
- [ ] Update `urls.py`  

### 3. Group Chat Module *(optional but powerful)*
- [ ] `models/group_chat.py`  
- [ ] `serializers/group_chat_serializer.py`  
- [ ] `views/group_chat_view.py`  
- [ ] Update `urls.py`  

### 4. Participant Module
- [ ] `models/participant.py`  
- [ ] `serializers/participant_serializer.py`  
- [ ] `views/participant_view.py`  
- [ ] Update `urls.py`  

---

## Vitu vya Jumla vya Mwisho
- [ ] `consumers.py` — WebSocket handling kupitia **Django Channels**  
- [ ] `routing.py` — channel routing  
- [ ] `permissions.py` — access kulingana na roles au institution  
- [ ] `admin.py` — kusajili models zote  
- [ ] **E2E Tests** za chat flow: kuanzisha conversation, kutuma message, kuona historia  
- [ ] Documentation ya kila endpoint na socket event  

---

## Notes
- **Real-Time Communication:** Django Channels + Redis kwa real-time messaging.  
- **Private Messaging:** 1-1 conversations kati ya user na user.  
- **Group Chats:** Institution au business inaweza kuanzisha group kwa mawasiliano na members.  
- **Security:** Message encryption *(optionally)*, JWT authentication kwa sockets.  
- **Standardization:** DRF pagination, filtering, searching, na permissions.  

---

## Jamiichat Integration Flow
1. **User starts conversation** — kupitia product, institution, au order.  
2. **Backend checks existing thread** — kama hakuna, inaumba conversation mpya.  
3. **WebSocket connects** — kupitia wss://chat.jamiikazini.com/ws/chat/{room_name}/
4. **Real-time messaging** — kupitia `consumers.py` kwa kutumia Django Channels.  
5. **Message stored** — kwenye `Message` model na kutangazwa kwa participants wengine.  
6. **Frontend updates** — UI inasasishwa mara moja kupitia WebSocket.  
7. **Notifications sent** — push/email/in-app *(optional)*.  

---

## Final Note
**Jamiichat** 
inaleta msingi wa mawasiliano ya haraka, salama, na yenye ufanisi
kati ya watoa huduma na wateja — ikijenga **uaminifu**, kutoa **msaada wa haraka**, 
na kuhakikisha **huduma bora** ndani ya mfumo mzima wa **Jamiikazini**.  

---

## Folder Structure (Suggested)

jamiichat/
├── models/
│   ├── __init__.py
│   ├── conversation.py
│   ├── message.py
│   ├── group_chat.py
│   ├── participant.py
├── serializers/
│   ├── __init__.py
│   ├── conversation_serializer.py
│   ├── message_serializer.py
│   ├── group_chat_serializer.py
│   ├── participant_serializer.py
├── views/
│   ├── __init__.py
│   ├── conversation_view.py
│   ├── message_view.py
│   ├── group_chat_view.py
│   ├── participant_view.py
├── consumers.py
├── routing.py
├── urls.py
├── permissions.py
├── admin.py
├── apps.py
├── tests.py
├── __init__.py

