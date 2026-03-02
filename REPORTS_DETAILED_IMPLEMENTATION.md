# OVERLAND TRACKING SYSTEM — DETAILED REPORT IMPLEMENTATION
> CodeIgniter MVC | Step-by-Step Technical Specification
> Date: 2026-03-02

---

## TABLE OF CONTENTS
1. [Database Schema Extensions](#1-database-schema-extensions)
2. [Phase 1: Client Report](#2-phase-1-client-report)
3. [Phase 2: NB/SB & Master Reports](#3-phase-2-nbsb--master-reports)
4. [Phase 3: Border, Financial, POD, Breakdown](#4-phase-3-border-financial-pod-breakdown)
5. [Phase 4: Live GPS & Offline Reports](#5-phase-4-live-gps--offline-reports)
6. [Shared Infrastructure](#6-shared-infrastructure)
7. [Route & Auth Configuration](#7-route--auth-configuration)

---

## 1. DATABASE SCHEMA EXTENSIONS

> Assuming your CI system already has the core shipments, drivers, vehicles, clients tables.
> These are the **additions needed** only for report generation.

```sql
-- ─────────────────────────────────────────────
-- 1.1 REPORT SNAPSHOT CACHE (optional but recommended)
-- ─────────────────────────────────────────────
CREATE TABLE report_cache (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    report_type  VARCHAR(60)  NOT NULL,  -- 'client_tracking', 'master_report', etc.
    report_key   VARCHAR(255) NOT NULL,  -- hashed params (client_id + date range + filters)
    payload      LONGTEXT     NOT NULL,  -- JSON-serialized result set
    generated_at DATETIME     NOT NULL,
    expires_at   DATETIME     NOT NULL,
    INDEX idx_report_key (report_key),
    INDEX idx_expires (expires_at)
);

-- ─────────────────────────────────────────────
-- 1.2 SHIPMENT MILESTONES (if not already present)
-- ─────────────────────────────────────────────
CREATE TABLE shipment_milestones (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    shipment_id   INT UNSIGNED NOT NULL,
    checkpoint    ENUM(
                      'loading_point',
                      'tunduma_tz',
                      'nakonde_zm',
                      'kasumbalesa_zm',
                      'kasumbalesa_drc',
                      'whiskey',
                      'destination',
                      'offloaded',
                      'pod_received'
                  ) NOT NULL,
    arrived_at    DATETIME    NULL,
    departed_at   DATETIME    NULL,
    days_at       SMALLINT    GENERATED ALWAYS AS (
                      DATEDIFF(COALESCE(departed_at, NOW()), arrived_at)
                  ) STORED,
    notes         TEXT        NULL,
    recorded_by   INT UNSIGNED NULL,
    created_at    DATETIME    DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_shipment_checkpoint (shipment_id, checkpoint),
    INDEX idx_shipment (shipment_id)
);

-- ─────────────────────────────────────────────
-- 1.3 DEMURRAGE RECORDS
-- ─────────────────────────────────────────────
CREATE TABLE demurrage_records (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    shipment_id         INT UNSIGNED NOT NULL,
    client_id           INT UNSIGNED NOT NULL,
    charge_leg          ENUM('border', 'offloading', 'mine_loading') NOT NULL,
    reference_date_from DATE         NOT NULL,
    reference_date_to   DATE         NULL,
    free_days           TINYINT      NOT NULL DEFAULT 7,
    total_days          SMALLINT     NOT NULL DEFAULT 0,
    chargeable_days     SMALLINT     GENERATED ALWAYS AS (
                            GREATEST(0, total_days - free_days)
                        ) STORED,
    rate_per_day_usd    DECIMAL(10,2) NOT NULL DEFAULT 250.00,
    parking_penalty_usd DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_amount_usd    DECIMAL(12,2) GENERATED ALWAYS AS (
                            (GREATEST(0, total_days - free_days) * rate_per_day_usd) + parking_penalty_usd
                        ) STORED,
    status              ENUM('draft','invoiced','paid','disputed') DEFAULT 'draft',
    invoice_ref         VARCHAR(60) NULL,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- 1.4 POLICE FINES
-- ─────────────────────────────────────────────
CREATE TABLE police_fines (
    id               INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    vehicle_id       INT UNSIGNED NOT NULL,
    driver_id        INT UNSIGNED NOT NULL,
    shipment_id      INT UNSIGNED NULL,
    fine_date        DATE         NOT NULL,
    particulars      VARCHAR(255) NOT NULL,
    shipping_order   VARCHAR(60)  NULL,
    driver_amount_tzs DECIMAL(12,2) NOT NULL DEFAULT 0,
    company_amount_tzs DECIMAL(12,2) NOT NULL DEFAULT 0,
    control_number   VARCHAR(60)  NULL,
    paid             BOOLEAN      NOT NULL DEFAULT FALSE,
    paid_at          DATETIME     NULL,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- 1.5 GPS PINGS (for Phase 4)
-- ─────────────────────────────────────────────
CREATE TABLE gps_pings (
    id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    vehicle_id   INT UNSIGNED NOT NULL,
    latitude     DECIMAL(10,7) NOT NULL,
    longitude    DECIMAL(10,7) NOT NULL,
    speed_kmh    SMALLINT  NULL,
    heading_deg  SMALLINT  NULL,
    location_name VARCHAR(120) NULL, -- resolved from coordinates
    pinged_at    DATETIME  NOT NULL,
    INDEX idx_vehicle_time (vehicle_id, pinged_at)
) PARTITION BY RANGE (YEAR(pinged_at)) (
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION pmax  VALUES LESS THAN MAXVALUE
);

-- ─────────────────────────────────────────────
-- 1.6 DAILY LOCATION SNAPSHOTS (for Master Report grid)
-- ─────────────────────────────────────────────
CREATE TABLE daily_locations (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    shipment_id  INT UNSIGNED NOT NULL,
    snapshot_date DATE        NOT NULL,
    location_text VARCHAR(180) NOT NULL,
    is_breakdown  BOOLEAN NOT NULL DEFAULT FALSE,
    is_border     BOOLEAN NOT NULL DEFAULT FALSE,
    recorded_by   INT UNSIGNED NULL,
    recorded_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_shipment_date (shipment_id, snapshot_date)
);

-- ─────────────────────────────────────────────
-- 1.7 USEFUL VIEWS FOR REPORTS
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW v_active_shipments AS
SELECT
    s.id,
    s.shipping_order,
    s.direction,                    -- IMPORT / EXPORT
    v.truck_reg,
    t1.trailer_reg  AS trailer_1,
    t2.trailer_reg  AS trailer_2,
    d.full_name     AS driver_name,
    d.phone         AS driver_phone,
    d.passport      AS driver_passport,
    d.license_no    AS driver_license,
    c.name          AS client_name,
    s.product,
    s.weight_net,
    s.weight_gross,
    s.bag_count,
    s.bl_number,
    s.lot_number,
    s.invoice_number,
    s.origin,
    s.destination,
    s.corridor,
    s.current_location,
    s.status,
    s.remarks,
    s.allocated_date,
    -- Milestone shortcuts
    ms_load.arrived_at  AS loading_date,
    ms_load.departed_at AS dispatch_date,
    ms_tund.arrived_at  AS tunduma_arrival,
    ms_tund.departed_at AS tunduma_dispatch,
    ms_nako.arrived_at  AS nakonde_arrival,
    ms_nako.departed_at AS nakonde_dispatch,
    ms_klza.arrived_at  AS kasumbalesa_zm_arrival,
    ms_kldrc.arrived_at AS kasumbalesa_drc_arrival,
    ms_kldrc.departed_at AS kasumbalesa_drc_dispatch,
    ms_whis.arrived_at  AS whiskey_arrival,
    ms_whis.departed_at AS whiskey_dispatch,
    ms_dest.arrived_at  AS destination_arrival,
    ms_offl.arrived_at  AS offloaded_date,
    ms_pod.arrived_at   AS pod_received_date,
    -- Computed days
    DATEDIFF(COALESCE(ms_offl.arrived_at, NOW()), ms_load.arrived_at) AS total_days_in_transit,
    s.client_id,
    s.vehicle_id,
    s.driver_id
FROM shipments s
JOIN vehicles  v    ON v.id = s.vehicle_id
LEFT JOIN trailers t1   ON t1.id = s.trailer_1_id
LEFT JOIN trailers t2   ON t2.id = s.trailer_2_id
JOIN drivers   d    ON d.id = s.driver_id
JOIN clients   c    ON c.id = s.client_id
LEFT JOIN shipment_milestones ms_load  ON ms_load.shipment_id  = s.id AND ms_load.checkpoint  = 'loading_point'
LEFT JOIN shipment_milestones ms_tund  ON ms_tund.shipment_id  = s.id AND ms_tund.checkpoint  = 'tunduma_tz'
LEFT JOIN shipment_milestones ms_nako  ON ms_nako.shipment_id  = s.id AND ms_nako.checkpoint  = 'nakonde_zm'
LEFT JOIN shipment_milestones ms_klza  ON ms_klza.shipment_id  = s.id AND ms_klza.checkpoint  = 'kasumbalesa_zm'
LEFT JOIN shipment_milestones ms_kldrc ON ms_kldrc.shipment_id = s.id AND ms_kldrc.checkpoint = 'kasumbalesa_drc'
LEFT JOIN shipment_milestones ms_whis  ON ms_whis.shipment_id  = s.id AND ms_whis.checkpoint  = 'whiskey'
LEFT JOIN shipment_milestones ms_dest  ON ms_dest.shipment_id  = s.id AND ms_dest.checkpoint  = 'destination'
LEFT JOIN shipment_milestones ms_offl  ON ms_offl.shipment_id  = s.id AND ms_offl.checkpoint  = 'offloaded'
LEFT JOIN shipment_milestones ms_pod   ON ms_pod.shipment_id   = s.id AND ms_pod.checkpoint   = 'pod_received'
WHERE s.deleted_at IS NULL;
```

---

## 2. PHASE 1: CLIENT REPORT

### 2.1 Controller — `application/controllers/reports/Client_report.php`

```php
<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Client_report extends CI_Controller {

    public function __construct() {
        parent::__construct();
        // Ensure client is logged in
        if (!$this->session->userdata('logged_in')) {
            redirect('auth/login');
        }
        $this->load->model('reports/Shipment_report_model', 'report_model');
        $this->load->library('Report_exporter');
        $this->load->helper('report_helper');
    }

    /**
     * Main client tracking report (HTML view)
     * URL: /client/reports/tracking
     */
    public function tracking() {
        $client_id  = $this->session->userdata('client_id');
        $date_from  = $this->input->get('date_from') ?: date('Y-m-01');
        $date_to    = $this->input->get('date_to')   ?: date('Y-m-t');
        $direction  = $this->input->get('direction');  // NB / SB / null (both)
        $status     = $this->input->get('status');     // enroute / offloaded / breakdown / null

        $filters = [
            'client_id'  => $client_id,
            'date_from'  => $date_from,
            'date_to'    => $date_to,
            'direction'  => $direction,
            'status'     => $status,
        ];

        $data = [
            'title'      => 'Tracking Report — ' . $this->session->userdata('client_name'),
            'shipments'  => $this->report_model->get_client_tracking($filters),
            'filters'    => $filters,
            'summary'    => $this->report_model->get_client_summary($filters),
        ];

        $this->load->view('reports/client/tracking', $data);
    }

    /**
     * Export to Excel
     * URL: /client/reports/tracking/export/excel
     */
    public function export_excel() {
        $client_id = $this->session->userdata('client_id');
        $filters   = array_merge(
            $this->input->get(null, TRUE) ?: [],
            ['client_id' => $client_id]
        );

        $shipments   = $this->report_model->get_client_tracking($filters);
        $client_name = $this->session->userdata('client_name');

        $this->report_exporter->client_tracking_excel(
            $shipments,
            $client_name,
            $filters
        );
        // ↑ sends download headers and exits
    }

    /**
     * Export to PDF
     * URL: /client/reports/tracking/export/pdf
     */
    public function export_pdf() {
        $client_id = $this->session->userdata('client_id');
        $filters   = array_merge(
            $this->input->get(null, TRUE) ?: [],
            ['client_id' => $client_id]
        );

        $shipments = $this->report_model->get_client_tracking($filters);

        $this->report_exporter->client_tracking_pdf(
            $shipments,
            $this->session->userdata('client_name'),
            $filters
        );
    }

    /**
     * Demurrage report for client
     * URL: /client/reports/demurrage
     */
    public function demurrage() {
        $client_id = $this->session->userdata('client_id');
        $filters   = [
            'client_id' => $client_id,
            'date_from' => $this->input->get('date_from') ?: date('Y-m-01'),
            'date_to'   => $this->input->get('date_to')   ?: date('Y-m-t'),
            'status'    => $this->input->get('status'),
        ];

        $data = [
            'title'            => 'Demurrage Report',
            'demurrage_records' => $this->report_model->get_demurrage_for_client($filters),
            'totals'           => $this->report_model->get_demurrage_totals($filters),
            'filters'          => $filters,
        ];

        $this->load->view('reports/client/demurrage', $data);
    }

    /**
     * POD Status report for client
     * URL: /client/reports/pod
     */
    public function pod() {
        $client_id = $this->session->userdata('client_id');
        $filters = [
            'client_id' => $client_id,
            'date_from' => $this->input->get('date_from') ?: date('Y-m-01'),
            'date_to'   => $this->input->get('date_to')   ?: date('Y-m-t'),
            'pod_status' => $this->input->get('pod_status'), // RECEIVED/PENDING
        ];

        $data = [
            'title'   => 'POD Status Report',
            'records' => $this->report_model->get_pod_for_client($filters),
            'filters' => $filters,
        ];

        $this->load->view('reports/client/pod', $data);
    }
}
```

---

### 2.2 Model — `application/models/reports/Shipment_report_model.php`

```php
<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Shipment_report_model extends CI_Model {

    public function __construct() {
        parent::__construct();
        $this->load->database();
    }

    /**
     * Core client tracking query.
     * Uses v_active_shipments view for clean, pre-joined data.
     */
    public function get_client_tracking(array $f): array {
        $this->db->from('v_active_shipments');

        // MANDATORY client isolation
        if (!empty($f['client_id'])) {
            $this->db->where('client_id', (int)$f['client_id']);
        }

        if (!empty($f['date_from'])) {
            $this->db->where('loading_date >=', $f['date_from'] . ' 00:00:00');
        }
        if (!empty($f['date_to'])) {
            $this->db->where('loading_date <=', $f['date_to'] . ' 23:59:59');
        }
        if (!empty($f['direction'])) {
            $this->db->where('direction', strtoupper($f['direction']));
        }
        if (!empty($f['status'])) {
            $this->db->like('status', $f['status']);
        }

        $this->db->order_by('loading_date', 'DESC');

        return $this->db->get()->result_array();
    }

    /**
     * Summary counts for client dashboard widget.
     */
    public function get_client_summary(array $f): array {
        $this->db->select(
            "COUNT(*) AS total,
             SUM(status LIKE '%enroute%' OR status LIKE '%transit%') AS in_transit,
             SUM(status LIKE '%offloaded%' OR status LIKE '%completed%') AS completed,
             SUM(status LIKE '%breakdown%' OR status LIKE '%b/d%') AS breakdowns,
             SUM(status LIKE '%border%' OR status LIKE '%tunduma%' OR status LIKE '%nakonde%') AS at_border",
            FALSE
        );
        $this->db->from('v_active_shipments');

        if (!empty($f['client_id'])) {
            $this->db->where('client_id', (int)$f['client_id']);
        }
        if (!empty($f['date_from'])) {
            $this->db->where('loading_date >=', $f['date_from']);
        }
        if (!empty($f['date_to'])) {
            $this->db->where('loading_date <=', $f['date_to']);
        }

        return $this->db->get()->row_array() ?: [];
    }

    /**
     * Demurrage query for a specific client.
     */
    public function get_demurrage_for_client(array $f): array {
        $this->db->select(
            'dr.*, v.truck_reg, t1.trailer_reg AS trailer_1, t2.trailer_reg AS trailer_2,
             s.shipping_order, s.bl_number, s.lot_number, s.current_location, s.status'
        );
        $this->db->from('demurrage_records dr');
        $this->db->join('shipments s', 's.id = dr.shipment_id');
        $this->db->join('vehicles v', 'v.id = s.vehicle_id');
        $this->db->join('trailers t1', 't1.id = s.trailer_1_id', 'left');
        $this->db->join('trailers t2', 't2.id = s.trailer_2_id', 'left');
        $this->db->where('dr.client_id', (int)$f['client_id']);

        if (!empty($f['date_from'])) {
            $this->db->where('dr.reference_date_from >=', $f['date_from']);
        }
        if (!empty($f['date_to'])) {
            $this->db->where('dr.reference_date_from <=', $f['date_to']);
        }
        if (!empty($f['status'])) {
            $this->db->where('dr.status', $f['status']);
        }

        $this->db->order_by('dr.reference_date_from', 'DESC');
        return $this->db->get()->result_array();
    }

    public function get_demurrage_totals(array $f): array {
        $this->db->select(
            'SUM(total_days) AS total_days,
             SUM(chargeable_days) AS chargeable_days,
             SUM(total_amount_usd) AS total_usd',
            FALSE
        );
        $this->db->from('demurrage_records');
        $this->db->where('client_id', (int)$f['client_id']);
        if (!empty($f['date_from'])) $this->db->where('reference_date_from >=', $f['date_from']);
        if (!empty($f['date_to']))   $this->db->where('reference_date_from <=', $f['date_to']);
        return $this->db->get()->row_array() ?: ['total_days'=>0,'chargeable_days'=>0,'total_usd'=>0];
    }

    public function get_pod_for_client(array $f): array {
        $this->db->select(
            'vas.*, pr.pod_status, pr.days_since_offloaded, pr.notes AS pod_notes'
        );
        $this->db->from('v_active_shipments vas');
        $this->db->join('pod_records pr', 'pr.shipment_id = vas.id', 'left');
        $this->db->where('vas.client_id', (int)$f['client_id']);

        if (!empty($f['date_from'])) {
            $this->db->where('vas.offloaded_date >=', $f['date_from']);
        }
        if (!empty($f['date_to'])) {
            $this->db->where('vas.offloaded_date <=', $f['date_to']);
        }
        if (!empty($f['pod_status'])) {
            $this->db->where('pr.pod_status', $f['pod_status']);
        }

        $this->db->order_by('vas.offloaded_date', 'DESC');
        return $this->db->get()->result_array();
    }

    // ──────────────────────────────────────────
    // PHASE 2 QUERIES
    // ──────────────────────────────────────────

    /**
     * All active shipments (no client filter) for internal NB/SB report.
     */
    public function get_all_shipments_nb_sb(array $f): array {
        $this->db->from('v_active_shipments');
        if (!empty($f['direction'])) $this->db->where('direction', strtoupper($f['direction']));
        if (!empty($f['date_from'])) $this->db->where('loading_date >=', $f['date_from']);
        if (!empty($f['date_to']))   $this->db->where('loading_date <=', $f['date_to']);
        if (!empty($f['client_id'])) $this->db->where('client_id', (int)$f['client_id']);
        $this->db->order_by('client_name, loading_date DESC');
        return $this->db->get()->result_array();
    }

    /**
     * Master Report: all shipments with their daily location snapshots.
     * Returns pivot-ready structure: shipment + array of date=>location.
     */
    public function get_master_report_data(string $date_from, string $date_to): array {
        // Shipments
        $this->db->from('v_active_shipments');
        $this->db->where('loading_date >=', $date_from);
        $this->db->order_by('client_name, truck_reg');
        $shipments = $this->db->get()->result_array();

        if (empty($shipments)) return [];

        $shipment_ids = array_column($shipments, 'id');

        // Daily locations for all shipments in range
        $this->db->select('shipment_id, snapshot_date, location_text, is_breakdown');
        $this->db->from('daily_locations');
        $this->db->where_in('shipment_id', $shipment_ids);
        $this->db->where('snapshot_date >=', $date_from);
        $this->db->where('snapshot_date <=', $date_to);
        $locations_raw = $this->db->get()->result_array();

        // Index by shipment_id => date => text
        $location_map = [];
        foreach ($locations_raw as $loc) {
            $location_map[$loc['shipment_id']][$loc['snapshot_date']] = [
                'text'         => $loc['location_text'],
                'is_breakdown' => (bool)$loc['is_breakdown'],
            ];
        }

        foreach ($shipments as &$s) {
            $s['daily_locations'] = $location_map[$s['id']] ?? [];
        }

        return $shipments;
    }

    /**
     * Border report — trucks currently at a specific checkpoint.
     */
    public function get_border_snapshot(string $checkpoint, string $direction = null): array {
        $this->db->from('v_active_shipments');
        $this->db->like('current_location', $checkpoint, 'both');
        if ($direction) $this->db->where('direction', strtoupper($direction));
        // Not yet offloaded
        $this->db->where('offloaded_date IS NULL', null, false);
        $this->db->order_by('client_name, truck_reg');
        return $this->db->get()->result_array();
    }

    /**
     * Breakdown report — monthly.
     */
    public function get_breakdowns(array $f): array {
        $this->db->select(
            'b.*, v.truck_reg, t.trailer_reg, d.full_name AS driver_name, c.name AS client_name'
        );
        $this->db->from('breakdowns b');
        $this->db->join('vehicles v', 'v.id = b.vehicle_id');
        $this->db->join('trailers t', 't.id = b.trailer_id', 'left');
        $this->db->join('drivers d', 'd.id = b.driver_id');
        $this->db->join('clients c', 'c.id = b.client_id', 'left');
        if (!empty($f['date_from'])) $this->db->where('b.start_date >=', $f['date_from']);
        if (!empty($f['date_to']))   $this->db->where('b.start_date <=', $f['date_to']);
        if (!empty($f['status']))    $this->db->where('b.status', $f['status']);
        $this->db->order_by('b.start_date DESC');
        return $this->db->get()->result_array();
    }

    /**
     * Police fine report.
     */
    public function get_police_fines(array $f): array {
        $this->db->select(
            'pf.*, v.truck_reg, d.full_name AS driver_name'
        );
        $this->db->from('police_fines pf');
        $this->db->join('vehicles v', 'v.id = pf.vehicle_id');
        $this->db->join('drivers d', 'd.id = pf.driver_id');
        if (!empty($f['date_from'])) $this->db->where('pf.fine_date >=', $f['date_from']);
        if (!empty($f['date_to']))   $this->db->where('pf.fine_date <=', $f['date_to']);
        if (!empty($f['vehicle_id'])) $this->db->where('pf.vehicle_id', (int)$f['vehicle_id']);
        $this->db->order_by('pf.fine_date DESC');
        return $this->db->get()->result_array();
    }

    /**
     * Offloading & Mines summary.
     */
    public function get_offloading_mines_report(): array {
        // At offloading (destination arrived, not yet offloaded)
        $this->db->select('*, DATEDIFF(NOW(), destination_arrival) AS days_at_destination');
        $this->db->from('v_active_shipments');
        $this->db->where('destination_arrival IS NOT NULL', null, false);
        $this->db->where('offloaded_date IS NULL', null, false);
        $this->db->order_by('days_at_destination DESC');
        $at_destination = $this->db->get()->result_array();

        // Summary by client
        $this->db->select('client_name, COUNT(*) AS truck_count, AVG(DATEDIFF(NOW(), destination_arrival)) AS avg_days', FALSE);
        $this->db->from('v_active_shipments');
        $this->db->where('destination_arrival IS NOT NULL', null, false);
        $this->db->where('offloaded_date IS NULL', null, false);
        $this->db->group_by('client_name');
        $summary = $this->db->get()->result_array();

        return [
            'trucks'  => $at_destination,
            'summary' => $summary,
        ];
    }
}
```

---

### 2.3 Library — `application/libraries/Report_exporter.php`

```php
<?php
defined('BASEPATH') OR exit('No direct script access allowed');

use PhpOffice\PhpSpreadsheet\Spreadsheet;
use PhpOffice\PhpSpreadsheet\Writer\Xlsx;
use PhpOffice\PhpSpreadsheet\Style\{Fill, Alignment, Border, Font};

class Report_exporter {

    private $CI;

    public function __construct() {
        $this->CI =& get_instance();
    }

    /**
     * Client tracking report — Excel
     */
    public function client_tracking_excel(array $shipments, string $client, array $filters): void {
        $spreadsheet = new Spreadsheet();
        $sheet = $spreadsheet->getActiveSheet();
        $sheet->setTitle('Tracking Report');

        // ── HEADER ROW 1: Title ──
        $sheet->setCellValue('A1', 'OVERLAND GROUP OF COMPANIES');
        $sheet->mergeCells('A1:U1');
        $this->style_title($sheet, 'A1:U1');

        // ── HEADER ROW 2: Sub-title ──
        $dateRange = date('d M Y', strtotime($filters['date_from'])) . ' to ' . date('d M Y', strtotime($filters['date_to']));
        $direction = !empty($filters['direction']) ? strtoupper($filters['direction']) : 'NB & SB';
        $sheet->setCellValue('A2', "TRACKING REPORT — {$client} — {$direction} — {$dateRange}");
        $sheet->mergeCells('A2:U2');
        $this->style_subtitle($sheet, 'A2:U2');

        // ── COLUMN HEADERS ──
        $headers = [
            'A' => 'S/N',      'B' => 'TRUCK',       'C' => 'TRAILER I',
            'D' => 'TRAILER II','E' => 'DRIVER NAME', 'F' => 'PHONE',
            'G' => 'PRODUCT',  'H' => 'NET WEIGHT',   'I' => 'BL / LOT NO',
            'J' => 'ORIGIN',   'K' => 'DESTINATION',  'L' => 'DIR',
            'M' => 'LOADING DATE', 'N' => 'DISPATCH DATE',
            'O' => 'TUNDUMA ARR', 'P' => 'TUNDUMA DEP',
            'Q' => 'NAKONDE ARR', 'R' => 'KASUMBALESA ARR',
            'S' => 'DESTINATION ARR', 'T' => 'OFFLOADED DATE',
            'U' => 'STATUS / REMARKS',
        ];

        foreach ($headers as $col => $label) {
            $sheet->setCellValue("{$col}3", $label);
        }
        $sheet->getStyle('A3:U3')->applyFromArray($this->header_style());

        // ── DATA ROWS ──
        $row = 4;
        foreach ($shipments as $i => $s) {
            $sheet->setCellValue("A{$row}", $i + 1);
            $sheet->setCellValue("B{$row}", $s['truck_reg']);
            $sheet->setCellValue("C{$row}", $s['trailer_1'] ?? '');
            $sheet->setCellValue("D{$row}", $s['trailer_2'] ?? '');
            $sheet->setCellValue("E{$row}", $s['driver_name']);
            $sheet->setCellValue("F{$row}", $s['driver_phone'] ?? '');
            $sheet->setCellValue("G{$row}", $s['product'] ?? '');
            $sheet->setCellValue("H{$row}", $s['weight_net'] ?? '');
            $sheet->setCellValue("I{$row}", trim(($s['bl_number'] ?? '') . ' / ' . ($s['lot_number'] ?? ''), ' /'));
            $sheet->setCellValue("J{$row}", $s['origin'] ?? '');
            $sheet->setCellValue("K{$row}", $s['destination'] ?? '');
            $sheet->setCellValue("L{$row}", $s['direction'] ?? '');
            $sheet->setCellValue("M{$row}", $s['loading_date'] ? date('d/m/Y', strtotime($s['loading_date'])) : '');
            $sheet->setCellValue("N{$row}", $s['dispatch_date'] ? date('d/m/Y', strtotime($s['dispatch_date'])) : '');
            $sheet->setCellValue("O{$row}", $s['tunduma_arrival'] ? date('d/m/Y', strtotime($s['tunduma_arrival'])) : '');
            $sheet->setCellValue("P{$row}", $s['tunduma_dispatch'] ? date('d/m/Y', strtotime($s['tunduma_dispatch'])) : '');
            $sheet->setCellValue("Q{$row}", $s['nakonde_arrival'] ? date('d/m/Y', strtotime($s['nakonde_arrival'])) : '');
            $sheet->setCellValue("R{$row}", $s['kasumbalesa_drc_arrival'] ? date('d/m/Y', strtotime($s['kasumbalesa_drc_arrival'])) : '');
            $sheet->setCellValue("S{$row}", $s['destination_arrival'] ? date('d/m/Y', strtotime($s['destination_arrival'])) : '');
            $sheet->setCellValue("T{$row}", $s['offloaded_date'] ? date('d/m/Y', strtotime($s['offloaded_date'])) : '');
            $sheet->setCellValue("U{$row}", $s['status'] ?? $s['remarks'] ?? '');

            // Color-code the row by status
            $rowStyle = $this->row_style_by_status($s['status'] ?? '');
            if ($rowStyle) {
                $sheet->getStyle("A{$row}:U{$row}")->applyFromArray($rowStyle);
            }

            $row++;
        }

        // Auto-width
        foreach (range('A', 'U') as $col) {
            $sheet->getColumnDimension($col)->setAutoSize(true);
        }

        // Freeze header
        $sheet->freezePane('A4');

        // Send file
        $filename = 'Tracking_Report_' . $client . '_' . date('Ymd') . '.xlsx';
        header('Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
        header('Content-Disposition: attachment; filename="' . $filename . '"');
        header('Cache-Control: max-age=0');

        $writer = new Xlsx($spreadsheet);
        $writer->save('php://output');
        exit;
    }

    // ── STYLE HELPERS ──

    private function style_title($sheet, string $range): void {
        $sheet->getStyle($range)->applyFromArray([
            'font' => ['bold' => true, 'size' => 14, 'color' => ['rgb' => 'FFFFFF']],
            'fill' => ['fillType' => Fill::FILL_SOLID, 'startColor' => ['rgb' => '1F3864']],
            'alignment' => ['horizontal' => Alignment::HORIZONTAL_CENTER, 'vertical' => Alignment::VERTICAL_CENTER],
        ]);
        $sheet->getRowDimension(1)->setRowHeight(30);
    }

    private function style_subtitle($sheet, string $range): void {
        $sheet->getStyle($range)->applyFromArray([
            'font' => ['bold' => true, 'size' => 11, 'color' => ['rgb' => 'FFFFFF']],
            'fill' => ['fillType' => Fill::FILL_SOLID, 'startColor' => ['rgb' => '2E75B6']],
            'alignment' => ['horizontal' => Alignment::HORIZONTAL_CENTER],
        ]);
        $sheet->getRowDimension(2)->setRowHeight(22);
    }

    private function header_style(): array {
        return [
            'font' => ['bold' => true, 'color' => ['rgb' => 'FFFFFF']],
            'fill' => ['fillType' => Fill::FILL_SOLID, 'startColor' => ['rgb' => '4472C4']],
            'alignment' => ['horizontal' => Alignment::HORIZONTAL_CENTER, 'wrapText' => true],
            'borders' => ['allBorders' => ['borderStyle' => Border::BORDER_THIN, 'color' => ['rgb' => 'FFFFFF']]],
        ];
    }

    private function row_style_by_status(string $status): ?array {
        $s = strtolower($status);
        if (str_contains($s, 'breakdown') || str_contains($s, 'b/d') || str_contains($s, 'incident')) {
            return ['fill' => ['fillType' => Fill::FILL_SOLID, 'startColor' => ['rgb' => 'FFE0E0']]]; // light red
        }
        if (str_contains($s, 'offloaded') || str_contains($s, 'completed')) {
            return ['fill' => ['fillType' => Fill::FILL_SOLID, 'startColor' => ['rgb' => 'E2EFDA']]]; // light green
        }
        if (str_contains($s, 'border') || str_contains($s, 'tunduma') || str_contains($s, 'nakonde')) {
            return ['fill' => ['fillType' => Fill::FILL_SOLID, 'startColor' => ['rgb' => 'FFF2CC']]]; // light yellow
        }
        return null; // default white
    }
}
```

---

### 2.4 Helper — `application/helpers/report_helper.php`

```php
<?php
defined('BASEPATH') OR exit('No direct script access allowed');

/**
 * Calculate days between two dates.
 * Returns 0 if either date is empty.
 */
function report_days_diff(?string $from, ?string $to = null): int {
    if (!$from) return 0;
    $d1 = new DateTime($from);
    $d2 = $to ? new DateTime($to) : new DateTime();
    return max(0, (int)$d1->diff($d2)->days);
}

/**
 * Format a datetime string to display format.
 */
function rpt_date(?string $datetime, string $format = 'd/m/Y'): string {
    if (!$datetime || $datetime === '0000-00-00' || $datetime === '0000-00-00 00:00:00') return '—';
    return date($format, strtotime($datetime));
}

/**
 * Status badge HTML for views.
 */
function status_badge(string $status): string {
    $s = strtolower($status);
    if (str_contains($s, 'breakdown') || str_contains($s, 'b/d')) {
        return '<span class="badge badge-danger">BREAKDOWN</span>';
    }
    if (str_contains($s, 'offloaded') || str_contains($s, 'completed')) {
        return '<span class="badge badge-success">OFFLOADED</span>';
    }
    if (str_contains($s, 'border') || str_contains($s, 'tunduma') || str_contains($s, 'nakonde')) {
        return '<span class="badge badge-warning">AT BORDER</span>';
    }
    if (str_contains($s, 'enroute') || str_contains($s, 'transit')) {
        return '<span class="badge badge-info">ENROUTE</span>';
    }
    return '<span class="badge badge-secondary">' . htmlspecialchars(strtoupper($status)) . '</span>';
}

/**
 * Alert class if shipment is overdue (>N days in transit).
 */
function overdue_class(int $days, int $threshold = 30): string {
    if ($days > $threshold) return 'table-danger';
    if ($days > ($threshold * 0.75)) return 'table-warning';
    return '';
}
```

---

### 2.5 View — `application/views/reports/client/tracking.php`

```php
<?php defined('BASEPATH') OR exit('No direct script access allowed'); ?>
<!-- Extends your base layout -->
<?php $this->load->view('layouts/header'); ?>

<div class="container-fluid py-4">

    <!-- Page header -->
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h4 class="mb-0">
            <i class="fas fa-truck"></i>
            <?= esc($title) ?>
        </h4>
        <div class="btn-group">
            <a href="<?= site_url('client/reports/tracking/export/excel?' . http_build_query($filters)) ?>"
               class="btn btn-success btn-sm">
                <i class="fas fa-file-excel"></i> Export Excel
            </a>
            <a href="<?= site_url('client/reports/tracking/export/pdf?' . http_build_query($filters)) ?>"
               class="btn btn-danger btn-sm">
                <i class="fas fa-file-pdf"></i> Export PDF
            </a>
        </div>
    </div>

    <!-- Summary cards -->
    <div class="row mb-3">
        <div class="col-md-3">
            <div class="card border-primary">
                <div class="card-body text-center">
                    <h3 class="text-primary"><?= $summary['total'] ?? 0 ?></h3>
                    <small>Total Shipments</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card border-info">
                <div class="card-body text-center">
                    <h3 class="text-info"><?= $summary['in_transit'] ?? 0 ?></h3>
                    <small>In Transit</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card border-warning">
                <div class="card-body text-center">
                    <h3 class="text-warning"><?= $summary['at_border'] ?? 0 ?></h3>
                    <small>At Border</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card border-success">
                <div class="card-body text-center">
                    <h3 class="text-success"><?= $summary['completed'] ?? 0 ?></h3>
                    <small>Completed</small>
                </div>
            </div>
        </div>
    </div>

    <!-- Filters -->
    <div class="card mb-3">
        <div class="card-body py-2">
            <form method="get" class="form-inline">
                <label class="mr-2">From:</label>
                <input type="date" name="date_from" class="form-control form-control-sm mr-3"
                       value="<?= esc($filters['date_from']) ?>">
                <label class="mr-2">To:</label>
                <input type="date" name="date_to" class="form-control form-control-sm mr-3"
                       value="<?= esc($filters['date_to']) ?>">
                <label class="mr-2">Direction:</label>
                <select name="direction" class="form-control form-control-sm mr-3">
                    <option value="">All</option>
                    <option value="NB" <?= $filters['direction']==='NB'?'selected':'' ?>>North Bound (Import)</option>
                    <option value="SB" <?= $filters['direction']==='SB'?'selected':'' ?>>South Bound (Export)</option>
                </select>
                <button type="submit" class="btn btn-primary btn-sm">Filter</button>
            </form>
        </div>
    </div>

    <!-- Report Table -->
    <div class="card">
        <div class="card-body p-0">
            <div class="table-responsive">
                <table class="table table-sm table-bordered table-hover mb-0" id="trackingTable">
                    <thead class="thead-dark">
                        <tr>
                            <th>#</th>
                            <th>TRUCK</th>
                            <th>TRAILER</th>
                            <th>DRIVER</th>
                            <th>PRODUCT</th>
                            <th>BL / LOT</th>
                            <th>DIR</th>
                            <th>LOADING</th>
                            <th>DISPATCH</th>
                            <th>TUNDUMA ↓</th>
                            <th>TUNDUMA ↑</th>
                            <th>NAKONDE ↓</th>
                            <th>K-LESA DRC ↓</th>
                            <th>DESTINATION ↓</th>
                            <th>OFFLOADED</th>
                            <th>DAYS</th>
                            <th>STATUS</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php if (empty($shipments)): ?>
                            <tr>
                                <td colspan="17" class="text-center text-muted py-4">
                                    No shipments found for the selected filters.
                                </td>
                            </tr>
                        <?php else: ?>
                            <?php foreach ($shipments as $i => $s): ?>
                                <?php $days = report_days_diff($s['loading_date'], $s['offloaded_date']); ?>
                                <tr class="<?= overdue_class($days) ?>">
                                    <td><?= $i + 1 ?></td>
                                    <td class="font-weight-bold"><?= esc($s['truck_reg']) ?></td>
                                    <td><?= esc($s['trailer_1'] ?? '') ?><?= $s['trailer_2'] ? '<br><small>'.esc($s['trailer_2']).'</small>' : '' ?></td>
                                    <td><?= esc($s['driver_name']) ?></td>
                                    <td><?= esc($s['product'] ?? '') ?></td>
                                    <td><small><?= esc($s['bl_number'] ?? '') ?><br><?= esc($s['lot_number'] ?? '') ?></small></td>
                                    <td><?= esc($s['direction'] ?? '') ?></td>
                                    <td><?= rpt_date($s['loading_date']) ?></td>
                                    <td><?= rpt_date($s['dispatch_date']) ?></td>
                                    <td><?= rpt_date($s['tunduma_arrival']) ?></td>
                                    <td><?= rpt_date($s['tunduma_dispatch']) ?></td>
                                    <td><?= rpt_date($s['nakonde_arrival']) ?></td>
                                    <td><?= rpt_date($s['kasumbalesa_drc_arrival']) ?></td>
                                    <td><?= rpt_date($s['destination_arrival']) ?></td>
                                    <td><?= rpt_date($s['offloaded_date']) ?></td>
                                    <td class="text-center <?= $days > 30 ? 'text-danger font-weight-bold' : '' ?>">
                                        <?= $days ?: '—' ?>
                                    </td>
                                    <td><?= status_badge($s['status'] ?? $s['remarks'] ?? '') ?></td>
                                </tr>
                            <?php endforeach; ?>
                        <?php endif; ?>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<!-- DataTables for sorting -->
<script>
$(document).ready(function() {
    $('#trackingTable').DataTable({
        paging: false,
        info: false,
        searching: true,
        order: [[7, 'desc']] // sort by loading date desc
    });
});
</script>
<?php $this->load->view('layouts/footer'); ?>
```

---

## 3. PHASE 2: NB/SB & MASTER REPORTS

### 3.1 Controller additions — `application/controllers/reports/Internal_report.php`

```php
<?php
class Internal_report extends CI_Controller {

    public function __construct() {
        parent::__construct();
        $this->require_role(['ops', 'manager', 'admin']); // your auth check
        $this->load->model('reports/Shipment_report_model', 'report_model');
        $this->load->library('Report_exporter');
        $this->load->helper('report_helper');
    }

    /** NB/SB Tracking — all clients */
    public function nb_sb() {
        $filters = [
            'date_from'  => $this->input->get('date_from') ?: date('Y-m-01'),
            'date_to'    => $this->input->get('date_to')   ?: date('Y-m-t'),
            'direction'  => $this->input->get('direction'),
            'client_id'  => $this->input->get('client_id'),
        ];
        $data = [
            'title'     => 'NB & SB Tracking Report',
            'shipments' => $this->report_model->get_all_shipments_nb_sb($filters),
            'filters'   => $filters,
            'clients'   => $this->report_model->get_all_clients_list(),
        ];
        $this->load->view('reports/internal/nb_sb', $data);
    }

    /** Master Report — date-column grid */
    public function master() {
        $date_from = $this->input->get('date_from') ?: date('Y-m-d', strtotime('-60 days'));
        $date_to   = $this->input->get('date_to')   ?: date('Y-m-d');
        $data = [
            'title'     => 'Master Daily Tracking Report',
            'shipments' => $this->report_model->get_master_report_data($date_from, $date_to),
            'date_from' => $date_from,
            'date_to'   => $date_to,
            'date_cols' => $this->_build_date_columns($date_from, $date_to),
        ];
        $this->load->view('reports/internal/master', $data);
    }

    private function _build_date_columns(string $from, string $to): array {
        $cols = [];
        $d = new DateTime($from);
        $end = new DateTime($to);
        while ($d <= $end) {
            $cols[] = $d->format('Y-m-d');
            $d->modify('+1 day');
        }
        return $cols;
    }

    /** Master In-Transit Report */
    public function in_transit() {
        $data = [
            'title'     => 'Master In-Transit Report',
            'shipments' => $this->report_model->get_all_shipments_nb_sb([
                'date_from' => date('Y-m-d', strtotime('-365 days')),
                'date_to'   => date('Y-m-d'),
            ]),
        ];
        // Filter to only active/non-completed
        $data['shipments'] = array_filter($data['shipments'], function($s) {
            return empty($s['offloaded_date'])
                && !str_contains(strtolower($s['status'] ?? ''), 'completed');
        });
        $this->load->view('reports/internal/in_transit', $data);
    }

    /** Border Snapshot */
    public function border() {
        $checkpoint = $this->input->get('checkpoint') ?: 'tunduma';
        $direction  = $this->input->get('direction');
        $data = [
            'title'      => strtoupper($checkpoint) . ' Border Report',
            'trucks'     => $this->report_model->get_border_snapshot($checkpoint, $direction),
            'checkpoint' => $checkpoint,
            'direction'  => $direction,
        ];
        $this->load->view('reports/internal/border', $data);
    }

    /** Breakdown Report */
    public function breakdown() {
        $filters = [
            'date_from' => $this->input->get('date_from') ?: date('Y-m-01'),
            'date_to'   => $this->input->get('date_to')   ?: date('Y-m-t'),
            'status'    => $this->input->get('status'),
        ];
        $data = [
            'title'      => 'Breakdown / Incident Report',
            'breakdowns' => $this->report_model->get_breakdowns($filters),
            'filters'    => $filters,
        ];
        $this->load->view('reports/internal/breakdown', $data);
    }

    /** Police Fine Report */
    public function police_fine() {
        $filters = [
            'date_from'  => $this->input->get('date_from') ?: date('Y-m-01'),
            'date_to'    => $this->input->get('date_to')   ?: date('Y-m-t'),
            'vehicle_id' => $this->input->get('vehicle_id'),
        ];
        $data = [
            'title'   => 'Police Fine Report',
            'fines'   => $this->report_model->get_police_fines($filters),
            'totals'  => $this->report_model->get_police_fine_totals($filters),
            'filters' => $filters,
        ];
        $this->load->view('reports/internal/police_fine', $data);
    }

    /** Offloading & Mines */
    public function offloading_mines() {
        $data = array_merge(
            ['title' => 'Offloading & Mines Summary'],
            $this->report_model->get_offloading_mines_report()
        );
        $this->load->view('reports/internal/offloading_mines', $data);
    }

    /** POD Master */
    public function pod_master() {
        $filters = [
            'date_from'  => $this->input->get('date_from') ?: date('Y-m-01'),
            'date_to'    => $this->input->get('date_to')   ?: date('Y-m-t'),
            'pod_status' => $this->input->get('pod_status'),
            'client_id'  => $this->input->get('client_id'),
        ];
        $data = [
            'title'   => 'POD Master Report',
            'records' => $this->report_model->get_pod_master($filters),
            'filters' => $filters,
        ];
        $this->load->view('reports/internal/pod_master', $data);
    }
}
```

---

## 4. PHASE 3: BORDER, FINANCIAL, POD, BREAKDOWN

*(See model methods above — views follow same pattern as client tracking view)*

### Demurrage calculation logic (in model or helper):

```php
function calculate_demurrage(DateTime $arrival, ?DateTime $departure, int $free_days, float $rate): array {
    $to = $departure ?? new DateTime();
    $total = max(0, (int)$arrival->diff($to)->days);
    $chargeable = max(0, $total - $free_days);
    return [
        'total_days'      => $total,
        'free_days'       => $free_days,
        'chargeable_days' => $chargeable,
        'amount_usd'      => round($chargeable * $rate, 2),
    ];
}
```

---

## 5. PHASE 4: LIVE GPS & OFFLINE REPORTS

```php
/** GPS Master in Internal_report controller */
public function gps_master() {
    // Subquery: latest ping per vehicle
    $sub = $this->db->select('vehicle_id, MAX(pinged_at) AS last_ping', FALSE)
                    ->from('gps_pings')
                    ->group_by('vehicle_id')
                    ->get_compiled_select();

    $this->db->select('v.truck_reg, gp.latitude, gp.longitude, gp.location_name, gp.speed_kmh, gp.pinged_at, vas.driver_name, vas.client_name, vas.status');
    $this->db->from("({$sub}) latest");
    $this->db->join('gps_pings gp', 'gp.vehicle_id = latest.vehicle_id AND gp.pinged_at = latest.last_ping');
    $this->db->join('vehicles v', 'v.id = gp.vehicle_id');
    $this->db->join('v_active_shipments vas', 'vas.vehicle_id = gp.vehicle_id', 'left');
    $pings = $this->db->get()->result_array();

    $threshold = date('Y-m-d H:i:s', strtotime('-12 hours'));
    $data = [
        'title'   => 'GPS Master Report',
        'active'  => array_filter($pings, fn($p) => $p['pinged_at'] >= $threshold),
        'offline' => array_filter($pings, fn($p) => $p['pinged_at'] < $threshold),
    ];
    $this->load->view('reports/internal/gps_master', $data);
}
```

---

## 6. SHARED INFRASTRUCTURE

### Composer Dependencies

```json
{
    "require": {
        "phpoffice/phpspreadsheet": "^2.0",
        "dompdf/dompdf": "^2.0"
    }
}
```

Run: `composer install` from CI root.

### CI Routes — `application/config/routes.php`

```php
// Client report routes
$route['client/reports/tracking']              = 'reports/Client_report/tracking';
$route['client/reports/tracking/export/excel'] = 'reports/Client_report/export_excel';
$route['client/reports/tracking/export/pdf']   = 'reports/Client_report/export_pdf';
$route['client/reports/demurrage']             = 'reports/Client_report/demurrage';
$route['client/reports/pod']                   = 'reports/Client_report/pod';

// Internal report routes
$route['internal/reports/nb-sb']              = 'reports/Internal_report/nb_sb';
$route['internal/reports/master']             = 'reports/Internal_report/master';
$route['internal/reports/in-transit']         = 'reports/Internal_report/in_transit';
$route['internal/reports/border']             = 'reports/Internal_report/border';
$route['internal/reports/breakdown']          = 'reports/Internal_report/breakdown';
$route['internal/reports/police-fine']        = 'reports/Internal_report/police_fine';
$route['internal/reports/offloading-mines']   = 'reports/Internal_report/offloading_mines';
$route['internal/reports/pod-master']         = 'reports/Internal_report/pod_master';
$route['internal/reports/gps']               = 'reports/Internal_report/gps_master';
$route['internal/reports/demurrage']         = 'reports/Internal_report/demurrage';
```

---

## 7. CLIENT DASHBOARD SIDEBAR MENU

```php
// In client layout sidebar
<?php if ($this->session->userdata('role') === 'client'): ?>
<li class="nav-item">
    <a href="<?= site_url('client/reports/tracking') ?>" class="nav-link">
        <i class="fas fa-map-marked-alt"></i> My Tracking Report
    </a>
</li>
<li class="nav-item">
    <a href="<?= site_url('client/reports/demurrage') ?>" class="nav-link">
        <i class="fas fa-calculator"></i> Demurrage Report
    </a>
</li>
<li class="nav-item">
    <a href="<?= site_url('client/reports/pod') ?>" class="nav-link">
        <i class="fas fa-file-signature"></i> POD Status
    </a>
</li>
<?php endif; ?>
```

---

## IMPLEMENTATION CHECKLIST

### Phase 1 — Client Report
- [ ] Install PhpSpreadsheet via Composer
- [ ] Create `v_active_shipments` database view
- [ ] Create/verify `shipment_milestones` table exists
- [ ] Create `Report_exporter.php` library
- [ ] Create `report_helper.php` helper
- [ ] Create `Shipment_report_model.php`
- [ ] Create `Client_report.php` controller
- [ ] Create `views/reports/client/tracking.php`
- [ ] Create `views/reports/client/demurrage.php`
- [ ] Create `views/reports/client/pod.php`
- [ ] Add routes to `routes.php`
- [ ] Add sidebar links to client layout
- [ ] Test with sample client data
- [ ] Test Excel export download
- [ ] Test PDF export download

### Phase 2 — Internal Reports
- [ ] Create `Internal_report.php` controller
- [ ] Create `views/reports/internal/nb_sb.php`
- [ ] Create `views/reports/internal/master.php` (date-grid view)
- [ ] Create `views/reports/internal/in_transit.php`
- [ ] Extend `Shipment_report_model.php` with internal queries

### Phase 3 — Financial/Border
- [ ] Create `demurrage_records` table
- [ ] Create `police_fines` table
- [ ] Add `daily_locations` table
- [ ] Create breakdown, fine, POD, border views
- [ ] Add demurrage calculation helper

### Phase 4 — GPS/Live
- [ ] Create `gps_pings` table
- [ ] GPS integration (API or device webhook)
- [ ] GPS master and offline views
