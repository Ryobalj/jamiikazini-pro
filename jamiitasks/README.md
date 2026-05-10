# jamiitasks

## 📌 Madhumuni ya App Hii

App ya `jamiitasks` ni ya kushughulikia kazi zote za nyuma ya pazia 
(background/async tasks) kwa mfumo wa jamiikazini.
Inatumia **Celery + Redis** kutekeleza majukumu haya kwa ufanisi, haraka, na
kupunguza mzigo kwenye requests za HTTP.

---

## 🎯 Malengo Mahususi

- Kutuma SMS, email, na push notifications.
- Kuhifadhi na kufuatilia transaction retries (payment/webhook tasks).
- Kutuma ujumbe wa chat bila kuchelewesha view za HTTP (`jamiichat`).
- Kuweka retry policies na logging ya makosa ya task.
- Kutoa services kwa apps nyingine kama `accounts`, `jamiiwallet`, `jamiichat`, `logistics`, n.k.


## 📦 Muundo wa App

---

jamiitasks/
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── tasks/
│   ├── __init__.py
│   ├── notifications.py     # SMS, email, push
│   ├── payments.py          # Transaction/webhook retries
│   ├── messaging.py         # Chat + system messages
│   └── cleanup.py           # Background maintenance tasks
├── services/
│   ├── __init__.py
│   ├── sms_gateway.py
│   ├── email_gateway.py
│   ├── push_gateway.py
│   └── payment_gateway.py
├── tests/
│   ├── __init__.py
│   ├── test_notifications.py
│   ├── test_payments.py
│   └── test_messaging.py
├── README.md
├── migrations/
│   └── __init__.py

---

## ✅ Checklist ya Task Muhimu

### 🔔 Notification Tasks
- [x] `send_sms_task(phone, message)`
- [x] `send_email_task(to_email, subject, body)`
- [x] `send_push_notification_task(user_id, message)`

### 💳 Payment/Transaction Tasks
- [x] `process_transaction_task(transaction_id)`
- [x] `retry_failed_transaction_task(transaction_id)`
- [x] `log_webhook_event_task(data)`

### 💬 Messaging Tasks
- [x] `send_chat_message_task(sender_id, recipient_id, message)`
- [x] `notify_user_of_new_message(user_id)`

### 🧹 Maintenance/Cleanup
- [x] `clear_old_sessions_task()`
- [x] `archive_old_messages_task()`

---

## 🔗 App Zinazotegemea `jamiitasks`

- `accounts` – kwa verification messages
- `jamiichat` – kwa ujumbe wa chat
- `jamiiwallet` – kwa transaction retries
- `logistics` – kwa status notifications
- `institutions` – kwa info updates

---

## 🛠️ Celery Configuration

Ensure `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` are set to Redis:

```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
