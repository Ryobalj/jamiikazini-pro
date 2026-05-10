# JamiiWallet App (`jamiiwallet/`)

Mfumo wa kifedha wa ndani kwa ajili ya kufanya miamala ya kifedha salama, 
ya haraka, na bila ada. JamiiWallet inalenga kuwezesha top-up, withdrawals, 
transfers, malipo, refunds, na kuandaa mazingira ya kuunganishwa na benki
au mitandao ya simu kama PawaPay.

---

## Lengo Kuu

Kujenga mfumo wa ndani wa kifedha unaounga mkono miamala ya fedha kati ya wateja
na watoa huduma, kwa usalama na maandalizi ya integrations.

---

## Malengo Mahususi

- Kurahisisha miamala bila ada
- Kuweka na kufuatilia salio la kila mtumiaji
- Kuwezesha huduma za:
  - **Top-up**
  - **Withdrawals**
  - **Transfers**
  - **Payments**
  - **Refunds**
- Kuhifadhi historia ya miamala na kutoa risiti
- Kujiandaa kuunganishwa na **mobile money** au **benki**

---

## Muundo wa Mfumo

Mfumo umegawanywa kwa modules zifuatazo:

- Wallet
- Transaction
- TopUp
- Withdrawal
- Transfer
- Payment & Refund

Kila module ina:
- `models/`
- `serializers/`
- `views/`
- `urls/`
- `tests/`

---

## Checklist ya Modules

### 1. Wallet
- [x] `models/wallet.py`
- [x] `serializers/wallet_serializer.py`
- [x] `views/wallet_view.py`
- [x] Update `urls.py`

### 2. Transaction
- [x] `models/transaction.py`
- [x] `serializers/transaction_serializer.py`
- [x] `views/transaction_view.py`
- [x] Update `urls.py`

### 3. TopUp
- [x] `models/topup.py`
- [x] `serializers/topup_serializer.py`
- [x] `views/topup_view.py`
- [x] Update `urls.py`

### 4. Withdrawal
- [x] `models/withdrawal.py`
- [x] `serializers/withdrawal_serializer.py`
- [x] `views/withdrawal_view.py`
- [x] Update `urls.py`

### 5. Transfer
- [x] `models/transfer.py`
- [x] `serializers/transfer_serializer.py`
- [x] `views/transfer_view.py`
- [x] Update `urls.py`

### 6. Payments & Refunds
- [ ] Implement payment & refund as transaction types
- [ ] Add logic for reversals, receipts, and logs

---

## Milestones

### Milestone 1: Foundation
- [x] Create `jamiiwallet` app
- [x] Setup folders: `models/`, `serializers/`, `views/`, etc.
- [x] Register app in `INSTALLED_APPS`
- [x] Add `apps.py`, `signals.py`
- [x] Create `Wallet` model (OneToOne to `User`)
- [x] Auto-create wallet via signal
- [x] Register model in `admin.py`
- [x] Test wallet creation

### Milestone 2: Transactions Core
- [x] Create `Transaction` model
- [x] Use enum: `TOP_UP`, `WITHDRAWAL`, `TRANSFER`, `PAYMENT`, `REFUND`
- [x] Add metadata, receipts (JSON), timestamps
- [ ] Add validators and tests

### Milestone 3: Top-Up
- [x] `TopUp` model (amount, channel, status)
- [x] Serializer & View
- [x] Handle statuses (pending, completed, failed)
- [ ] Record in `Transaction`
- [x] Tests

### Milestone 4: Withdrawals
- [x] `Withdrawal` model (amount, OTP, channel, status)
- [ ] PIN/OTP validation
- [ ] Validate wallet balance
- [ ] Record transaction
- [ ] Tests

### Milestone 5: Transfers
- [x] `Transfer` model (sender, recipient, amount)
- [ ] Validate balance, PIN
- [x] Create credit/debit transactions
- [ ] Tests

### Milestone 6: Payments & Refunds
- [x] Add support in transaction model
- [x] Refund method with reason & amount
- [ ] Receipt + transaction reversal
- [ ] Tests

### Milestone 7: Security & Permissions
- [ ] `permissions.py` (e.g. `IsWalletOwner`)
- [ ] OTP for withdrawals, PIN for transfers
- [ ] Audit logging

### Milestone 8: Cleanup & Docs
- [ ] Finalize `signals.py` and `admin.py`
- [ ] Add API docs + README
- [ ] End-to-end tests

---

## Features Muhimu

- **Wallet ya mtumiaji mmoja mmoja** (`OneToOneField`)
- **Aina za Miamala**: `TOP_UP`, `WITHDRAWAL`, `TRANSFER`, `PAYMENT`, `REFUND`
- **Security**: OTP (withdrawals), PIN (transfers)
- **Receipts**: JSONField kwa kila muamala
- **Validation ya Balance**: Hakuna muamala bila salio la kutosha
- **Audit Trail**: Log kila hatua ya muamala

---

## Mafanikio Yanayotarajiwa

- Mfumo thabiti, salama, na wenye test coverage nzuri
- Hakuna muamala usio halali kupita
- Miundombinu tayari kwa integration na mobile money (PawaPay)
- All APIs documented

---

## Muundo wa Mafaili

```txt
jamiiwallet/
├── models/
│   ├── __init__.py
│   ├── wallet.py
│   ├── transaction.py
│   ├── topup.py
│   ├── withdrawal.py
│   ├── transfer.py
├── serializers/
│   ├── __init__.py
│   ├── wallet_serializer.py
│   ├── transaction_serializer.py
│   ├── topup_serializer.py
│   ├── withdrawal_serializer.py
│   ├── transfer_serializer.py
├── views/
│   ├── __init__.py
│   ├── wallet_view.py
│   ├── transaction_view.py
│   ├── topup_view.py
│   ├── withdrawal_view.py
│   ├── transfer_view.py
├── urls.py
├── admin.py
├── permissions.py
├── signals.py
├── tests.py
├── apps.py
├── __init__.py



# JamiiWallet Development Checklist

## 1. Models (Core Ledger Design)

* [x] `Transaction`: master ledger ya miamala yote
* [ ] `TopUp`: miamala ya kuweka pesa (initiate → transaction)
* [ ] `Withdrawal`: kutoa pesa (with PIN, approval logic)
* [ ] `Transfer`: user → user (check balance, validate PIN)
* [ ] `Payment`: malipo ya bidhaa au huduma
* [ ] `Refund`: kurejesha pesa (linked to failed `Payment`)
* [ ] `Wallet`: balance ya kila mtumiaji
* [ ] `TransactionLog`: audit trail, system-level logs

## 2. Serializers

* [ ] `TopUpSerializer`
* [ ] `WithdrawalSerializer`
* [ ] `TransferSerializer`
* [ ] `TransactionSerializer` (readonly)
* [ ] `WalletSerializer` (readonly)

## 3. Views

* [ ] `TopUpView`
* [ ] `WithdrawalView`
* [ ] `TransferView`
* [ ] `PaymentView`
* [ ] `RefundView`
* [ ] `TransactionListView`
* [ ] `WalletDetailView`

## 4. Permissions & Validation

* [ ] PIN validation before critical actions (withdraw, transfer)
* [ ] Balance check before withdraw/transfer
* [ ] Role-based permission check (e.g. allow `CLIENT` only)
* [ ] Ownership enforcement (e.g. can't view other user wallet)

## 5. Routing (URLs)

* [ ] `/wallet/` – GET wallet info
* [ ] `/wallet/topup/` – POST topup request
* [ ] `/wallet/withdraw/` – POST withdrawal request
* [ ] `/wallet/transfer/` – POST transfer to another user
* [ ] `/wallet/transactions/` – GET transaction history

## 6. Tasks – via `jamiitasks`

* [ ] `confirm_topup_transaction`
* [ ] `process_withdrawal`
* [ ] `send_transaction_receipt`
* [ ] `retry_failed_transaction`
* [ ] `notify_user_of_wallet_changes`

## 7. Signals & Hooks

* [ ] `post_save` on `TopUp` → trigger Celery confirmation
* [ ] `post_save` on `Transaction` → update related TopUp/Withdrawal status
* [ ] `post_save` on `Wallet` → optional notify user of balance change

## 8. Admin Interface

* [ ] Transaction inline view (readonly)
* [ ] Wallet management (view balances only)
* [ ] Refund approvals
* [ ] Withdrawal limits control

## 9. Tests

* [ ] Wallet balance calculation
* [ ] Successful topup → transaction recorded
* [ ] Withdrawal with wrong PIN → denied
* [ ] Transfer with low balance → denied
* [ ] Transaction log written every time

## 10. Security

* [ ] PIN encryption using hashing (not plain text)
* [ ] Role restrictions (e.g., no withdrawals by INSTITUTION\_ADMIN)
* [ ] Access control via DRF permissions
* [ ] Prevent duplicate topups via unique reference

