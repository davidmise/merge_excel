# OVERLAND TRACKING SYSTEM — REPORT MODULE: FULL PICTURE
> CodeIgniter System | Report Generation Implementation Plan
> Date: 2026-03-02 | Author: Engineering Team

---

## SYSTEM CONTEXT

Your existing CodeIgniter system already handles:
- Shipment CRUD (trucks, drivers, clients, cargo, routes)
- Milestone/checkpoint recording
- Daily location updates
- Border crossing timestamps
- Breakdown/incident logging
- Driver & vehicle management

**What's missing: Report Generation — this document covers the full plan.**

---

## REPORT CLASSIFICATION

### 🔴 EXTERNAL REPORTS (Client-Facing — requires client login role)
| # | Report Name | Audience | Frequency | Priority |
|---|-------------|----------|-----------|----------|
| 1 | **Client Tracking Report** | Clients (Glencore, Mercuria, BASH, etc.) | On-demand / Live | ⭐ START HERE |
| 2 | **Client Demurrage / Standing Report** | Clients | Monthly / On-demand | Phase 2 |
| 3 | **Client POD Report** | Clients | On-demand | Phase 2 |

### 🔵 INTERNAL REPORTS (Management — admin/ops login only)
| # | Report Name | Description | Frequency | Priority |
|---|-------------|-------------|-----------|----------|
| 4 | **NB & SB Tracking Report** | North Bound + South Bound full fleet tracker | Daily | Phase 2 |
| 5 | **Master Report** | God-view daily location grid (date columns) | Daily | Phase 2 |
| 6 | **Master In-Transit Report** | All currently moving shipments | Live/Daily | Phase 2 |
| 7 | **Border Report (Import)** | Trucks at each border — Import direction | Daily | Phase 3 |
| 8 | **Border Report (Export)** | Trucks at each border — Export direction | Daily | Phase 3 |
| 9 | **Offloading & Mines Report** | Trucks at mines + offload sites | Daily | Phase 3 |
| 10 | **Breakdown / Incident Report** | Fleet incidents by month | Monthly | Phase 3 |
| 11 | **Police Fine Report** | Daily fines tracker | Daily | Phase 3 |
| 12 | **POD Report (Master)** | Proof of delivery status (historic) | Monthly | Phase 3 |
| 13 | **Runner Report** | Active truck assignments + ETA | Daily | Phase 4 |
| 14 | **GPS Master Report** | GPS data overlaid on shipment status | Live | Phase 4 |
| 15 | **Offline Reports** | Trucks with no GPS/comms signal | Live | Phase 4 |
| 16 | **Demurrage / Standing Report (Internal)** | Full demurrage calculations all clients | Monthly | Phase 4 |

---

## IMPLEMENTATION PHASES

```
PHASE 1 (NOW)     → CLIENT REPORTS      [Visible to clients on login]
PHASE 2 (Next)    → CORE INTERNAL       [Daily ops team usage]
PHASE 3 (Month 2) → BORDER & FINANCIAL  [Management reporting]
PHASE 4 (Month 3) → LIVE & GPS REPORTS  [Real-time dashboards]
```

---

## PHASE 1 — CLIENT REPORT (START HERE)

### What the client sees when they log in:
```
┌─────────────────────────────────────────────────────────────┐
│  DASHBOARD: Glencore KCC                                    │
│  ─────────────────────────────────── Active Shipments: 34   │
│  [CLIENT TRACKING REPORT]  [DEMURRAGE REPORT]  [POD STATUS] │
│                                                             │
│  TRACKING REPORT — January 2026 — KCC (Import)             │
│  ┌──────┬──────────┬─────────┬────────────────┬──────────┐ │
│  │Truck │ Driver   │ Status  │ Current Loc.   │ ETA      │ │
│  │T320  │ JOHN DOE │ Enroute │ Tunduma B/O    │ 3 Days   │ │
│  └──────┴──────────┴─────────┴────────────────┴──────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Client Report has 3 sub-types:
1. **NB Client Report** — Import (Origin  → destination) per client
2. **SB Client Report** — Export (origin → Destinaion) per client
3. **Combined Client Report** — Both directions, all shipments

### Data columns included:
**Core (always visible):**
- Truck / Trailer / Driver / Contacts
- Product / Weight / BL / Lot No / Manifest
- Current Location + Status + Remarks
- Loading Date / Dispatch Date
- ETA to Next Checkpoint / ETA to Destination
- Total Days in Transit

**Border Milestones (date in / date out  borders shouldntbe fixed add crud to it so user can edit,create and delete borders on settings ):** 
- Origin → Tunduma → Nakonde → Kasumbalesa → Whiskey → Destination

**Computed:**
- Days at each checkpoint
- Border delay days
- Free days consumed / remaining
- Alert flag (if overdue)

---

## PHASE 2 — CORE INTERNAL REPORTS

### NB & SB Tracking Report
Same structure as client report but:
- Shows ALL clients on ONE sheet
- Includes cost/rate columns (hidden from clients)
- Includes clearing agent info
- Groups by client then by route

### Master Report (Time-Series Grid)
- Rows = Trucks
- Columns = Dates (rolling 60 days)
- Cell = Location text on that date
- Color-coded: Green=moving, Red=breakdown, Yellow=border, Gray=offloaded

### Master In-Transit Report
- Only trucks with status ≠ OFFLOADED and ≠ COMPLETED
- Live summary: how many at each checkpoint
- Grouped by Direction (NB/SB) and Client

---

## PHASE 3 — BORDER & FINANCIAL REPORTS

### Border Reports (Import / Export)
- Filter shipments where `current_checkpoint` = given border
- Show: days at border, reason for delay, ETA to clear

### Offloading & Mines Report
- Two sections: trucks at offloading warehouses (DAR/TANGA) + trucks at mine destinations
- Summary counts by client/mine

### Breakdown / Incident Report
- Monthly sheet per vehicle
- Problem type, location, days down, status (open/closed)
- KPIs: avg breakdown days, most common issues

### Police Fine Report
- Daily sheet per incident
- Split: driver account vs company account
- Monthly summary: total TZS, top offenders

### POD Report
- All offloaded shipments without received POD
- Days since offloaded (highlight > 30 days)
- Per-client grouping

---

## PHASE 4 — LIVE / GPS REPORTS

### Runner Report
- Real-time truck assignments
- Driver + current position + next checkpoint + ETA
- Refresh every hour

### GPS Master Report
- GPS coordinates mapped to named locations
- Last known position for all active trucks
- Offline detection (no ping > 12 hours)

### Offline Report
- Trucks with GPS silent > threshold
- Last known location, client, cargo

### Demurrage / Standing (Full Internal)
- All demurrage across all clients, all legs
- Chargeable days × rate = USD
- Aging report (30/60/90 days overdue)

---

## CODEIGNITER ARCHITECTURE REQUIRED

```
application/
├── controllers/
│   ├── reports/
│   │   ├── Client_report.php        ← Phase 1
│   │   ├── Master_report.php        ← Phase 2
│   │   ├── Border_report.php        ← Phase 3
│   │   ├── Breakdown_report.php     ← Phase 3
│   │   ├── Financial_report.php     ← Phase 3
│   │   └── Gps_report.php           ← Phase 4
├── models/
│   ├── reports/
│   │   ├── Report_model.php         ← Base query model
│   │   ├── Shipment_report_model.php
│   │   ├── Financial_report_model.php
│   │   └── Gps_report_model.php
├── views/
│   ├── reports/
│   │   ├── client/
│   │   │   ├── tracking.php         ← Client tracking report view
│   │   │   ├── demurrage.php
│   │   │   └── pod.php
│   │   ├── internal/
│   │   │   ├── master.php
│   │   │   ├── border.php
│   │   │   ├── breakdown.php
│   │   │   ├── police_fine.php
│   │   │   ├── pod_master.php
│   │   │   └── offloading_mines.php
│   │   └── partials/
│   │       ├── report_filters.php   ← Shared filter bar
│   │       ├── export_buttons.php   ← Excel/PDF/Print buttons
│   │       └── milestone_row.php    ← Shared checkpoint row
├── libraries/
│   ├── Report_exporter.php          ← Excel + PDF generation
│   └── Report_builder.php           ← Fluent query builder for reports
└── helpers/
    └── report_helper.php            ← Days calc, date format, color flags
```

---

## KEY DESIGN DECISIONS

### 1. Role-Based Report Access
```
client_role   → can only see their own data (client_id filtered automatically)
ops_role      → all internal reports, no financial
manager_role  → all reports including financial
admin_role    → everything + configuration
```

### 2. Excel Export
Use `PhpSpreadsheet` (via Composer in CI) for proper Excel formatting with:
- Merged header cells
- Color-coded status rows
- Auto-width columns
- Frozen header rows

### 3. PDF Export
Use `DOMPDF` or `mPDF` (CI library) for clean PDF rendering.

### 4. Report Caching
- Live data: no cache
- Historical reports (past months): cache for 1 hour
- Master report grid: cache for 15 min

### 5. Client Report URL Structure
```
/client/reports/tracking?direction=NB&date_from=2026-01-01&date_to=2026-01-31
/client/reports/tracking/export/excel
/client/reports/tracking/export/pdf
```

---

## START: CLIENT REPORT — MINIMUM VIABLE REPORT (MVR)

The absolute minimum to ship Phase 1:

1. **Auth gate:** Client login → filtered to their `client_id` only
2. **Query:** SELECT all shipments WHERE client_id = logged-in client AND date range
3. **Display:** HTML table with sortable columns + color-coded status
4. **Milestones:** Show border checkpoint dates in collapsible sub-row
5. **Export:** One "Export to Excel" button → downloads formatted `.xlsx`
6. **Filter:** Date range picker + Direction (NB/SB/Both) + Status filter

**Estimated time to MVR: 3-5 days of focused development**

---

## PRIORITY DECISION: WHY CLIENT REPORTS FIRST

1. **Client-visible = revenue-critical** — clients judge you by what they can see
2. **Simpler scope** — filtered by client, no fleet-wide complexity
3. **Forces good data architecture** — if client report works, internal reports are trivial extensions
4. **Immediate value** — you stop sending Excel files manually by email
5. **Security-first** — builds the ACL system everything else will use
