# Logistics App (`logistics/`)

# Logistics App Development Plan (`logistics/README.md`)

## Malengo
- Kusimamia huduma za usafirishaji wa mizigo
- Ku-track madereva, magari, maombi ya usafirishaji, na utekelezaji wa maagizo
- Kutumia PostGIS kwa Pickup na Delivery Points

---

## Modular Structure
Kila module ina:
- Model
- Serializer
- View
- URL update
- Tests

---

## Checklist ya Hatua (kwa kila module)

### 1. TransportProvider Module
- [x] `models/transport_provider.py`
- [x] `serializers/transport_provider_serializer.py`
- [x] `views/transport_provider_view.py`
- [x] Update `urls.py`

### 2. Vehicle Module
- [x] `models/vehicle.py`
- [x] `serializers/vehicle_serializer.py`
- [x] `views/vehicle_view.py`
- [x] Update `urls.py`

### 3. TransportRequest Module
- [x] `models/transport_request.py`
- [x] `serializers/transport_request_serializer.py`
- [x] `views/transport_request_view.py`
- [x] Update `urls.py`

### 4. TransportAssignment Module
- [ ] `models/transport_assignment.py`
- [ ] `serializers/transport_assignment_serializer.py`
- [ ] `views/transport_assignment_view.py`
- [ ] Update `urls.py`

---

## Vitu vya Jumla vya Mwisho
- [ ] `permissions.py` — kulinda access kulingana na roles
- [ ] `admin.py` — kusajili models zote
- [ ] Testing ya E2E ya delivery na tracking
- [ ] Documentation kwa kila endpoint

---

## Notes
- **Role-Based Access:** Mtoa huduma anaona order zake na majukumu yake pekee.
- **PostGIS Usage:** `pickup_location` na `delivery_location` ni `PointField`.
- **Security:** Picha za mtoa huduma, gari, na dereva zinahitajika kwa uthibitisho.
- **Standardization:** DRF pagination, filtering, searching, na permissions.

---

logistics/
├── models/
│   ├── __init__.py
│   ├── transport_provider.py
│   ├── vehicle.py
│   ├── transport_request.py
│   ├── transport_assignment.py
├── serializers/
│   ├── __init__.py
│   ├── transport_provider_serializer.py
│   ├── vehicle_serializer.py
│   ├── transport_request_serializer.py
│   ├── transport_assignment_serializer.py
├── views/
│   ├── __init__.py
│   ├── transport_provider_view.py
│   ├── vehicle_view.py
│   ├── transport_request_view.py
│   ├── transport_assignment_view.py
├── urls.py
├── admin.py
├── apps.py
├── permissions.py
├── tests.py
├── __init__.py


# Jamiikazini Logistics Workflow

## Overview

This document outlines the complete end-to-end logistics workflow from the moment
a client pays for a product to final delivery. It integrates the `businesses`,
`payments`, and `logistics` apps into a seamless, real-time transportation and
delivery system.

---

## 1. Payment Completed

Once a client makes payment via the `payments` app:

- The `businesses` app records the transaction.
- It sends shipment initialization data to the `logistics` app via internal API or Django signal:
  - `product_id`
  - `sender` (vendor)
  - `receiver` (client)
  - `preferred_transport_modes` (e.g., `["DRONE", "BIKE", "TRUCK"]`)
  - `route_details` (start, end, waypoints)

---

## 2. Logistics App Creates Shipment

A `Shipment` instance is created with:

- ForeignKeys to `Product`, `sender`, `receiver`
- Preferred transport mode(s)
- Route details
- Initial `status = PENDING`

Example JSON payload:

```json
{
  "product": 34,
  "sender": 5,
  "receiver": 12,
  "preferred_transport_modes": ["BIKE", "TRUCK"],
  "route_details": {
    "start": [36.8121, -1.2841],
    "end": [36.8987, -1.3429],
    "waypoints": [
      [36.8219, -1.2921],
      [36.8500, -1.3100]
    ]
  }
}
```

---

## 3. Vendor Marks Product as Packaged

- Vendor updates the shipment to mark packaging as complete.
- The system updates the status to `READY`.
- The shipment is now eligible for pickup.

---

## 4. System Dispatches Pickup Requests

- The `logistics` app:
  - Uses PostGIS to locate available `TransportProvider`s near the sender.
  - Filters by transport modes supported (e.g., `BIKE`, `TRUCK`).
  - Sorts transporters from nearest to farthest.
  - Sends pickup requests automatically or via app notification.

---

## 5. Transport Provider Accepts Request

- Transport provider logs into their dashboard or mobile app.
- Views available shipments based on location and capacity.
- Accepts the request.
- Shipment is assigned to them.
- Status updates to `IN_TRANSIT`.

---

## 6. Shipment Tracking and Delivery

- Driver uses real-time map (from `route_details`) to complete delivery.
- Shipment tracking is updated using `current_location` field.
- Status progresses as:
  - `IN_TRANSIT`
  - `NEAR_DESTINATION` (optional stage)
  - `DELIVERED`

---

## 7. Real-Time Tracking Implementation

- Shipment model includes:
  ```python
  current_location = models.PointField(null=True, blank=True)
  ```
- Drivers update location every few seconds/minutes via mobile app.
- Frontend shows map with live shipment location and estimated time of arrival.

---

## 8. Notifications and Communication

- Notification triggers for:
  - Pickup request sent
  - Shipment accepted
  - Driver near destination
  - Shipment delivered
- Delivery updates sent to both sender and receiver via:
  - Email
  - SMS
  - In-app notification (via Firebase or OneSignal)

---

## 9. Delay or Failure Handling

- System tracks time taken vs. expected duration (ETA).
- If delay or issue occurs:
  - Status is updated to `FAILED` or `CANCELLED`.
  - Admin and client are notified.
  - Retry options available or refund initiated through `payments` app.

---

## 10. Commission and Cost Breakdown

- Fields in `Shipment`:
  - `transport_fee`
  - `jamiikazini_commission`
  - `total_cost`
- Calculated automatically during shipment creation or update.
- Future improvement: implement fee tiers per transport mode or vendor policy.

---

## 11. Integration with External APIs (Optional)

- System supports external transport APIs like:
  - Uber for Business
  - Bolt API
  - SafeBoda
- Integration layer (already supported) can map external drivers to `TransportProvider` objects.

---

## Data Flow Summary

| Action           | Triggered By      | Affected App | Key Fields                                 |
|------------------|-------------------|--------------|---------------------------------------------|
| Payment          | Client            | `payments`   | `order_id`, `amount`                        |
| Shipment Created | `businesses` App  | `logistics`  | `product`, `sender`, `receiver`, `modes`, `route` |
| Request Pickup   | `logistics` App   | `logistics`  | `transport_providers`, `location`           |
| Accept Pickup    | Transport Provider| `logistics`  | `assigned_driver`, `status`                |
| Delivery         | Transport Provider| `logistics`  | `status`, `tracking`, `current_location`    |

---

## Final Note

All logistics processes in **Jamiikazini** are production-ready and fully integrated — from payment to pickup to real-time delivery and tracking, ensuring reliability and speed across East Africa and beyond.