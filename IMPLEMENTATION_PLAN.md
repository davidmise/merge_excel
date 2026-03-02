# OVERLAND TRACKING REPORTS — DEEP ANALYSIS & IMPLEMENTATION PLAN

> Generated: 2026-03-02 | 28 Excel files analyzed | 586 sheets total

---

## PART 1: DEEP ANALYSIS OF EACH JSON/EXCEL REPORT

### 1. OVERLAND MAIN MASTER REPORT (580 rows, 74 columns)
**Purpose:** The "God-view" daily tracking log of the entire fleet. Each row = one truck. Each column after the fixed headers = one date. The cell value = the truck's location/status on that date.

**Fixed Columns (8):**
| # | Field | Description |
|---|-------|-------------|
| 1 | TRUCK OWNER | Company that owns the truck (e.g., MBARAKA) |
| 2 | S/NO | Sequential number |
| 3 | TRUCKS | Truck registration plate (e.g., T320CFY) |
| 4 | TRAILER 1 | Trailer registration(s) (e.g., T326BXG-T525EFH) |
| 5 | DRIVER NAME | Full name |
| 6 | TYPE | IMPORT / EXPORT |
| 7 | CLIENT | Client name (e.g., BASHI, G.T. OCEAN) |
| 8 | DESTINATION | Route string (e.g., TANGA/LIKASI, DAR/LIKASI) |

**Dynamic Columns (66):** Daily location snapshots with format `"20th January 2026; TIME: 1130HRS"`. Cell values are free-text locations like `"Konkola enroute to Shituru"`, `"Edha Yard"`, `"Tunduma day 4 enroute to shituru"`, `"Nakonde enroute to Likasi [b/DOWN]"`.

**Key Insight:** This is a **time-series location tracker**, not a structured milestone report. Breakdown (b/d) status is embedded in the text.

---

### 2. BASH TRACKING REPORT NORTH BOUND (18 rows, 42 columns)
**Purpose:** Client-specific (BASH/XIN DA SARL) structured tracking report with milestone dates + demurrage calculation.

**Core Fields:**
| Field | Type | Description |
|-------|------|-------------|
| Consignee Name | text | BASH client (XIN DA SARL) |
| B/L# | text | Bill of Lading number |
| Container no. | text | Product description |
| Gross Weight / Net | number | Weight in kg |
| No of Bags | number | Bag count |
| Truck # | text | Truck plate |
| Type (x2) | text | Truck type (DOUBLE DIFF, DENGLOUR) |
| Trailer # / Trailer II | text | Trailer plates |
| Current Location | text | Current position |
| STATUS | text | Enroute/Offloaded |
| DESTINATION | text | Final destination (LIKASI/SHITURU) |
| DRIVER NAME | text | Driver full name |
| CONTACTS | text | Phone number |
| D/LICENCE | number | Driver license number |
| ATB | date | ATB date |
| ALLOCATED DATE | date | When truck was allocated |
| DAR DISPATCH DATE | date | Dispatch from Dar |
| TANGA ARR DATE | date | Arrival at Tanga |
| Loading Date | date | Loaded date |
| DISPATCH TANGA | date | Dispatch from Tanga |
| DAYS (transit) | number | Days in transit Tanga leg |
| Tunduma Arrival | date | Tunduma border arrival |
| Nakonde Arrival / Depart | date | Nakonde border checkpoints |
| DAYS (border) | number | Border dwell days |
| K-Lesa ZMB Arrival | date | Kasumbalesa Zambia arrival |
| K-lesa DRC Arrival | date | Kasumbalesa DRC arrival |
| Whiskey Arrival / Dispatch | date | Whiskey border |
| Boarder Days | number | Total border days |
| Arrival at Site | date | Final destination arrival |
| Offloaded | date | Offload date |
| Days / Free days | number | Total days / free days |
| Chargeable Days / Rate | number | Demurrage chargeable days and rate |
| Demurrage Charges | USD | Calculated charges |
| Parking penalties | USD | Penalties if applicable |

---

### 3. KCC PO C003636963 TRACKING REPORT (34 rows, 37 columns)
**Purpose:** Glencore/KCC client-formatted Purchase Order tracking report. This is the **client's own template** format.

**Core Fields:**
| Field | Type |
|-------|------|
| TripCode / OrderNumber | identifiers (often empty — for client's internal use) |
| Bag Number (qty of bags) | number |
| Loaded Net/Gross Weight (In MT) | number |
| Invoice Number | text |
| Consignment Number (Manifest) | text |
| Supplier | text |
| Product | text (SULPHUR) |
| Origin Country / Destination Country | text |
| Corridor | text (Dar Es Salaam, Tanzania - DRC) |
| FXICode / Bv Code | client reference codes |
| Truck Reg / TrailerRegistration1 / TrailerRegistration2 | plates |
| Nominated Haulier | text (overland) |
| Drivers Name | text |
| DriverPassport | text |
| Current Location | dropdown (At Destination, In Transit, etc.) |
| Inbound Status | dropdown (Offloaded, In Transit, Loaded) |
| DCG Kisarawe arrival date | date |
| Loading Date | date |
| Origin Dispatch Date | date |
| Tunduma arrival/dispatch Date | date |
| Nakonde Dispatch Date | date |
| Last Update Date Position | date |
| Trip Duration in Days | number |
| Kasumbalesa Arrive/Dispatch date | date |
| Border delays Days | number |
| KCC Arrive date / KCC Offload Date | date |
| Offload delays Days | number |
| Clearing Agents | text (CONNEXAFRICA, DOUANE EXPRESS) |

**Has Background Info sheet:** Corridors, Legs, TripTypes, Days in Transit lookup data.

---

### 4. MUMI PO C003355377 TRACKING REPORT (4 sheets, 36 columns each)
**Purpose:** Identical format to KCC report but for MUMI mine destination. Sheets split by B/L number.

Same fields as KCC but destination-specific: `MUMI Arrive date`, `MUMI Offload Date`. Products: MGO. Corridor: Tanga, Tanzania - DRC.

---

### 5. GLENCORE EXPORTS UPDATE (19 sheets, 408+ rows per sheet)
**Purpose:** The **largest export tracking report**. Tracks copper exports from DRC mines to Dar/Tanga ports. One sheet per route (KCC-DAR, KCC-TANGA, MUTANDA-DAR, etc.)

**Core Fields (consistent across 19 sheets):**
| Field | Description |
|-------|-------------|
| SN# | Row number |
| Uplift | Mine name (KCC, MUTANDA, TFM, DEZIWA) |
| Offloading Point | Destination warehouse (DCG DAR, TAZARA, TANGA PORT) |
| Transporter | Always "OVERLAND" |
| Lot No | Export lot reference |
| Truck / Trailer I / Trailer II | Vehicle plates |
| Driver Name (First/Last) | Driver info |
| Passport | Driver passport |
| Loading Capacities | MT |
| Type | FLATBED, SIDELOADER |
| Current Location | text |
| REMARK | Status text |
| **Border Checkpoints (Arrival/Dispatch pairs):** | |
| Origins → Arrival/Loaded/Departure/Days | Loading site dates |
| WHISKY → Arrival/Dispatch | Whiskey border |
| KASUMBALESA/SAKANIA → Arrival/Dispatch | K-Lesa border |
| Nakonde border → Arrival/Dispatch | Nakonde |
| Tunduma border → Arrival/Dispatch | Tunduma |
| Final destination → Arrival/Offloaded/Days/Total delays | Offload dates |

---

### 6. NST DEZIWA-DAR TRACKING REPORT (11 sheets, ~30-56 rows each)
**Purpose:** Monthly tracking for Deziwa mine exports to Dar. Same "Overland Tracking Status report" template as Glencore exports — identical column structure.

Months: Feb, April, May, June, July, Aug, Sep, Oct, Nov, Dec, Jan 2026.

---

### 7. TRACKING REPORT - MERCURIA (January 2026) (2 sheets)
**Purpose:** Client-specific (Mercuria/TFM) tracking. Same export template format.

Fields: Uplift (TFM), Offloading Point (C-Steinweg Bridge WH TAZARA), PRODUCT (Copper Cathode).
Same border checkpoint structure.

---

### 8. TRACKING REPORT - MERCURIA (December) (2 sheets)
**Purpose:** Same as above for December period.

---

### 9. BRILLIANT--SOUTH BOUND KAMOA (3 sheets: KAMOA, LCS, KAMOA-2)
**Purpose:** Tracking southbound shipments to Kamoa mine area.

**KAMOA-2 sheet has structured milestone columns:**
| Field | Description |
|-------|-------------|
| Sn, S.O, Truck, TrailerI | Vehicle details |
| BlNumber, Container | Document references |
| Total Tons | Weight |
| DriverName, Passport | Driver info |
| LoadingMine, OffloadingWHDar | Locations |
| Current location, Status, ETA | Status info |
| Loading Date / Dispatch Date | dates |
| Kasumbalesa DRC/ZMB Arrival/Departure pairs | Border checkpoints |
| Nakonde ZMB Arrival/Departure | Border |
| Tunduma TZ Arrival/Departure | Border |
| Arrive on Site / Offload Date / Offload Site | Destination |
| POD sent to BRILLIANT | POD status |

---

### 10. TALANA NORTH BOUND TRACKING REPORT (2 sheets)
**Purpose:** Tracking northbound cargo to Deziwa Mine for Talana.

Fields: Truck, Trailer, Trailer II, Bol (Bill of Lading), Current Location, BAGS LOADED, Net/Gross/GVM weights, Driver Name, Passport, D/Licence, Route, Allocation Date, Arrive At Loading point, Loading, Dispatch Dar, Days, Border checkpoints (Tunduma/Nakonde/Kasumbalesa), Final destination arrival/offloaded, Transit days, Driver Contact.

---

### 11. BREAKDOWNS REPORT (5 sheets: Sep, Oct, Nov, Dec, Jan 2026)
**Purpose:** Monthly breakdown/incident tracking. ~150-230 rows per month.

**Fields:**
| Field | Description |
|-------|-------------|
| S/NO | Row number |
| TRUCK | Truck plate |
| TRAILER | Trailer plate(s) |
| DRIVER NAME | Full name |
| B/DOWN PLACE | Breakdown location (NDOLA, NAKONDE, etc.) |
| PROBLEM DIAGNOSED | Issue type (GEAR/CLUTCH, U-BOLT, STARTER, etc.) |
| INCHARGE | Person managing repair |
| B/DOWN DATE | Date breakdown occurred |
| B/D DATE END | Date breakdown resolved |
| DAYS AT B/DOWN | Duration (calculated) |
| CLIENT | Client name |
| STATUS | IMPORT/EXPORT + CLOSED/OPEN |

---

### 12. DEMURRAGE CHARGES ACCESS WORLD IMPORT (6 sheets per BL)
**Purpose:** Client-specific demurrage billing. Each sheet = one BL/shipment batch.

**Fields:**
| Field | Description |
|-------|-------------|
| Haulier Name | Overland |
| BL No. | Bill of Lading (where applicable) |
| Truck Registration / Trailer 1 / Trailer 2 | Plates |
| Current Location | Position |
| Remark | Status |
| K-lesa Arr Date | Kasumbalesa arrival |
| Whiskey Dispatch Date | Whiskey departure |
| Arrived-to-Dispatch Delays days | Calculated days |
| Destination Arr Date | Arrival at destination |
| Offloading Date | Offload date |
| Offloading Delays day | Calculated |
| Free Days | Agreed free days (7, 10) |
| Chargeable Demurrage Days | Calculated: Total - Free |
| Parking penalty | Amount USD |
| Rate | USD per day (250) |
| Total | Total charges USD |

---

### 13. GLENCORE-KCC COPPER TRUCKS DEMURRAGE CHARGES (1 sheet, 41 rows)
**Purpose:** Export-side demurrage for KCC copper cathode loading delays.

**Fields:**
| Field | Description |
|-------|-------------|
| Mine | KCC |
| Haulier Name | Overland |
| Truck Registration / Trailer 1 / Trailer 2 | Plates |
| Corridor | Route (DCG DAR) |
| Commodity | Copper cathodes |
| Export Lot | Reference |
| Current Location / Remark | Status |
| Date Reported For Loading | When truck arrived at mine |
| Loading Date | Actual load date |
| Dispatch Date | Dispatch date |
| Empty-to-Dispatch | Days calculated |
| Free Days | Allowed free days (13) |
| Chargeable Demurrage Days | Overage |
| Rate | USD per day (250) |
| Total | Charges USD |

---

### 14. POLICE FINE REPORT 2026 (290 sheets! — one per day)
**Purpose:** Daily police fine tracking. Each sheet = one calendar day.

**Fields:**
| Field | Description |
|-------|-------------|
| S/N | Sequence |
| PARTICULAR | Fine reason (DEFECTIVE TIRES, CONDITION OF MOTOR VEHICLE, etc.) |
| TRUCK | Truck plate |
| DRIVER NAME | Full name |
| SH/ORDER | Shipping order reference |
| ACCOUNT (DRIVER AC / COMPANY AC) | Who pays (split) |
| CONTROL NO | Payment control number |
| TZS | Fine amount in TZS |

---

### 15. POD (Proof of Delivery) ---2026 (3 sheets: Nov, Dec, Sites)
**Purpose:** Tracks POD document collection after offloading.

**Fields:**
| Field | Description |
|-------|-------------|
| SN / S/ORDER | Row number / Shipping order |
| TRUCK | Truck plate |
| DRIVER NAME | Full name |
| Loading Date | Load date |
| Offloading Date | Offload date |
| Days since offloaded | Calculated |
| Current location | Text |
| Transporter | OVERLAND |
| Loading point | Origin |
| Client | Client name |
| Destination | Route |
| Telephone | Driver phone |
| B/Lading | BL reference |
| Pod Status | RECEIVED / PENDING |
| Remark | COMPLETED etc. |

---

### 16. POD MASTER-16-01-2026 (26 sheets — monthly from 2024-2026)
**Purpose:** Historical master POD tracking — comprehensive going/return cargo log.

**Fields:**
| Field | Description |
|-------|-------------|
| Date | Date |
| Serial | S/N |
| Master Pod report | Truck plate |
| GOING CARGO | Outbound cargo client |
| GOING | Client name |
| Loading/Offloading dates | Dates |
| Return Cargo | Return cargo client/loading/offloading |
| POD STATUS | RECEIVED/PENDING/YES |
| Driver Name | Driver |
| Lot/BL | References |
| Destination | Location |

---

### 17. LOADING ORDER (17 sheets, 507+ rows per primary sheet)
**Purpose:** Comprehensive dispatch/loading order records.

**Primary Template (TANKRES--23) Fields:**
| Field | Description |
|-------|-------------|
| S.NO | Sequential |
| DATE LOADED | Loading date |
| SH/ORDER | Shipping order number |
| Truck REG # / Trailer REG # | Plates |
| DRIVER NAME | Full name |
| CLIENT | Client name |
| ITERMS | Product/items (PMS, etc.) |
| MOBILE | Phone number |
| PASSPORT | Passport |
| D/LICENCE | License number |
| LITRES | Volume (for tankers) |
| DESTINATION | Route |
| TYPE | Vehicle type (TANKER) |

**Extended Template (monthly sheets) adds:**
Allocated date, Loading date, Offloading date, Going Cargo, Return Cargo, Trip Days, Transporter, Loading point, File, Type, B/Lading, Items, Net, Gross, GVM, Agent, Return Client, Return Loading Point, Order Sent & Confirmed.

---

### 18. TUNDUMA BORDER REPORT (4 sheets)
**Purpose:** Snapshot of trucks at Tunduma border on a specific date.

**Fields:** S/N, TRUCK, LOCATION, GOING (IMPORT/EXPORT), DAYS (at border), REMARKS (B/DOWN, DRIVING LICENSE RENEW, etc.)

---

### 19. NDOLA EXPORT & IMPORT REPORT (1 sheet)
**Purpose:** Snapshot of trucks at Ndola yard.

**Fields:** Sl.No, Truck, Client, Location, Days, Ndola Arrived Date, Remarks.

---

### 20. EXPORT BORDERS REPORT (1 sheet, 74 rows)
**Purpose:** Similar to main master — daily location grid for export trucks specifically. Fewer usable columns, structured as a date-column pivot.

---

### 21. OFFLOADING & MINES SUMMARY REPORT (3 sheets)
**Purpose:** Summary of trucks at offloading sites and mines.

**Offloading DAR:** Truck, Client, Arrived at offloading Site, Days, Warehouse, Driver name, Phone number.
**Export Mines:** Truck No, Driver Name, Mine Name, Status, Days, Client.
**Summary Final:** Aggregated counts by category.

---

### 22. JOSE KSM (20 sheets) & WILLY KSM (190 sheets)
**Purpose:** Kasumbalesa border tracking per individual truck/driver. Each sheet = one truck's detailed border crossing log. Very high sheet-count personal trackers.

---

---

## PART 2: REPORT CATEGORIES

### CATEGORY A: ROUTE TRACKING REPORTS (Client-Specific)
> Same underlying data, different client template/filter/grouping

| Report | Client | Direction | Template Style |
|--------|--------|-----------|----------------|
| Glencore exports update (19 sheets) | Glencore (KCC/MUTANDA/TFM) | EXPORT (mine→port) | Overland Standard |
| NST DEZIWA-Dar Tracking (11 sheets) | NST/Deziwa | EXPORT | Overland Standard |
| Mercuria Tracking (Jan) | Mercuria/TFM | EXPORT | Overland Standard |
| Mercuria Tracking (Dec) | Mercuria/TFM | EXPORT | Overland Standard |
| BASH North Bound | BASH/XIN DA SARL | IMPORT (port→mine) | BASH Template |
| KCC PO Tracking | Glencore/KCC | IMPORT | Client KCC Template |
| MUMI PO Tracking | Glencore/MUMI | IMPORT | Client KCC Template |
| BRILLIANT South Bound Kamoa | Brilliant/Kamoa | IMPORT | Mixed |
| TALANA North Bound | Talana/Deziwa | IMPORT | Overland Standard |

**Shared Core Parameters (across ALL route tracking):**
- Truck Reg, Trailer(s), Driver Name, Driver Phone, Passport
- Client, Product/Commodity, Weight/Bags
- Origin, Destination, Corridor/Route
- Lot/BL/Invoice/Manifest references
- Border checkpoint dates: Loading → Tunduma → Nakonde → Kasumbalesa/Whiskey → Destination
- Current Location, Status, Remark
- Days calculations (transit, border, total)

---

### CATEGORY B: DAILY STATUS SNAPSHOTS
> Time-series location grid — each column is a date, each row is a truck

| Report | Scope |
|--------|-------|
| OVERLAND MAIN MASTER REPORT | Full fleet |
| EXPORT BORDERS REPORT | Export trucks only |

**Core Data:** Truck, Trailer, Driver, Client, Destination, Type + daily location string.

---

### CATEGORY C: BORDER/LOCATION POINT REPORTS
> Snapshots of trucks at specific border/yard at a point in time

| Report | Location |
|--------|----------|
| TUNDUMA BORDER REPORT | Tunduma border |
| NDOLA EXPORT & IMPORT REPORT | Ndola yard |
| OFFLOADING & MINES SUMMARY | DAR offload sites + DRC mines |
| JOSE KSM / WILLY KSM | Kasumbalesa border (per-truck detail) |

**Core Data:** Truck, Location, Days at location, Status/Remarks, Client.

---

### CATEGORY D: FINANCIAL/CHARGES REPORTS
> Demurrage and penalty calculations derived from tracking dates

| Report | Type |
|--------|------|
| Demurrage Charges Access World IMPORT | Import-side border delays |
| Glencore-KCC Copper Trucks Demurrage | Export-side mine loading delays |
| POLICE FINE REPORT 2026 | Traffic fines (290 daily sheets) |

**Core Data:** Truck, Trailer, Dates (arrival/dispatch), Delay days, Free days, Chargeable days, Rate, Total USD.

---

### CATEGORY E: OPERATIONAL / DOCUMENT TRACKING
> Loading orders, PODs, breakdowns

| Report | Purpose |
|--------|---------|
| LOADING ORDER | Dispatch planning and cargo assignment |
| POD ---2026 | Short-term POD collection tracking |
| POD Master | Long-term master POD history |
| BREAKDOWNS REPORT | Fleet maintenance/incident log |

---

---

## PART 3: DATA FIELD SIMILARITY MATRIX

### UNIVERSAL FIELDS (present in 90%+ of reports)
These fields exist in virtually every report and represent the **core shipment entity**:

```
┌─────────────────────────────────────────────────┐
│  TRUCK REGISTRATION    ← present in ALL reports │
│  TRAILER REGISTRATION  ← present in ALL reports │
│  DRIVER NAME           ← present in ALL reports │
│  CLIENT                ← present in ALL reports │
│  CURRENT LOCATION      ← present in ALL reports │
│  STATUS / REMARK       ← present in ALL reports │
└─────────────────────────────────────────────────┘
```

### HIGH-FREQUENCY FIELDS (present in 70%+ of reports)
```
┌─────────────────────────────────────────────────────┐
│  DESTINATION / ROUTE                                │
│  DRIVER PHONE / CONTACTS                            │
│  DRIVER PASSPORT                                    │
│  LOADING DATE                                       │
│  OFFLOADING DATE                                    │
│  WEIGHT (Net/Gross) or BAGS                         │
│  PRODUCT/COMMODITY/ITEMS                            │
│  B/L (Bill of Lading) / LOT NUMBER                  │
│  DAYS (transit / border / total)                    │
│  TYPE (IMPORT/EXPORT, vehicle type)                 │
└─────────────────────────────────────────────────────┘
```

### MEDIUM-FREQUENCY FIELDS (present in 40-70% of reports)
```
┌─────────────────────────────────────────────────────┐
│  TRANSPORTER (always "OVERLAND" when present)       │
│  ORIGIN COUNTRY / ORIGIN                            │
│  CORRIDOR                                           │
│  SHIPPING ORDER NUMBER                              │
│  UPLIFT MINE                                        │
│  OFFLOADING POINT / WAREHOUSE                       │
│  BORDER DATES (Tunduma, Nakonde, Kasumbalesa, Whiskey) │
│  DISPATCH DATES (per checkpoint)                    │
│  DRIVER LICENSE                                     │
└─────────────────────────────────────────────────────┘
```

### REPORT-SPECIFIC DERIVED FIELDS
```
┌─────────────────────────────────────────────────────┐
│  Demurrage: Free Days, Chargeable Days, Rate, Total │
│  Police Fine: Particular, Account split, Control No │
│  POD: Pod Status, Days since offloaded              │
│  Breakdown: Problem, Incharge, B/D Duration         │
│  Loading Order: LITRES, GVM, File reference         │
│  Client Template: TripCode, FXICode, BvCode         │
└─────────────────────────────────────────────────────┘
```

---

## PART 4: THE CORE DATA MODEL

All reports derive from ONE core entity: **a Shipment/Trip**, which has:

```
SHIPMENT
├── Vehicle: truck_reg, trailer_1, trailer_2, vehicle_type
├── Driver: name, phone, passport, license
├── Cargo: product, weight_net, weight_gross, bags, bl_number, lot_number, invoice
├── Route: origin, destination, corridor, direction (IMPORT/EXPORT)
├── Client: client_name, consignee, transporter
├── Milestones (ordered checkpoint timestamps):
│   ├── allocated_date
│   ├── loading_point_arrival
│   ├── loading_date
│   ├── dispatch_date
│   ├── tunduma_arrival / tunduma_dispatch
│   ├── nakonde_arrival / nakonde_dispatch
│   ├── kasumbalesa_zmb_arrival / kasumbalesa_drc_arrival
│   ├── whiskey_arrival / whiskey_dispatch
│   ├── destination_arrival
│   ├── offload_date
│   └── pod_received_date
├── Location: current_location, status, remark
├── Computed:
│   ├── transit_days, border_days, total_days
│   ├── free_days, chargeable_days
│   └── demurrage_amount
└── Incidents:
    ├── breakdowns (location, problem, duration)
    └── fines (particular, amount, date)
```

**Every single report is just a VIEW/FILTER/AGGREGATION of this model.**

---

## PART 5: IMPLEMENTATION PLAN

### Phase 1: Core Data Model & Database Schema

#### 1.1 Database Tables

```sql
-- Core entities
vehicles (id, truck_reg, vehicle_type, owner)
trailers (id, trailer_reg, type)
drivers (id, name, phone, passport, license_no)
clients (id, name, type)
mines_warehouses (id, name, location, type) -- KCC, MUMI, DCG DAR, TAZARA...
border_checkpoints (id, name, country)       -- Tunduma, Nakonde, Kasumbalesa, Whiskey...

-- Core shipment
shipments (
    id, shipping_order,
    vehicle_id, trailer_1_id, trailer_2_id,
    driver_id, client_id,
    product, weight_net, weight_gross, bags,
    bl_number, lot_number, invoice_number, manifest_number,
    fxi_code, bv_code, -- client reference codes
    origin_id, destination_id, corridor,
    direction,  -- IMPORT/EXPORT
    transporter, clearing_agent,
    current_location, status, remark,
    created_at, updated_at
)

-- Milestone timestamps
shipment_milestones (
    id, shipment_id,
    checkpoint_id,     -- FK to border_checkpoints or custom
    milestone_type,    -- ARRIVAL, DEPARTURE, LOADING, OFFLOADING
    timestamp,
    days_at_checkpoint -- calculated
)

-- Daily location tracking (for the master report time-series)
daily_locations (
    id, shipment_id,
    date, time,
    location_text,  -- free text like "Mpika enroute to Shituru"
    is_breakdown     -- parsed from text containing "b/d" or "B/DOWN"
)

-- Breakdowns
breakdowns (
    id, vehicle_id, driver_id, shipment_id,
    location, problem_diagnosed,
    incharge_person,
    start_date, end_date, days,
    client_id, status
)

-- Demurrage
demurrage_charges (
    id, shipment_id, client_id,
    charge_type,  -- IMPORT_BORDER, EXPORT_LOADING, OFFLOADING
    arrival_date, dispatch_date,
    delay_days, free_days, chargeable_days,
    rate_per_day, parking_penalty,
    total_amount_usd
)

-- Police fines
police_fines (
    id, vehicle_id, driver_id,
    fine_date,
    particular,  -- DEFECTIVE TIRES, CONDITION OF MOTOR VEHICLE...
    shipping_order,
    driver_account_amount, company_account_amount,
    control_number, total_tzs
)

-- POD tracking
pod_records (
    id, shipment_id,
    loading_date, offloading_date,
    days_since_offloaded,
    pod_status,  -- RECEIVED, PENDING
    remark
)

-- Loading orders
loading_orders (
    id, shipment_id,
    order_date, shipping_order,
    allocated_date, loading_date,
    litres, -- for tankers
    going_cargo_client, return_cargo_client,
    order_confirmed
)
```

#### 1.2 Python Models (Django/SQLAlchemy style)

Create models that mirror the tables above. The key is that `Shipment` is the central entity and everything links to it.

---

### Phase 2: Report Generation Engine

#### 2.1 Report Registry

Each report type becomes a **Report Definition** with:
- Name, category, client filter
- Required columns (mapped from universal fields)
- Computed columns (formulas)
- Grouping/filtering rules
- Template (Overland Standard, Client KCC, BASH, etc.)

```python
REPORT_DEFINITIONS = {
    "glencore_export_kcc_dar": {
        "category": "A_ROUTE_TRACKING",
        "client_filter": ["GLENCORE"],
        "mine_filter": ["KCC"],
        "destination_filter": ["DCG DAR"],
        "direction": "EXPORT",
        "template": "overland_standard_export",
        "group_by_period": "monthly",
    },
    "bash_north_bound": {
        "category": "A_ROUTE_TRACKING",
        "client_filter": ["BASH", "XIN DA SARL"],
        "direction": "IMPORT",
        "template": "bash_import",
        "includes_demurrage": True,
    },
    "kcc_po_tracking": {
        "category": "A_ROUTE_TRACKING",
        "client_filter": ["GLENCORE"],
        "direction": "IMPORT",
        "template": "client_kcc",
        "po_number": "C003636963",
    },
    "breakdown_report": {
        "category": "E_OPERATIONAL",
        "template": "breakdown_monthly",
        "group_by_period": "monthly",
    },
    "police_fine_report": {
        "category": "D_FINANCIAL",
        "template": "police_fine_daily",
        "group_by_period": "daily",
    },
    "demurrage_import": {
        "category": "D_FINANCIAL",
        "template": "demurrage_charges",
        "charge_type": "IMPORT_BORDER",
    },
    "demurrage_export_loading": {
        "category": "D_FINANCIAL",
        "template": "demurrage_charges",
        "charge_type": "EXPORT_LOADING",
    },
    "master_daily_tracker": {
        "category": "B_DAILY_SNAPSHOT",
        "template": "daily_location_grid",
        "date_range": "rolling_60_days",
    },
    "tunduma_border_snapshot": {
        "category": "C_LOCATION_SNAPSHOT",
        "template": "border_snapshot",
        "location_filter": ["TUNDUMA"],
    },
    "ndola_yard_snapshot": {
        "category": "C_LOCATION_SNAPSHOT",
        "template": "border_snapshot",
        "location_filter": ["NDOLA"],
    },
    "pod_tracking": {
        "category": "E_OPERATIONAL",
        "template": "pod_status",
        "group_by_period": "monthly",
    },
    "loading_order": {
        "category": "E_OPERATIONAL",
        "template": "loading_order",
        "group_by_period": "monthly",
    },
    "offloading_mines_summary": {
        "category": "C_LOCATION_SNAPSHOT",
        "template": "mines_summary",
    },
}
```

#### 2.2 Template Engine

Each template defines the output format:

```python
TEMPLATES = {
    "overland_standard_export": {
        "columns": [
            "SN#", "Uplift", "Offloading Point", "Transporter", "Lot No",
            "Truck", "Trailer I", "Trailer II",
            "Driver Name", "Phone", "Passport",
            "Loading Capacities", "Type",
            "Current Location", "REMARK",
            # Border checkpoint pairs (dynamic based on route)
            "Origins.Arrival", "Origins.Loaded", "Origins.Departure", "Origins.Days",
            "WHISKY.Arrival", "WHISKY.Dispatch",
            "KASUMBALESA.Arrival", "KASUMBALESA.Dispatch",
            "Nakonde.Arrival", "Nakonde.Dispatch",
            "Tunduma.Arrival", "Tunduma.Dispatch",
            "Final.Arrival", "Final.Offloaded", "Total.Days", "Total.Delays"
        ],
    },
    "client_kcc": {
        "columns": [
            "TripCode", "OrderNumber",
            "Bag Number", "Net Weight (MT)", "Gross Weight (MT)",
            "Invoice Number", "Consignment Number", "Supplier", "Product",
            "Origin Country", "Destination Country", "Corridor",
            "FXICode", "Bv Code",
            "Truck Reg", "TrailerRegistration1", "TrailerRegistration2",
            "Nominated Haulier", "Drivers Name", "DriverPassport",
            "Current Location", "Inbound Status",
            "DCG Kisarawe arrival date", "Loading Date", "Origin Dispatch Date",
            "Tunduma arrival Date", "Tunduma Dispatch Date", "Nakonde Dispatch Date",
            "Last Update Date Position", "Trip Duration in Days",
            "Kasumbalesa Arrive date", "Kasumbalesa Dispatch Date",
            "Border delays Days",
            "KCC Arrive date", "KCC Offload Date", "Offload delays Days",
            "Clearing Agents"
        ],
    },
    # ... etc for each template
}
```

---

### Phase 3: Implementation Steps

#### Step 1: Data Import Layer (Week 1)
- [ ] Create standardized column mapping config (building on existing `analyze_column` logic)
- [ ] Build Excel parser that handles merged headers (the "Unnamed:" problem)
- [ ] Parse the header rows correctly (many files have header in row 2-3, not row 1)
- [ ] Handle date format variations (dd/mm/yyyy, ISO, text dates like "20th January 2026")
- [ ] Import all existing Excel data into the database

#### Step 2: Core Models (Week 1-2)
- [ ] Implement the database schema (SQLite for simplicity, or PostgreSQL)
- [ ] Create Shipment CRUD operations
- [ ] Build the milestone/checkpoint tracking system
- [ ] Implement the daily location tracking
- [ ] Build vehicle, driver, client lookup/dedup logic

#### Step 3: Report Generators (Week 2-3)
**For each category, build a generator class:**

- [ ] **Category A - Route Tracking Generator**
  - Query shipments by client + direction + date range
  - Format milestones into the correct checkpoint columns
  - Support both "Overland Standard" and "Client KCC" templates
  - Calculate transit days, border days, total delays

- [ ] **Category B - Daily Snapshot Generator**
  - Pivot daily_locations table: rows=trucks, columns=dates
  - Generate the rolling date column headers
  - Fill cells with location text

- [ ] **Category C - Location Snapshot Generator**
  - Query shipments by current_location
  - Calculate days at location
  - Group by IMPORT/EXPORT

- [ ] **Category D - Financial Report Generator**
  - Calculate demurrage from milestone dates
  - Apply free-day rules per client
  - Calculate police fines from fine records

- [ ] **Category E - Operational Report Generator**
  - Loading order formatting
  - POD status tracking
  - Breakdown report aggregation

#### Step 4: Export Engine (Week 3)
- [ ] Excel export with proper formatting (merged headers, date formats)
- [ ] Multi-sheet workbook generation (monthly sheets, per-BL sheets)
- [ ] Summary sheet generation
- [ ] Client-specific branding/titles

#### Step 5: GUI Integration (Week 4)
- [ ] Extend existing GUI with report selection
- [ ] Date range picker
- [ ] Client/route filters
- [ ] Preview before export
- [ ] Batch report generation

---

### Phase 4: Non-Duplicate Strategy

Since the same truck/driver/shipment appears across MULTIPLE reports:

1. **Shipment deduplication:** Use `(truck_reg, loading_date, destination)` as natural key
2. **Import priority:** KCC/MUMI PO reports have the most structured data → import first as "golden records"
3. **Enrichment:** Overlay Glencore export data, BASH data for additional fields
4. **Daily location is additive:** Each daily snapshot adds to the timeline, never overwrites
5. **Financial data is always additive:** Each demurrage/fine is a separate record

---

## PART 6: WHAT YOUR SYSTEM ALREADY HAS vs. WHAT'S NEEDED

### Already Built (master_merge/)
- Excel file discovery and reading
- Basic column name standardization (truck, location, driver, etc.)
- Generic merge logic (concatenate all rows)
- Deduplication (basic exact-row match)
- GUI for file selection and merge

### What's Missing
| Gap | Priority | Effort |
|-----|----------|--------|
| Proper header parsing (row 2-3 headers, merged cells) | HIGH | Medium |
| Database storage (currently merge-to-flat-file only) | HIGH | High |
| Report-aware processing (not all sheets are equal data) | HIGH | High |
| Milestone/checkpoint extraction from dates | HIGH | Medium |
| Shipment entity resolution (link same truck across reports) | HIGH | High |
| Computed field engine (days, demurrage, etc.) | MEDIUM | Medium |
| Client-specific export templates | MEDIUM | High |
| Daily location time-series handling | MEDIUM | Medium |
| Financial report generators | MEDIUM | Medium |
| POD/Breakdown separate tracking | LOW | Low |
| GUI report builder interface | LOW | Medium |

---

## SUMMARY

**All 28 Excel files (586 sheets) represent different VIEWS of the same underlying data: shipments tracked by Overland trucks across the Tanzania-Zambia-DRC corridor.**

The data model is simple:
> **TRUCK + DRIVER + CARGO → travels through CHECKPOINTS → arrives at DESTINATION**

What changes between reports is:
1. **Client filter** (Glencore, Mercuria, BASH, NST, Talana, etc.)
2. **Direction** (Import vs Export)
3. **Time granularity** (milestone dates vs daily text snapshots)
4. **Derived calculations** (demurrage, fines, transit days)
5. **Template format** (Overland internal vs client-specific)

Build the **one data model**, and all 28+ reports become **parameterized queries with templates**.
