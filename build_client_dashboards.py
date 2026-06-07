#!/usr/bin/env python3
"""
QiBi Client Dashboard Builder v2 — Sales + Wastage
KEY FIX: Aggregates by VENUE per transaction (not fridge with static mapping).
Fridges move between venues over time — each transaction's venue is used as-is.

Processes 5 input files, outputs dashboard_data.json for HTML dashboards.
"""
import csv
import io
import json
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

# ============================================================
# CONFIG
# ============================================================
SALES_FILE = "mnt/uploads/1-All_machine_Sales_Report_30_12_2024_to_31_05_2026_on_07_06_2026_05_01_04.csv"
STOCK_VL_FILE = "mnt/uploads/1-All_machine_Stock_Movements_Report_29_12_2024_to_01_06_2026_on_07_06_2026_18_46_04.csv"
CRYO_SALES_FILE = "mnt/uploads/3593 - 2026-06-07T061913.756.csv"
CRYO_STOCK_FILE = "mnt/uploads/5435 (11).csv"
MELBA_FILE = "mnt/uploads/melba_recipes_2026-05-21.csv"

# BoostBar (account 188) — separate CSV exports, same VendLive format, NO EPC/RFID
# Set to "" to skip if not available
BOOST_SALES_FILE = "mnt/uploads/BoostBar_Greentime_Sales_Report_30_12_2024_to_31_05_2026_on_07_06_2026_04_23_05.csv"
BOOST_STOCK_FILE = "mnt/uploads/BoostBar_Greentime_Stock_Movements_Report_28_12_2025_to_01_06_2026_on_07_06_2026_18_11_12.csv"

# SKU fix mapping
SKU_FIXES = {'COl12':'COL12','COL2':'COL02','SU14':'SOU14','PDT3':'PTD03','PDT13':'PTD13','PDT11':'PTD11','PTD6':'PTD06'}

# Venues to EXCLUDE from dashboards
EXCLUDED_VENUES = {
    "STORAGE GE", "STORAGE ZH", "SNACKS Rotation ZH",
    "SPARE STORAGE GE (ex Migros Frigo 2)", "SPARE TEST OFFICE GE 2025",
    "CRYOWerx TEST FRIDGE GE", "PAVE SPACE"
}

# Also exclude specific fridge IDs (their venue may change)
EXCLUDED_MACHINES = {"AEG-SF-GT-073"}

def is_excluded(venue, fridge=""):
    """Check if a venue or fridge should be excluded"""
    if fridge in EXCLUDED_MACHINES:
        return True
    v_upper = venue.upper().strip()
    for excl in EXCLUDED_VENUES:
        if excl.upper() == v_upper:
            return True
    if "STORAGE" in v_upper or "TEST" in v_upper or "SPARE" in v_upper:
        return True
    return False

# Category mapping (SKU prefix → specific category)
def get_sub_category(sku):
    prefix = "".join(c for c in sku if c.isalpha())
    mapping = {
        "PLT": "Hot Dishes", "SOU": "Soups",
        "SAL": "Salads & Bowls", "WRA": "Sandwiches & Wraps",
        "DES": "Desserts", "PTD": "Breakfast", "COL": "Cold Dishes",
        "ENT": "Starters",
        "SNK": "Sweet Snacks", "SNKS": "Savoury Snacks",
        "DRK": "Drinks", "YOG": "Yogurts", "OTH": "Other"
    }
    return mapping.get(prefix, "Other")

# Cryo category → standard
CRYO_CAT_MAP = {
    "Plats chauds": "Hot Dishes", "Desserts": "Desserts",
    "Salades": "Salads & Bowls", "Sandwichs": "Sandwiches & Wraps",
    "Wraps": "Sandwiches & Wraps", "Poke Bowls": "Salads & Bowls",
    "Petits-déjeuners": "Breakfast", "Soupes": "Soups",
    "Bagels": "Sandwiches & Wraps", "Collations": "Cold Dishes",
    "Boissons": "Drinks", "Snacks": "Sweet Snacks", "SWEET": "Sweet Snacks"
}


# Full COGS table (from CLAUDE.md + new SKUs)
COGS = {
    "COL02":4.09,"COL11":2.20,"COL12":2.79,"COL13":1.84,"COL14":2.20,"COL15":1.96,
    "COL16":2.00,"COL17":1.26,"COL18":1.83,"COL19":2.01,"COL23":1.94,"COL24":2.20,
    "COL26":2.11,"COL28":2.39,
    "DES01":1.18,"DES02":3.68,"DES03":3.06,"DES04":1.61,"DES06":2.95,"DES13":2.46,
    "DES15":1.58,"DES17":2.44,"DES18":2.27,"DES19":2.15,"DES20":2.15,"DES22":2.15,
    "DES24":1.61,"DES31":1.70,"DES33":1.96,"DES34":1.41,"DES38":2.39,"DES39":1.35,
    "DES40":2.15,"DES41":1.91,"DES42":2.15,"DES43":2.15,"DES50":2.15,"DES51":2.15,"DES52":2.91,
    "ENT19":0.91,
    "PLT01":4.04,"PLT02":2.02,"PLT04":3.51,"PLT07":1.80,"PLT101":4.24,"PLT102":3.97,
    "PLT104":4.07,"PLT11":3.51,"PLT110":3.34,"PLT111":3.26,"PLT112":3.51,"PLT114":2.96,
    "PLT116":3.51,"PLT119":3.51,"PLT12":2.49,"PLT121":4.55,"PLT123":3.51,"PLT125":5.07,
    "PLT13":2.52,"PLT15":3.32,"PLT16":4.38,"PLT17":2.43,"PLT22":2.22,"PLT24":3.00,
    "PLT27":2.56,"PLT28":3.06,"PLT29":2.59,"PLT34":4.28,"PLT35":3.66,"PLT36":2.40,
    "PLT37":3.25,"PLT39":1.71,"PLT40":3.28,"PLT42":2.36,"PLT44":3.45,"PLT45":4.70,
    "PLT46":5.19,"PLT48":3.58,"PLT49":3.29,"PLT53":3.30,"PLT56":4.57,"PLT58":4.47,
    "PLT59":2.91,"PLT62":3.63,"PLT63":3.97,"PLT64":2.40,"PLT65":3.79,"PLT68":2.65,
    "PLT69":4.09,"PLT71":3.50,"PLT72":4.52,"PLT75":3.12,"PLT76":5.35,"PLT77":2.92,
    "PLT78":2.11,"PLT79":3.97,"PLT80":6.68,"PLT81":3.64,"PLT82":3.55,"PLT90":3.04,
    "PLT91":3.90,"PLT92":4.34,"PLT93":3.80,"PLT94":4.32,"PLT95":6.55,"PLT96":3.70,
    "PLT98":3.83,"PLT99":2.85,
    "PTD01":1.40,"PTD02":1.02,"PTD03":1.96,"PTD04":1.43,"PTD05":1.19,"PTD06":1.27,
    "PTD07":1.82,"PTD10":1.24,"PTD11":1.30,"PTD12":1.69,"PTD13":1.60,"PTD14":1.52,
    "PTD19":1.74,"PTD20":1.64,"PTD21":1.75,"PTD22":1.38,"PTD23":0.94,"PTD24":0.73,
    "PTD25":0.90,"PTD26":1.18,"PTD27":1.18,"PTD28":1.25,
    "SAL02":3.55,"SAL03":2.83,"SAL04":3.02,"SAL05":3.60,"SAL06":3.26,"SAL07":3.26,
    "SAL09":2.85,"SAL13":4.40,"SAL15":3.46,"SAL16":4.24,"SAL17":3.49,"SAL19":2.76,
    "SAL23":4.36,"SAL24":4.02,"SAL25":2.97,"SAL26":3.54,"SAL27":3.72,"SAL28":3.69,
    "SAL29":3.75,"SAL30":3.38,"SAL32":2.70,"SAL33":2.51,"SAL34":3.08,"SAL35":3.35,
    "SAL37":2.69,"SAL38":2.00,"SAL39":3.16,"SAL40":3.02,"SAL41":3.14,"SAL42":3.01,
    "SAL47":4.48,"SAL48":3.51,"SAL49":2.40,"SAL50":3.12,"SAL52":3.99,"SAL53":2.62,"SAL54":3.63,
    "SOU10":2.28,"SOU11":3.11,"SOU12":1.33,"SOU13":1.34,"SOU14":1.74,"SOU15":5.00,
    "WRA01":2.94,"WRA02":4.07,"WRA04":3.08,"WRA09":2.58,"WRA12":3.05,"WRA13":3.53,
    "WRA15":3.38,"WRA16":4.24,"WRA17":3.60,"WRA19":2.75,"WRA25":3.60,"WRA26":3.48,
    "WRA27":2.94,"WRA28":3.21,"WRA30":3.07,"WRA31":3.95,"WRA32":3.24,"WRA33":3.43,
    "WRA35":2.45,"WRA36":3.04,"WRA37":2.79,"WRA38":3.79,"WRA39":3.57,"WRA40":3.32,
    "WRA42":2.21,"WRA43":2.60,"WRA44":2.67,"WRA45":3.09,"WRA46":3.29,"WRA47":3.74,
    "WRA49":3.68,"WRA51":3.24,"WRA53":3.24,"WRA55":3.24,
}


def get_week_key(dt):
    """ISO week key as 'YYYY-WNN'"""
    iso = dt.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"

def parse_vl_date(s):
    """Parse VendLive date formats"""
    s = s.strip()
    for fmt in ("%d.%m.%Y %H:%M", "%d/%m/%Y %H:%M", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except:
            continue
    return None

# ============================================================
# STEP 1: PROCESS SALES — venue from each transaction row
# Filter 1: skip rows where is_refunded has any value (autorefund or manual)
# Filter 2: EPC dedup — all tags are single-use; if same EPC appears in
#   multiple non-refunded rows, keep only the LATEST sale, discard earlier ones
# ============================================================
print("Step 1: Processing sales...")
sales_data = []
refund_skipped = 0

# Two-pass approach: first collect all non-refunded rows with parsed data,
# then deduplicate EPCs keeping latest timestamp
pending_rows = []  # (dt, week, venue, sku, name, sub_cat, price, tag_id)

with open(SALES_FILE, "r", encoding="utf-8-sig") as f:
    content = f.read().lstrip('\n\r')  # strip leading blank lines
with io.StringIO(content) as f:
    for row in csv.DictReader(f):
        refund_val = row.get("is_refunded","").strip()
        if refund_val:  # any non-empty value = refunded, skip
            refund_skipped += 1
            continue

        vend_status = row.get("vend_status","").strip()
        if vend_status and vend_status != "Success":
            refund_skipped += 1  # count with refunds as filtered-out
            continue

        ts = row.get("timestamp","").strip()
        dt = parse_vl_date(ts)
        if not dt:
            continue

        sku = row.get("product__external_id","").strip()
        sku = SKU_FIXES.get(sku, sku)
        name = row.get("name","").strip()
        fridge = row.get("machine__friendly_name","").strip()
        venue = row.get("location__venue__name","").strip()

        if is_excluded(venue, fridge):
            continue

        price_str = row.get("price","0").replace(",",".")
        try:
            price = float(price_str)
        except:
            price = 0

        week = get_week_key(dt)
        sub_cat = get_sub_category(sku)
        tag_id = row.get("item_tag_id","").strip()

        pending_rows.append((dt, week, venue, sku, name, sub_cat, price, tag_id))

# EPC dedup: for each EPC with multiple rows, keep only the LATEST (by timestamp)
# Rows without EPC (empty or "-") pass through as-is
epc_latest = {}  # tag_id → index in pending_rows (latest dt wins)
no_epc_rows = []
epc_dupes_discarded = 0

for i, (dt, week, venue, sku, name, sub_cat, price, tag_id) in enumerate(pending_rows):
    if not tag_id or tag_id == "-":
        no_epc_rows.append(i)
    else:
        if tag_id in epc_latest:
            prev_i = epc_latest[tag_id]
            prev_dt = pending_rows[prev_i][0]
            if dt > prev_dt:
                # Current is newer — replace, discard previous
                epc_latest[tag_id] = i
            # else: current is older — discard current
            epc_dupes_discarded += 1
        else:
            epc_latest[tag_id] = i

# Build final sales_data from kept rows
kept_indices = set(no_epc_rows) | set(epc_latest.values())
for i in sorted(kept_indices):
    dt, week, venue, sku, name, sub_cat, price, tag_id = pending_rows[i]
    sales_data.append((week, venue, sku, name, sub_cat, price, 1))

print(f"  VendLive sales loaded: {len(sales_data):,} clean transactions")
print(f"  Refunds skipped: {refund_skipped:,}")
print(f"  EPC dupes discarded (earlier sales): {epc_dupes_discarded:,} ({len(epc_latest):,} unique EPCs)")

# Also process Cryo sales (3593) — location IS the venue
with open(CRYO_SALES_FILE, "r", encoding="utf-8-sig") as f:
    cryo_sales_count = 0
    for row in csv.DictReader(f):
        location = row.get("Location","").strip()
        if is_excluded(location):
            continue

        ts = row.get("DateTime (CET)","").strip()
        dt = parse_vl_date(ts)
        if not dt:
            continue

        sku = row.get("SKU","").strip()
        sku = SKU_FIXES.get(sku, sku)
        name = row.get("Product","").strip()
        cryo_cat = row.get("Category","").strip()

        price_str = row.get("Price","0").replace(",",".")
        try:
            price = float(price_str)
        except:
            price = 0

        week = get_week_key(dt)
        sub_cat = CRYO_CAT_MAP.get(cryo_cat, get_sub_category(sku))

        # Cryo: location IS the venue
        sales_data.append((week, location, sku, name, sub_cat, price, 1))
        cryo_sales_count += 1

print(f"  Cryo sales added: {cryo_sales_count:,}")

# ============================================================
# STEP 1.5: PROCESS BOOSTBAR SALES (Account 188)
# Same VendLive CSV format — Tag ID always "-" (no RFID).
# vend_status filter handles errors; no EPC dedup needed.
# ============================================================
if BOOST_SALES_FILE and os.path.exists(BOOST_SALES_FILE):
    print("\nStep 1.5: Processing BoostBar sales...")
    boost_sales_count = 0
    boost_refund_skipped = 0

    with open(BOOST_SALES_FILE, "r", encoding="utf-8-sig") as f:
        _boost_content = f.read().lstrip('\n\r')
    with io.StringIO(_boost_content) as f:
        for row in csv.DictReader(f):
            refund_val = row.get("is_refunded","").strip()
            if refund_val:
                boost_refund_skipped += 1
                continue

            vend_status = row.get("vend_status","").strip()
            if vend_status and vend_status != "Success":
                boost_refund_skipped += 1
                continue

            ts = row.get("timestamp","").strip()
            dt = parse_vl_date(ts)
            if not dt:
                continue

            sku = row.get("product__external_id","").strip()
            sku = SKU_FIXES.get(sku, sku)
            name = row.get("name","").strip()
            fridge = row.get("machine__friendly_name","").strip()
            venue = row.get("location__venue__name","").strip()

            if is_excluded(venue, fridge):
                continue

            price_str = row.get("price","0").replace(",",".")
            try:
                price = float(price_str)
            except:
                price = 0

            week = get_week_key(dt)
            sub_cat = get_sub_category(sku)

            # No EPC dedup for BoostBar — Tag ID is always "-"
            sales_data.append((week, venue, sku, name, sub_cat, price, 1))
            boost_sales_count += 1

    print(f"  BoostBar sales added: {boost_sales_count:,}")
    print(f"  BoostBar refunds/errors skipped: {boost_refund_skipped:,}")
else:
    if BOOST_SALES_FILE:
        print(f"\nStep 1.5: BoostBar sales file not found: {BOOST_SALES_FILE} — skipping")
    else:
        print("\nStep 1.5: No BoostBar sales file configured — skipping")

print(f"  Total sales: {len(sales_data):,}")

# ============================================================
# STEP 2: PROCESS STOCK MOVEMENTS (VendLive) — venue per row
# ============================================================
print("\nStep 2: Processing VendLive stock movements...")

# First pass: load and sort by datetime for global EPC dedup
stock_rows = []
with open(STOCK_VL_FILE, "r", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        ts = row.get("Created at","").strip()
        dt = parse_vl_date(ts)
        if not dt:
            continue
        stock_rows.append((dt, row))

stock_rows.sort(key=lambda x: x[0])

# Process sorted rows — use per-row Venue, not fridge mapping
# intro/waste: (week, venue, product_name, product_id, sub_cat, units)
intro_data = []
waste_data = []
epc_intro_week = {}  # EPC → intro week for backtracing
epc_all_intro_dts = defaultdict(list)  # EPC → [datetime, ...] ALL intro timestamps (for re-intro check)

for dt, row in stock_rows:
    typ = row.get("Type","").strip()
    fridge = row.get("Machine (Friendly Name)","").strip()
    venue = row.get("Venue","").strip()  # PER-ROW VENUE — the fix
    product_name = row.get("Product (Name)","").strip()
    product_id = row.get("Product (ID)","").strip()
    vl_cat = row.get("Category (Name)","").strip()
    epc = row.get("Tag ID","").strip()
    qty = abs(int(row.get("Quantity","0") or "0"))

    if not product_name or not venue:
        continue

    if is_excluded(venue, fridge):
        continue

    # Map VendLive category to specific sub-category
    vl_cat_map = {
        "Hot": "Hot Dishes",
        "Cold": "Salads & Bowls",
        "Desserts": "Desserts",
        "Sweet Snacks": "Sweet Snacks",
        "Savory Snacks": "Savoury Snacks",
        "Drinks": "Drinks",
        "New in the fridge": "Hot Dishes",
        "Salades": "Salads & Bowls",
    }

    sub_cat = vl_cat_map.get(vl_cat, "Other")
    week = get_week_key(dt)

    if typ in ("In", "Add", "Found"):
        if epc and epc != "-":
            epc_all_intro_dts[epc].append(dt)  # track ALL intro timestamps
            if epc in epc_intro_week:
                continue  # skip duplicate from intro count
            epc_intro_week[epc] = week
        # KEY: store venue from this row
        intro_data.append((week, venue, product_name, product_id, sub_cat, qty))
    elif typ in ("Wasted", "Remove"):
        waste_data.append((week, venue, product_name, product_id, sub_cat, qty, epc, dt))

print(f"  Introductions: {sum(q for *_,q in intro_data):,} units ({len(intro_data):,} rows)")
print(f"  Wastage (pre-dedup): {sum(e[5] for e in waste_data):,} units ({len(waste_data):,} rows)")
print(f"  Unique EPCs tracked: {len(epc_intro_week):,}")

# ============================================================
# STEP 3: PROCESS CRYO STOCK MOVEMENTS (5435)
# ============================================================
print("\nStep 3: Processing Cryo stock movements...")
cryo_stock_count = 0

with open(CRYO_STOCK_FILE, "r", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        location = row.get("locality","").strip()
        if is_excluded(location):
            continue

        ts = row.get("Action Time","").strip()
        dt = parse_vl_date(ts)
        if not dt:
            continue

        action = row.get("actionType","").strip()
        name = row.get("name","").strip()
        cryo_cat = row.get("Category Name","").strip()
        epc = row.get("epcCode","").strip()

        sub_cat = CRYO_CAT_MAP.get(cryo_cat, "Other")
        week = get_week_key(dt)

        if action == "Add":
            if epc:
                epc_all_intro_dts[epc].append(dt)  # track ALL intro timestamps
                if epc in epc_intro_week:
                    continue  # skip duplicate from intro count
                epc_intro_week[epc] = week
            # Cryo: location IS the venue
            intro_data.append((week, location, name, "", sub_cat, 1))
            cryo_stock_count += 1
        elif action == "Remove":
            waste_data.append((week, location, name, "", sub_cat, 1, epc, dt))

print(f"  Cryo introductions: {cryo_stock_count:,}")

# ============================================================
# STEP 3.5: PROCESS BOOSTBAR STOCK MOVEMENTS (Account 188)
# Same VendLive CSV format — Tag ID always "-" (no RFID).
# Use Quantity column for unit count. No EPC dedup.
# Only In/Add/Found = introductions. Inventory is NOT intro.
# ============================================================
if BOOST_STOCK_FILE and os.path.exists(BOOST_STOCK_FILE):
    print("\nStep 3.5: Processing BoostBar stock movements...")
    boost_intro_count = 0
    boost_waste_count = 0

    boost_stock_rows = []
    with open(BOOST_STOCK_FILE, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            ts = row.get("Created at","").strip()
            dt = parse_vl_date(ts)
            if not dt:
                continue
            boost_stock_rows.append((dt, row))

    boost_stock_rows.sort(key=lambda x: x[0])

    for dt, row in boost_stock_rows:
        typ = row.get("Type","").strip()
        fridge = row.get("Machine (Friendly Name)","").strip()
        venue = row.get("Venue","").strip()
        product_name = row.get("Product (Name)","").strip()
        product_id = row.get("Product (ID)","").strip()
        vl_cat = row.get("Category (Name)","").strip()
        qty = abs(int(row.get("Quantity","0") or "0"))

        if not product_name or not venue:
            continue

        if is_excluded(venue, fridge):
            continue

        # Map VendLive category to specific sub-category
        vl_cat_map = {
            "Hot": "Hot Dishes",
            "Cold": "Salads & Bowls",
            "Desserts": "Desserts",
            "Sweet Snacks": "Sweet Snacks",
            "Savory Snacks": "Savoury Snacks",
            "Drinks": "Drinks",
            "New in the fridge": "Hot Dishes",
            "Salades": "Salads & Bowls",
        }

        sub_cat = vl_cat_map.get(vl_cat, "Other")
        week = get_week_key(dt)

        # No EPC dedup for BoostBar — Tag ID is always "-"
        if typ in ("In", "Add", "Found"):
            intro_data.append((week, venue, product_name, product_id, sub_cat, qty))
            boost_intro_count += qty
        elif typ in ("Wasted", "Remove"):
            waste_data.append((week, venue, product_name, product_id, sub_cat, qty, "", dt))
            boost_waste_count += qty

    print(f"  BoostBar introductions: {boost_intro_count:,} units")
    print(f"  BoostBar wastage: {boost_waste_count:,} units")
else:
    if BOOST_STOCK_FILE:
        print(f"\nStep 3.5: BoostBar stock file not found: {BOOST_STOCK_FILE} — skipping")
    else:
        print("\nStep 3.5: No BoostBar stock file configured — skipping")

# ============================================================
# STEP 3.8: EPC-BASED WASTAGE BACKTRACING + WASTE DEDUP
#
# Logic per EPC:
#   1. If multiple Remove/Wasted events exist, keep only the LAST one.
#      Earlier events are likely RFID misreads (tag still in fridge).
#   2. Check if the item was re-introduced AFTER that last waste event.
#      If yes → the "waste" was a misread, item is still in the fridge → discard.
#      If no  → real waste → proceed.
#   3. For real waste in categories other than Sweet Snacks / Drinks / Savoury Snacks:
#      backtrace to the introduction week (attribute waste to production batch).
#   4. Sweet Snacks / Drinks / Savoury Snacks: keep removal-week attribution.
#   5. No-EPC items (BoostBar) pass through unchanged.
# ============================================================
print("\nStep 3.8: EPC-based wastage backtracing...")

KEEP_REMOVAL_WEEK_CATS = {"Sweet Snacks", "Drinks", "Savoury Snacks"}

# Phase 1: Group waste events by EPC; collect no-EPC items separately
epc_waste_groups = defaultdict(list)  # EPC → [waste_tuple, ...]
no_epc_waste = []

for entry in waste_data:
    w, v, n, pid, sc, qty, epc, dt = entry
    if epc and epc != "-":
        epc_waste_groups[epc].append(entry)
    else:
        no_epc_waste.append(entry)

# Phase 2: For each EPC, keep only the LAST waste event.
# Then check if re-introduced after that last waste → discard if so.
new_waste_data = []
waste_epc_dupes = 0
reintro_discarded = 0
backtraced = 0
no_match = 0
kept_removal = 0

for epc, events in epc_waste_groups.items():
    # Sort by datetime, pick the LAST event
    events.sort(key=lambda e: e[7])  # sort by dt
    waste_epc_dupes += len(events) - 1  # earlier events are misread dupes

    last_event = events[-1]
    w, v, n, pid, sc, qty, _, last_dt = last_event

    # Check if re-introduced AFTER last waste event
    intro_dts = epc_all_intro_dts.get(epc, [])
    reintroduced = any(idt > last_dt for idt in intro_dts)

    if reintroduced:
        # Item was put back / re-scanned after "waste" — not actually wasted
        reintro_discarded += 1
        continue

    # Real waste — apply category-based logic
    if sc in KEEP_REMOVAL_WEEK_CATS:
        new_waste_data.append((w, v, n, pid, sc, qty))
        kept_removal += 1
    elif epc in epc_intro_week:
        # Backtrace to introduction week
        intro_week = epc_intro_week[epc]
        new_waste_data.append((intro_week, v, n, pid, sc, qty))
        if intro_week != w:
            backtraced += 1
    else:
        # EPC not found in intros (pre-data-window) — keep removal week
        new_waste_data.append((w, v, n, pid, sc, qty))
        no_match += 1

# Phase 3: Add no-EPC waste (BoostBar etc.) as-is — strip epc+dt fields
for w, v, n, pid, sc, qty, _, _ in no_epc_waste:
    new_waste_data.append((w, v, n, pid, sc, qty))

waste_data = new_waste_data

print(f"  Unique EPCs with waste events: {len(epc_waste_groups):,}")
print(f"  Earlier misread dupes removed: {waste_epc_dupes:,}")
print(f"  Re-introduced after waste (discarded): {reintro_discarded:,}")
print(f"  Backtraced to intro week: {backtraced:,}")
print(f"  EPCs not in intros (kept removal week): {no_match:,}")
print(f"  Sweet Snacks/Drinks/Savoury kept at removal week: {kept_removal:,}")
print(f"  No-EPC items (BoostBar): {len(no_epc_waste):,}")
print(f"  Final waste records: {len(waste_data):,}")

# ============================================================
# STEP 3.9: TEA CAKES CATEGORY OVERRIDE
# Dashboard-only category — does not exist in source files.
# Remaps specific products from their source category to "Tea Cakes"
# so users can filter them out via category selectors in any dashboard.
# Applied here (post-load, pre-aggregation) to flow through ALL JSONs.
# ============================================================
TEA_CAKE_NAMES = {
    "double trouble chocolate cake",
    "marble cake",
    "lemon & almond cake",
    "lemon and almond cake",
}

def _is_tea_cake(name):
    return name.lower().strip() in TEA_CAKE_NAMES

tc_sales = sum(1 for _, _, _, n, *_ in sales_data if _is_tea_cake(n))
tc_intro = sum(1 for _, _, n, _, *_ in intro_data if _is_tea_cake(n))
tc_waste = sum(1 for _, _, n, _, *_ in waste_data if _is_tea_cake(n))

sales_data = [(w, v, s, n, ("Tea Cakes" if _is_tea_cake(n) else sc), p, u)
              for w, v, s, n, sc, p, u in sales_data]
intro_data = [(w, v, n, pid, ("Tea Cakes" if _is_tea_cake(n) else sc), u)
              for w, v, n, pid, sc, u in intro_data]
waste_data = [(w, v, n, pid, ("Tea Cakes" if _is_tea_cake(n) else sc), u)
              for w, v, n, pid, sc, u in waste_data]

print(f"\nStep 3.9: Tea Cakes override — {tc_sales} sales, {tc_intro} intros, {tc_waste} waste rows remapped")

# ============================================================
# STEP 4: AGGREGATE DATA — all by VENUE, not fridge
# ============================================================
print("\nStep 4: Aggregating by venue...")

# Sales: (week, venue, sku) → detail
sales_product = defaultdict(lambda: {"units":0,"revenue":0.0,"name":"","sub_cat":""})

all_weeks = set()
all_venues = set()

for week, venue, sku, name, sub_cat, price, units in sales_data:
    key = (week, venue, sku)
    sales_product[key]["units"] += units
    sales_product[key]["revenue"] += price
    sales_product[key]["name"] = name
    sales_product[key]["sub_cat"] = sub_cat
    all_weeks.add(week)
    all_venues.add(venue)

# Stock: (week, venue, product_name) → {introduced, wasted}
stock_agg = defaultdict(lambda: {"introduced":0, "wasted":0})

for week, venue, name, pid, sub_cat, qty in intro_data:
    key = (week, venue, name)
    stock_agg[key]["introduced"] += qty
    stock_agg[key]["sub_cat"] = sub_cat
    all_weeks.add(week)
    all_venues.add(venue)

for week, venue, name, pid, sub_cat, qty in waste_data:
    key = (week, venue, name)
    stock_agg[key]["wasted"] += qty
    if "sub_cat" not in stock_agg[key]:
        stock_agg[key]["sub_cat"] = sub_cat
    all_weeks.add(week)
    all_venues.add(venue)

weeks_sorted = sorted(all_weeks)

# Filter excluded venues
venues_filtered = sorted(v for v in all_venues if not is_excluded(v))
excluded = sorted(v for v in all_venues if is_excluded(v))
print(f"  Excluded venues: {len(excluded)} — {excluded}")
print(f"  Active venues: {len(venues_filtered)}")
print(f"  Weeks: {len(weeks_sorted)} ({weeks_sorted[0]} to {weeks_sorted[-1]})")

# ============================================================
# STEP 5: BUILD JSON FOR DASHBOARDS
# ============================================================
print("\nStep 5: Building JSON...")

# --- SALES JSON ---
# Aggregate: venue → week → {units, revenue} + per-category breakdown
sales_by_venue_week = defaultdict(lambda: defaultdict(lambda: {"units":0,"revenue":0.0,"cats":defaultdict(lambda: {"units":0,"revenue":0.0})}))

for (week, venue, sku), data in sales_product.items():
    sc = data["sub_cat"]
    sales_by_venue_week[venue][week]["units"] += data["units"]
    sales_by_venue_week[venue][week]["revenue"] += data["revenue"]
    sales_by_venue_week[venue][week]["cats"][sc]["units"] += data["units"]
    sales_by_venue_week[venue][week]["cats"][sc]["revenue"] += data["revenue"]

# Build venue-level weekly arrays with category breakdowns
venue_sales = {}
for venue in venues_filtered:
    weeks_data = {}
    ytd_units = 0
    ytd_revenue = 0.0
    ytd_cats = defaultdict(lambda: {"u":0,"r":0.0})
    for week in weeks_sorted:
        empty = {"units":0,"revenue":0.0,"cats":{}}
        d = sales_by_venue_week[venue].get(week, empty)
        wk_entry = {"u": d["units"], "r": round(d["revenue"],2)}
        # Add non-zero category breakdowns
        cats_obj = {}
        for cg, cd in d.get("cats", {}).items():
            if cd["units"] > 0:
                cats_obj[cg] = {"u": cd["units"], "r": round(cd["revenue"],2)}
                ytd_cats[cg]["u"] += cd["units"]
                ytd_cats[cg]["r"] += cd["revenue"]
        if cats_obj:
            wk_entry["cats"] = cats_obj
        weeks_data[week] = wk_entry
        ytd_units += d["units"]
        ytd_revenue += d["revenue"]
    ytd_cats_out = {cg: {"u": v["u"], "r": round(v["r"],2)} for cg, v in ytd_cats.items() if v["u"] > 0}
    venue_sales[venue] = {
        "venue": venue,
        "weeks": weeks_data,
        "ytd_u": ytd_units,
        "ytd_r": round(ytd_revenue, 2),
        "ytd_cats": ytd_cats_out
    }

# --- WASTAGE JSON ---
# Build name_to_sku mapping for COGS lookup
name_to_sku = {}
for (week, venue, sku), data in sales_product.items():
    if data["name"] and sku:
        name_to_sku[data["name"]] = sku

stock_name_sku = {
    "Avocado & Halloumi Sandwich":"WRA45","Bœuf bourguignon":"PLT16",
    "Chineese Satay Beef & Rice noodles":"PLT76","Creamy Bean & Roasted Veggie's Salad":"SAL42",
    "Halloumi Poke":"SAL26","Il Tiramisu":"DES34","Linguine sauce forestière":"PLT36",
    "Niçoise Salad":"SAL25","Plum Bircher":"PTD21","Sun Kissed Sandwich":"WRA27",
    "Tarte à la rhubarbe":"DES52","Thaï caramelized pork":"PLT44","Thaï salad":"SAL06",
    "Toblerone Chocolat Mousse":"DES31","Vegetable soup":"SOU12",
    "Veggie Thaï Curry & Soba Noodles":"SOU15","Veggie Thaï Curry Soup":"SOU15",
    "Velouté de chou-fleur":"SOU13","Velouté de potiron":"SOU10",
    "Velouté de topinambour et noisettes":"SOU11","ìl Tiramisu":"DES34",
    "Glazed Cauliflower & Black Rice":"PLT121","French Cordon Bleu":"PLT125",
    "Vegetarian Gyoza & Rice":"PLT119","Pear, Kiwi & Vanilla Crumble":"DES43",
    "Beetroot, Goat cheese and Walnut Quiche":"COL24","Onigirazu Sandwich":"WRA51",
}
name_to_sku.update(stock_name_sku)

CAT_AVG_COGS = {
    "Hot Dishes": 3.51, "Salads & Bowls": 3.31, "Sandwiches & Wraps": 3.24,
    "Desserts": 2.15, "Breakfast": 1.37, "Soups": 2.47, "Cold Dishes": 2.20,
    "Starters": 0.91, "Sweet Snacks": 1.20, "Savoury Snacks": 1.30,
    "Drinks": 1.25, "Tea Cakes": 2.15, "Other": 2.00
}

# Aggregate wastage by venue with category breakdowns
wastage_by_venue_week = defaultdict(lambda: defaultdict(lambda: {"intro":0,"wasted":0,"waste_cost":0.0,"cats":defaultdict(lambda: {"intro":0,"wasted":0,"waste_cost":0.0})}))

for key, data in stock_agg.items():
    week, venue, product_name = key
    intro = data["introduced"]
    wasted = data["wasted"]
    sub_cat = data.get("sub_cat", "Other")

    sku = name_to_sku.get(product_name, "")
    sku = SKU_FIXES.get(sku, sku)
    unit_cost = COGS.get(sku, CAT_AVG_COGS.get(sub_cat, 2.94))
    waste_cost = wasted * unit_cost

    wastage_by_venue_week[venue][week]["intro"] += intro
    wastage_by_venue_week[venue][week]["wasted"] += wasted
    wastage_by_venue_week[venue][week]["waste_cost"] += waste_cost
    wastage_by_venue_week[venue][week]["cats"][sub_cat]["intro"] += intro
    wastage_by_venue_week[venue][week]["cats"][sub_cat]["wasted"] += wasted
    wastage_by_venue_week[venue][week]["cats"][sub_cat]["waste_cost"] += waste_cost

# Build venue-level wastage arrays with category breakdowns
venue_wastage = {}
for venue in venues_filtered:
    weeks_data = {}
    ytd_intro = 0
    ytd_wasted = 0
    ytd_waste_cost = 0.0
    ytd_cats = defaultdict(lambda: {"i":0,"w":0,"c":0.0})
    for week in weeks_sorted:
        empty = {"intro":0,"wasted":0,"waste_cost":0.0,"cats":{}}
        d = wastage_by_venue_week[venue].get(week, empty)
        wk_entry = {
            "i": d["intro"],
            "w": d["wasted"],
            "c": round(d["waste_cost"], 2)
        }
        cats_obj = {}
        for cg, cd in d.get("cats", {}).items():
            if cd["intro"] > 0 or cd["wasted"] > 0:
                cats_obj[cg] = {"i": cd["intro"], "w": cd["wasted"], "c": round(cd["waste_cost"],2)}
                ytd_cats[cg]["i"] += cd["intro"]
                ytd_cats[cg]["w"] += cd["wasted"]
                ytd_cats[cg]["c"] += cd["waste_cost"]
        if cats_obj:
            wk_entry["cats"] = cats_obj
        weeks_data[week] = wk_entry
        ytd_intro += d["intro"]
        ytd_wasted += d["wasted"]
        ytd_waste_cost += d["waste_cost"]

    ytd_cats_out = {cg: {"i": v["i"], "w": v["w"], "c": round(v["c"],2)} for cg, v in ytd_cats.items() if v["i"] > 0}
    venue_wastage[venue] = {
        "venue": venue,
        "weeks": weeks_data,
        "ytd_i": ytd_intro,
        "ytd_w": ytd_wasted,
        "ytd_c": round(ytd_waste_cost, 2),
        "ytd_cats": ytd_cats_out
    }

# --- PRODUCT-LEVEL DATA for filters ---
product_sales_agg = defaultdict(lambda: {"units":0,"revenue":0.0,"sub_cat":"","name":"","sku":""})
for (week, venue, sku), data in sales_product.items():
    key = sku if sku else data["name"]
    product_sales_agg[key]["units"] += data["units"]
    product_sales_agg[key]["revenue"] += data["revenue"]
    product_sales_agg[key]["sub_cat"] = data.get("sub_cat","")
    product_sales_agg[key]["name"] = data["name"]
    product_sales_agg[key]["sku"] = sku

product_wastage_agg = defaultdict(lambda: {"intro":0,"wasted":0,"waste_cost":0.0,"sub_cat":"","name":""})
for key, data in stock_agg.items():
    week, venue, product_name = key
    sub_cat = data.get("sub_cat","Other")
    sku = name_to_sku.get(product_name,"")
    sku = SKU_FIXES.get(sku, sku)
    unit_cost = COGS.get(sku, CAT_AVG_COGS.get(sub_cat, 2.94))

    pkey = sku if sku else product_name
    product_wastage_agg[pkey]["intro"] += data["introduced"]
    product_wastage_agg[pkey]["wasted"] += data["wasted"]
    product_wastage_agg[pkey]["waste_cost"] += data["wasted"] * unit_cost
    product_wastage_agg[pkey]["sub_cat"] = sub_cat
    product_wastage_agg[pkey]["name"] = product_name

products_list = []
for key, d in product_sales_agg.items():
    sku = d.get("sku", key)
    products_list.append({
        "sku": sku,
        "name": d["name"],
        "sub_cat": d["sub_cat"],
        "total_units": d["units"],
        "total_revenue": round(d["revenue"], 2)
    })

products_wastage_list = []
for key, d in product_wastage_agg.items():
    waste_pct = round(d["wasted"] / d["intro"] * 100, 1) if d["intro"] > 0 else 0
    products_wastage_list.append({
        "key": key,
        "name": d["name"],
        "sub_cat": d["sub_cat"],
        "intro": d["intro"],
        "wasted": d["wasted"],
        "waste_pct": waste_pct,
        "waste_cost": round(d["waste_cost"], 2)
    })

# ============================================================
# FINAL JSON OUTPUT
# ============================================================
# NOTE: JSON is now keyed by VENUE (not fridge).
# The "by_fridge" key name is kept for backwards compatibility with the
# HTML builder — it reads DATA.sales.by_fridge / DATA.wastage.by_fridge.
# Each entry's key is now the venue name, and "venue" field = same string.
output = {
    "meta": {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "weeks": weeks_sorted,
        "venues": venues_filtered,
        "total_sales": len(sales_data),
        "categories": sorted(set(d["sub_cat"] for d in product_sales_agg.values() if d["sub_cat"])),
    },
    "sales": {
        "by_fridge": venue_sales,  # keyed by venue name now
        "products": sorted(products_list, key=lambda x: -x["total_units"])
    },
    "wastage": {
        "by_fridge": venue_wastage,  # keyed by venue name now
        "products": sorted(products_wastage_list, key=lambda x: -x["intro"])
    }
}

json_str = json.dumps(output, ensure_ascii=False)
with open("dashboard_data.json", "w") as f:
    f.write(json_str)

print(f"\n=== SUMMARY ===")
print(f"Total clean sales: {len(sales_data):,}")
print(f"Weeks: {len(weeks_sorted)} ({weeks_sorted[0]} → {weeks_sorted[-1]})")
print(f"Venues: {len(venues_filtered)}")
print(f"Products (sales): {len(products_list)}")
print(f"Products (wastage): {len(products_wastage_list)}")
total_revenue = sum(d["ytd_r"] for d in venue_sales.values())
total_intro = sum(d["ytd_i"] for d in venue_wastage.values())
total_wasted = sum(d["ytd_w"] for d in venue_wastage.values())
total_waste_cost = sum(d["ytd_c"] for d in venue_wastage.values())
print(f"Total revenue: CHF {total_revenue:,.0f}")
print(f"Total introduced: {total_intro:,}")
print(f"Total wasted: {total_wasted:,}")
print(f"Wastage %: {total_wasted/total_intro*100:.1f}%")
print(f"Waste cost (COGS): CHF {total_waste_cost:,.0f}")
print(f"\nJSON saved: dashboard_data.json ({len(json_str):,} bytes)")

# ============================================================
# VENUE VALIDATION — print key venues for cross-checking
# ============================================================
print("\n=== VENUE VALIDATION (spot-check) ===")
check_venues = ["Teoxane Meyrin", "Kugler Bimetal", "Syz Genève", "FIFA", "McDonald's SC", "Bloom"]
for v in check_venues:
    if v in venue_sales:
        s = venue_sales[v]
        y25 = sum(w.get("r",0) for wk, w in s["weeks"].items() if wk.startswith("2025"))
        y26 = sum(w.get("r",0) for wk, w in s["weeks"].items() if wk.startswith("2026"))
        print(f"  {v}: 2025=CHF {y25:,.1f}, 2026=CHF {y26:,.1f}, total=CHF {s['ytd_r']:,.1f}")
    else:
        # Try fuzzy
        matches = [k for k in venue_sales if v.lower() in k.lower()]
        if matches:
            for m in matches:
                s = venue_sales[m]
                y25 = sum(w.get("r",0) for wk, w in s["weeks"].items() if wk.startswith("2025"))
                y26 = sum(w.get("r",0) for wk, w in s["weeks"].items() if wk.startswith("2026"))
                print(f"  {m}: 2025=CHF {y25:,.1f}, 2026=CHF {y26:,.1f}, total=CHF {s['ytd_r']:,.1f}")
        else:
            print(f"  {v}: NOT FOUND")

# ============================================================
# STEP 6: GENERATE PERFORMANCE DASHBOARD JSON
# Per-product metrics with weekly breakdowns, matching the
# perf_dashboard_data.json format expected by build_qibi_perf.py
# ============================================================
print("\n=== STEP 6: Generating perf_dashboard_data.json ===")

# Build per-SKU per-week aggregations
# Sales: (week, sku) → {sold, revenue}
perf_sales_pw = defaultdict(lambda: defaultdict(lambda: {"sold":0, "revenue":0.0}))
for (week, venue, sku), data in sales_product.items():
    if not sku:
        continue
    perf_sales_pw[sku][week]["sold"] += data["units"]
    perf_sales_pw[sku][week]["revenue"] += data["revenue"]

# Stock: (week, product_name) → {introduced} — need to map to SKU
perf_intro_pw = defaultdict(lambda: defaultdict(lambda: 0))
for key, data in stock_agg.items():
    week, venue, product_name = key
    sku = name_to_sku.get(product_name, "")
    sku = SKU_FIXES.get(sku, sku)
    if not sku:
        continue
    perf_intro_pw[sku][week] += data["introduced"]

# Location × product: (venue, sku) → {introduced, sold, revenue}
loc_product = defaultdict(lambda: defaultdict(lambda: {"introduced":0, "sold":0, "revenue":0.0}))
for (week, venue, sku), data in sales_product.items():
    if not sku:
        continue
    loc_product[venue][sku]["sold"] += data["units"]
    loc_product[venue][sku]["revenue"] += data["revenue"]

for key, data in stock_agg.items():
    week, venue, product_name = key
    sku = name_to_sku.get(product_name, "")
    sku = SKU_FIXES.get(sku, sku)
    if not sku:
        continue
    loc_product[venue][sku]["introduced"] += data["introduced"]

# All unique SKUs across both sales and stock
all_skus = sorted(set(list(perf_sales_pw.keys()) + list(perf_intro_pw.keys())))

# Per-product aggregation
perf_products = []
for sku in all_skus:
    # Total across all weeks
    total_intro = sum(perf_intro_pw[sku].values())
    total_sold = sum(d["sold"] for d in perf_sales_pw[sku].values())
    total_revenue = sum(d["revenue"] for d in perf_sales_pw[sku].values())
    total_wasted = max(0, total_intro - total_sold)

    # Weeks on menu: weeks with ≥30 introductions
    weeks_on_menu = sum(1 for w in weeks_sorted if perf_intro_pw[sku].get(w, 0) >= 30)
    participation_pct = round(weeks_on_menu / len(weeks_sorted) * 100, 1) if weeks_sorted else 0

    # Averages (per production week, not calendar week)
    avg_intro_wk = round(total_intro / weeks_on_menu, 1) if weeks_on_menu > 0 else 0
    avg_sold_wk = round(total_sold / weeks_on_menu, 1) if weeks_on_menu > 0 else 0
    avg_wasted_wk = round(total_wasted / weeks_on_menu, 1) if weeks_on_menu > 0 else 0

    wastage_pct = round(total_wasted / total_intro * 100, 1) if total_intro > 0 else 0
    sell_through_pct = round(total_sold / total_intro * 100, 1) if total_intro > 0 else 0

    # Economics
    unit_cost = COGS.get(sku, CAT_AVG_COGS.get(get_sub_category(sku), 2.94))
    avg_price = round(total_revenue / total_sold, 2) if total_sold > 0 else 10.05
    waste_cost = round(total_wasted * unit_cost, 2)
    revenue = round(total_revenue, 2)
    net_profit = round(total_revenue - (total_intro * unit_cost), 2)
    net_margin_pct = round(net_profit / total_revenue * 100, 1) if total_revenue > 0 else 0
    waste_cost_wk = round(waste_cost / weeks_on_menu, 2) if weeks_on_menu > 0 else 0

    # Get product name from sales or stock
    product_name = ""
    for (w, v, s), d in sales_product.items():
        if s == sku and d["name"]:
            product_name = d["name"]
            break
    if not product_name:
        # Try stock side
        for pn, s in name_to_sku.items():
            if s == sku:
                product_name = pn
                break
    if not product_name:
        product_name = sku

    category = get_sub_category(sku)

    perf_products.append({
        "product": product_name,
        "introduced": total_intro,
        "sold": total_sold,
        "wasted": total_wasted,
        "category": category,
        "wastage_pct": wastage_pct,
        "sell_through_pct": sell_through_pct,
        "weeks_on_menu": weeks_on_menu,
        "participation_pct": participation_pct,
        "avg_intro_wk": avg_intro_wk,
        "avg_sold_wk": avg_sold_wk,
        "avg_wasted_wk": avg_wasted_wk,
        "SKU": sku,
        "unit_cost": unit_cost,
        "avg_price": avg_price,
        "waste_cost": waste_cost,
        "revenue": revenue,
        "net_profit": net_profit,
        "net_margin_pct": net_margin_pct,
        "waste_cost_wk": waste_cost_wk
    })

# Weekly totals
perf_weekly = []
for week in weeks_sorted:
    wk_intro = sum(perf_intro_pw[sku].get(week, 0) for sku in all_skus)
    wk_sold = sum(perf_sales_pw[sku][week]["sold"] for sku in all_skus)
    wk_wasted = max(0, wk_intro - wk_sold)
    wk_wastage = round(wk_wasted / wk_intro * 100, 1) if wk_intro > 0 else 0
    perf_weekly.append({
        "menu_week": week,
        "introduced": wk_intro,
        "sold": wk_sold,
        "wasted": wk_wasted,
        "wastage_pct": wk_wastage,
        "epc_gap": week == "2025-W33"  # week of Aug 11 2025
    })

# Location × product for location filtering
perf_loc_product = []
for venue in venues_filtered:
    for sku in all_skus:
        lp = loc_product.get(venue, {}).get(sku, {})
        intro = lp.get("introduced", 0)
        sold = lp.get("sold", 0)
        rev = lp.get("revenue", 0.0)
        if intro == 0 and sold == 0:
            continue
        wasted = max(0, intro - sold)
        unit_cost = COGS.get(sku, CAT_AVG_COGS.get(get_sub_category(sku), 2.94))
        perf_loc_product.append({
            "location": venue,
            "product": sku,
            "introduced": intro,
            "sold": sold,
            "wasted": wasted,
            "revenue": round(rev, 2),
            "waste_cost": round(wasted * unit_cost, 2)
        })

perf_categories = sorted(set(p["category"] for p in perf_products))

perf_output = {
    "products": sorted(perf_products, key=lambda x: -x["sold"]),
    "weekly": perf_weekly,
    "loc_product": perf_loc_product,
    "locations": venues_filtered,
    "categories": perf_categories,
    "weeks": weeks_sorted
}

perf_json = json.dumps(perf_output, ensure_ascii=False)
# Replace any NaN/Inf that snuck through
perf_json = perf_json.replace(': NaN', ': 0').replace(': Infinity', ': 0').replace(': -Infinity', ': 0')
with open("perf_dashboard_data.json", "w") as f:
    f.write(perf_json)
print(f"  Products: {len(perf_products)}, Weekly: {len(perf_weekly)}, Loc×Prod: {len(perf_loc_product)}")
print(f"  perf_dashboard_data.json saved ({len(perf_json):,} bytes)")

# ============================================================
# STEP 7: GENERATE PROFITABILITY DASHBOARD JSON
# Site economics with COGS, matching profitability_data.json
# format expected by build_qibi_prof_v7.py
# ============================================================
print("\n=== STEP 7: Generating profitability_data.json ===")

from datetime import date

def week_to_month(week_key):
    """Convert ISO week key to YYYY-MM"""
    parts = week_key.split("-W")
    year = int(parts[0])
    wk = int(parts[1])
    # Get the Monday of that ISO week
    jan4 = date(year, 1, 4)
    start = jan4 - timedelta(days=jan4.weekday())
    monday = start + timedelta(weeks=wk-1)
    return monday.strftime("%Y-%m")

# Site × month aggregation
site_month = defaultdict(lambda: defaultdict(lambda: {
    "revenue":0.0, "units_sold":0, "units_introduced":0,
    "cogs_sold":0.0, "waste_cost":0.0
}))

# From sales: revenue and units sold per site per month
for (week, venue, sku), data in sales_product.items():
    if venue not in venues_filtered:
        continue
    month = week_to_month(week)
    unit_cost = COGS.get(sku, CAT_AVG_COGS.get(data.get("sub_cat","Other"), 2.94))
    site_month[venue][month]["revenue"] += data["revenue"]
    site_month[venue][month]["units_sold"] += data["units"]
    site_month[venue][month]["cogs_sold"] += data["units"] * unit_cost

# From stock: introduced and wasted per site per month
for key, data in stock_agg.items():
    week, venue, product_name = key
    if venue not in venues_filtered:
        continue
    month = week_to_month(week)
    sku = name_to_sku.get(product_name, "")
    sku = SKU_FIXES.get(sku, sku)
    sub_cat = data.get("sub_cat", "Other")
    unit_cost = COGS.get(sku, CAT_AVG_COGS.get(sub_cat, 2.94))
    site_month[venue][month]["units_introduced"] += data["introduced"]

# Compute derived metrics per site per month
all_months = sorted(set(m for v in site_month.values() for m in v.keys()))

prof_sites = []
for venue in venues_filtered:
    months_data = []
    t_rev = 0; t_sold = 0; t_intro = 0; t_cogs_sold = 0; t_waste_cost = 0
    for month in all_months:
        d = site_month[venue].get(month, {"revenue":0,"units_sold":0,"units_introduced":0,"cogs_sold":0})
        rev = d["revenue"]
        sold = d["units_sold"]
        intro = d["units_introduced"]
        cogs_s = d["cogs_sold"]
        wasted = max(0, intro - sold)
        # Average unit cost for this site-month
        avg_uc = cogs_s / sold if sold > 0 else 2.94
        wc = wasted * avg_uc
        gp = rev - cogs_s
        np_ = rev - (intro * avg_uc)
        gm = round(gp / rev * 100, 1) if rev > 0 else 0
        nm = round(np_ / rev * 100, 1) if rev > 0 else 0
        wpct = round(wasted / intro * 100, 1) if intro > 0 else 0
        wrev = round(wc / rev * 100, 1) if rev > 0 else 0

        months_data.append({
            "month": month,
            "revenue": round(rev, 2),
            "units_sold": sold,
            "units_introduced": intro,
            "units_wasted": wasted,
            "cogs_sold": round(cogs_s, 2),
            "waste_cost": round(wc, 2),
            "gross_profit": round(gp, 2),
            "net_profit": round(np_, 2),
            "gross_margin_pct": gm,
            "net_margin_pct": nm,
            "wastage_units_pct": wpct,
            "waste_pct_rev": wrev
        })
        t_rev += rev; t_sold += sold; t_intro += intro
        t_cogs_sold += cogs_s; t_waste_cost += wc

    t_wasted = max(0, t_intro - t_sold)
    t_gp = t_rev - t_cogs_sold
    t_np = t_rev - t_cogs_sold - t_waste_cost
    n_months = len([m for m in months_data if m["revenue"] > 0])
    avg_mo_waste = round(t_waste_cost / n_months, 2) if n_months > 0 else 0
    avg_selling_price = t_rev / t_sold if t_sold > 0 else 10.05
    avg_mo_loss = round(t_wasted * avg_selling_price / n_months, 2) if n_months > 0 else 0

    prof_sites.append({
        "venue": venue,
        "revenue": round(t_rev, 2),
        "units_sold": t_sold,
        "units_introduced": t_intro,
        "units_wasted": t_wasted,
        "cogs_sold": round(t_cogs_sold, 2),
        "waste_cost": round(t_waste_cost, 2),
        "gross_profit": round(t_gp, 2),
        "net_profit": round(t_np, 2),
        "gross_margin_pct": round(t_gp / t_rev * 100, 1) if t_rev > 0 else 0,
        "net_margin_pct": round(t_np / t_rev * 100, 1) if t_rev > 0 else 0,
        "wastage_units_pct": round(t_wasted / t_intro * 100, 1) if t_intro > 0 else 0,
        "waste_pct_rev": round(t_waste_cost / t_rev * 100, 1) if t_rev > 0 else 0,
        "avg_mo_waste": avg_mo_waste,
        "avg_mo_loss": avg_mo_loss,
        "months": months_data
    })

# Monthly totals
prof_monthly = []
for month in all_months:
    m_rev = sum(site_month[v].get(month, {}).get("revenue", 0) for v in venues_filtered)
    m_sold = sum(site_month[v].get(month, {}).get("units_sold", 0) for v in venues_filtered)
    m_intro = sum(site_month[v].get(month, {}).get("units_introduced", 0) for v in venues_filtered)
    m_cogs = sum(site_month[v].get(month, {}).get("cogs_sold", 0) for v in venues_filtered)
    m_wasted = max(0, m_intro - m_sold)
    m_wc = m_wasted * (m_cogs / m_sold if m_sold > 0 else 2.94)
    m_gp = m_rev - m_cogs
    m_np = m_rev - m_cogs - m_wc
    prof_monthly.append({
        "month": month,
        "revenue": round(m_rev, 2),
        "units_sold": m_sold,
        "units_introduced": m_intro,
        "units_wasted": m_wasted,
        "cogs_sold": round(m_cogs, 2),
        "waste_cost": round(m_wc, 2),
        "gross_profit": round(m_gp, 2),
        "net_profit": round(m_np, 2),
        "gross_margin_pct": round(m_gp / m_rev * 100, 1) if m_rev > 0 else 0,
        "net_margin_pct": round(m_np / m_rev * 100, 1) if m_rev > 0 else 0,
        "wastage_units_pct": round(m_wasted / m_intro * 100, 1) if m_intro > 0 else 0
    })

# Product economics
prof_products = []
for sku in all_skus:
    total_sold = sum(d["sold"] for d in perf_sales_pw[sku].values())
    total_revenue = sum(d["revenue"] for d in perf_sales_pw[sku].values())
    total_intro = sum(perf_intro_pw[sku].values())
    total_wasted = max(0, total_intro - total_sold)
    unit_cost = COGS.get(sku, CAT_AVG_COGS.get(get_sub_category(sku), 2.94))
    avg_price = round(total_revenue / total_sold, 2) if total_sold > 0 else 10.05

    prof_products.append({
        "SKU": sku,
        "name": next((p["product"] for p in perf_products if p["SKU"] == sku), sku),
        "category": get_sub_category(sku),
        "units_sold": total_sold,
        "units_introduced": total_intro,
        "units_wasted": total_wasted,
        "revenue": round(total_revenue, 2),
        "unit_cost": unit_cost,
        "avg_price": avg_price,
        "cogs_sold": round(total_sold * unit_cost, 2),
        "waste_cost": round(total_wasted * unit_cost, 2),
        "gross_profit": round(total_revenue - (total_sold * unit_cost), 2),
        "net_profit": round(total_revenue - (total_intro * unit_cost), 2),
        "gross_margin_pct": round((total_revenue - total_sold * unit_cost) / total_revenue * 100, 1) if total_revenue > 0 else 0,
        "net_margin_pct": round((total_revenue - total_intro * unit_cost) / total_revenue * 100, 1) if total_revenue > 0 else 0,
        "wastage_units_pct": round(total_wasted / total_intro * 100, 1) if total_intro > 0 else 0
    })

# Build flat site_monthly records matching v7 schema
prof_site_monthly = []
site_month_products = defaultdict(lambda: defaultdict(set))
for (week, venue, sku), data in sales_product.items():
    if venue not in venues_filtered or not sku:
        continue
    month = week_to_month(week)
    site_month_products[venue][month].add(sku)

for venue in venues_filtered:
    for month in all_months:
        d = site_month[venue].get(month, {"revenue":0,"units_sold":0,"units_introduced":0,"cogs_sold":0})
        rev = d["revenue"]
        sold = d["units_sold"]
        intro = d["units_introduced"]
        cogs_s = d["cogs_sold"]
        if rev == 0 and intro == 0:
            continue
        wasted = max(0, intro - sold)
        avg_uc = cogs_s / sold if sold > 0 else 2.94
        wc = wasted * avg_uc
        cogs_intro = intro * avg_uc
        gp = rev - cogs_s
        np_ = rev - cogs_intro
        prof_site_monthly.append({
            "location": venue, "year_month": month,
            "introduced": intro, "sold": sold, "wasted": wasted,
            "revenue": round(rev, 2), "cogs_sold": round(cogs_s, 2),
            "waste_cost": round(wc, 2), "cogs_introduced": round(cogs_intro, 2),
            "gross_profit": round(gp, 2), "net_profit": round(np_, 2),
            "products_count": len(site_month_products[venue].get(month, set())),
            "wastage_pct": round(wasted / intro * 100, 1) if intro > 0 else 0,
            "gross_margin_pct": round(gp / rev * 100, 1) if rev > 0 else 0,
            "net_margin_pct": round(np_ / rev * 100, 1) if rev > 0 else 0,
            "waste_pct_rev": round(wc / rev * 100, 1) if rev > 0 else 0
        })

# Transform monthly: rename fields to match v7 HTML expectations
prof_monthly_v7 = []
for m in prof_monthly:
    mc = dict(m)
    mc["year_month"] = mc.pop("month")
    m_cogs = mc.get("cogs_sold", 0); m_sold = mc.get("units_sold", 0); m_intro = mc.get("units_introduced", 0)
    avg_uc = m_cogs / m_sold if m_sold > 0 else 2.94
    mc["cogs_introduced"] = round(m_intro * avg_uc, 2)
    mc["introduced"] = mc.pop("units_introduced", 0)
    mc["sold"] = mc.pop("units_sold", 0)
    mc["wasted"] = mc.pop("units_wasted", 0)
    mc["wastage_pct"] = mc.pop("wastage_units_pct", 0)
    prof_monthly_v7.append(mc)

# Transform products: rename fields to match v7 HTML expectations
prof_products_v7 = []
for p in prof_products:
    name = next((pp["product"] for pp in perf_products if pp["SKU"] == p["SKU"]), p.get("name", p["SKU"]))
    cogs_intro = p.get("units_introduced", 0) * p.get("unit_cost", 2.94)
    locs = len(set(lp["location"] for lp in perf_loc_product if lp["product"] == p["SKU"]))
    prof_products_v7.append({
        "product": name, "SKU": p["SKU"], "category": p["category"],
        "introduced": p.get("units_introduced", 0), "sold": p.get("units_sold", 0),
        "wasted": p.get("units_wasted", 0), "revenue": p.get("revenue", 0),
        "cogs_sold": p.get("cogs_sold", 0), "waste_cost": p.get("waste_cost", 0),
        "cogs_introduced": round(cogs_intro, 2),
        "gross_profit": p.get("gross_profit", 0), "net_profit": p.get("net_profit", 0),
        "unit_cost": p.get("unit_cost", 2.94), "revenue_per_unit": p.get("avg_price", 10.05),
        "wastage_pct": p.get("wastage_units_pct", 0),
        "gross_margin_pct": p.get("gross_margin_pct", 0), "net_margin_pct": p.get("net_margin_pct", 0),
        "locations": locs
    })

prof_categories_v7 = sorted(set(p["category"] for p in prof_products_v7))
prof_skus_v7 = sorted(set(p["SKU"] for p in prof_products_v7))

prof_output = {
    "site_monthly": prof_site_monthly,
    "monthly": prof_monthly_v7,
    "products": sorted(prof_products_v7, key=lambda x: -x["revenue"]),
    "locations": sorted(venues_filtered),
    "categories": prof_categories_v7,
    "months": all_months,
    "skus": prof_skus_v7
}

prof_json = json.dumps(prof_output, ensure_ascii=False)
prof_json = prof_json.replace(': NaN', ': 0').replace(': Infinity', ': 0').replace(': -Infinity', ': 0')
with open("profitability_data.json", "w") as f:
    f.write(prof_json)
print(f"  Sites: {len(prof_sites)}, Months: {len(all_months)}, Products: {len(prof_products)}")
print(f"  profitability_data.json saved ({len(prof_json):,} bytes)")

# ============================================================
# STEP 8: GENERATE BESTSELLERS JSON
# Derived from performance data — same product metrics grouped by block
# ============================================================
print("\n=== STEP 8: Generating bestsellers_data.json ===")

# Group products by block (Hot, Cold, Desserts)
hot_prefixes = {"PLT", "SOU"}
cold_prefixes = {"SAL", "WRA", "COL", "ENT", "PTD"}
des_prefixes = {"DES"}

def get_block(sku):
    prefix = "".join(c for c in sku if c.isalpha())
    if prefix in hot_prefixes:
        return "Hot"
    elif prefix in cold_prefixes:
        return "Cold"
    elif prefix in des_prefixes:
        return "Desserts"
    return None

bs_products = []
for p in perf_products:
    block = get_block(p["SKU"])
    if not block:
        continue
    # Per-week data for sparklines
    weekly = []
    for week in weeks_sorted:
        intro = perf_intro_pw[p["SKU"]].get(week, 0)
        sold = perf_sales_pw[p["SKU"]][week]["sold"]
        weekly.append({"w": week, "s": sold, "i": intro})

    sold_val = p["sold"]
    rev_val = p["revenue"]
    wom = p["weeks_on_menu"]
    wasted_val = p["wasted"]
    total_weeks = len(weeks_sorted)
    price_val = round(rev_val / sold_val, 2) if sold_val > 0 else 0
    sparkline = [w_data["s"] for w_data in weekly]  # sold per week for sparkline

    bs_products.append({
        "sku": p["SKU"],
        "name": p["product"],
        "block": block,
        "category": p["category"],
        "introduced": p["introduced"],
        "sold": sold_val,
        "wasted": wasted_val,
        "wastage_pct": p["wastage_pct"],
        "weeks_on_menu": wom,
        "total_weeks": total_weeks,
        "participation_pct": round(wom / total_weeks * 100, 1) if total_weeks > 0 else 0,
        "avg_sold_wk": p["avg_sold_wk"],
        "avg_wasted_wk": p["avg_wasted_wk"],
        "avg_intro_wk": p["avg_intro_wk"],
        "avg_revenue_wk": round(rev_val / wom, 1) if wom > 0 else 0,
        "price": price_val,
        "total_revenue": round(rev_val, 2),
        "revenue": rev_val,
        "unit_cost": p["unit_cost"],
        "waste_cost": p["waste_cost"],
        "net_profit": p["net_profit"],
        "net_margin_pct": p["net_margin_pct"],
        "rev_per_waste": round(rev_val / wasted_val, 1) if wasted_val > 0 else 0,
        "sparkline": sparkline,
        "weekly": weekly
    })

# Rename name→product in bestseller products for v7 HTML compatibility
for p in bs_products:
    p["product"] = p.pop("name")

# Build flat prod_weekly array for filter support
bs_prod_weekly = []
for p in bs_products:
    for w in p["weekly"]:
        wasted = max(0, w["i"] - w["s"])
        if w["i"] > 0 or w["s"] > 0:
            bs_prod_weekly.append({
                "product": p["product"], "week": w["w"],
                "introduced": w["i"], "sold": w["s"], "wasted": wasted
            })

bs_output = {
    "products": bs_products,
    "prod_weekly": bs_prod_weekly,
    "weeks": weeks_sorted,
    "meta": {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_products": len(bs_products),
        "blocks": {"Hot": sum(1 for p in bs_products if p["block"]=="Hot"),
                   "Cold": sum(1 for p in bs_products if p["block"]=="Cold"),
                   "Desserts": sum(1 for p in bs_products if p["block"]=="Desserts")}
    }
}

bs_json = json.dumps(bs_output, ensure_ascii=False)
with open("bestsellers_data.json", "w") as f:
    f.write(bs_json)
print(f"  Hot: {bs_output['meta']['blocks']['Hot']}, Cold: {bs_output['meta']['blocks']['Cold']}, Desserts: {bs_output['meta']['blocks']['Desserts']}")
print(f"  bestsellers_data.json saved ({len(bs_json):,} bytes)")

# ============================================================
# STEP 9: GENERATE SNACKS & DRINKS + PRODUCT SEARCH JSONs
# These only use VendLive sales data
# ============================================================
print("\n=== STEP 9: Generating snacks/drinks + product search JSONs ===")

# statistics already imported at top

# ---------- Snacks & Drinks ----------
snack_cats = {"Sweet Snacks", "Savoury Snacks", "Drinks", "Yogurts"}
sd_products = defaultdict(lambda: {"units":0,"revenue":0.0,
    "weeks":defaultdict(lambda: {"u":0,"r":0.0}), "venues":set()})
for (week, venue, sku), data in sales_product.items():
    if data["sub_cat"] not in snack_cats:
        continue
    sd_products[sku]["units"] += data["units"]
    sd_products[sku]["revenue"] += data["revenue"]
    sd_products[sku]["name"] = data["name"]
    sd_products[sku]["sub_cat"] = data["sub_cat"]
    sd_products[sku]["weeks"][week]["u"] += data["units"]
    sd_products[sku]["weeks"][week]["r"] += data["revenue"]
    sd_products[sku]["venues"].add(venue)

# Build products list matching snacks_drinks.html schema
sd_prods_list = []
for sku, d in sorted(sd_products.items(), key=lambda x: -x[1]["units"]):
    sparkline = [d["weeks"].get(w, {"u":0})["u"] for w in weeks_sorted]
    wom = sum(1 for s in sparkline if s > 0)
    ts = d["units"]
    tr = round(d["revenue"], 2)
    sd_prods_list.append({
        "product": d["name"], "sku": sku, "block": d["sub_cat"],
        "price": round(tr / ts, 2) if ts > 0 else 0,
        "total_sold": ts, "total_revenue": tr,
        "weeks_on_menu": wom, "total_weeks": len(weeks_sorted),
        "participation_pct": round(wom / len(weeks_sorted) * 100, 1) if weeks_sorted else 0,
        "avg_sold_wk": round(ts / wom, 1) if wom > 0 else 0,
        "avg_revenue_wk": round(tr / wom, 1) if wom > 0 else 0,
        "locations": len(d["venues"]),
        "sparkline": sparkline
    })

# Build prod_weekly flat array
sd_prod_weekly = []
for sku, d in sd_products.items():
    for w, wd in d["weeks"].items():
        if wd["u"] > 0:
            sd_prod_weekly.append({
                "product": d["name"], "week": w,
                "sold": wd["u"], "revenue": round(wd["r"], 2)
            })

sd_output = {
    "products": sd_prods_list,
    "prod_weekly": sd_prod_weekly,
    "weeks": weeks_sorted,
    "meta": {"generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
             "total_products": len(sd_prods_list)}
}

sd_json = json.dumps(sd_output, ensure_ascii=False)
with open("snacks_drinks_data.json", "w") as f:
    f.write(sd_json)
print(f"  Snacks & Drinks: {len(sd_prods_list)} products, {len(sd_prod_weekly)} weekly records, saved ({len(sd_json):,} bytes)")

# ---------- Product Search ----------
ps_products = defaultdict(lambda: {
    "units":0,"revenue":0.0,"name":"","sub_cat":"",
    "venues":defaultdict(lambda: {"u":0,"r":0.0,"weeks":set()}),
    "weeks":defaultdict(lambda: {"u":0,"r":0.0})
})
for (week, venue, sku), data in sales_product.items():
    if not sku:
        continue
    ps_products[sku]["units"] += data["units"]
    ps_products[sku]["revenue"] += data["revenue"]
    ps_products[sku]["name"] = data["name"]
    ps_products[sku]["sub_cat"] = data["sub_cat"]
    ps_products[sku]["venues"][venue]["u"] += data["units"]
    ps_products[sku]["venues"][venue]["r"] += data["revenue"]
    ps_products[sku]["venues"][venue]["weeks"].add(week)
    ps_products[sku]["weeks"][week]["u"] += data["units"]
    ps_products[sku]["weeks"][week]["r"] += data["revenue"]

# Build products matching product_search.html schema: {name, cat, tu, tr, nl, avg, med, cv, t10, locs[]}
ps_prods_list = []
all_ps_venues = set()
for sku, d in sorted(ps_products.items(), key=lambda x: -x[1]["units"]):
    venues = d["venues"]
    all_ps_venues.update(venues.keys())
    locs = []
    venue_units = []
    for v, vd in sorted(venues.items(), key=lambda x: -x[1]["u"]):
        wks = len(vd["weeks"])
        uw = round(vd["u"] / wks, 1) if wks > 0 else 0
        locs.append({"l": v, "u": vd["u"], "r": round(vd["r"], 2), "w": wks, "uw": uw})
        venue_units.append(vd["u"])
    tu = d["units"]
    tr = round(d["revenue"], 2)
    nl = len(venues)
    avg_val = round(tu / nl, 1) if nl > 0 else 0
    med_val = round(statistics.median(venue_units), 1) if venue_units else 0
    if nl > 1 and avg_val > 0:
        cv_val = round(statistics.stdev(venue_units) / (tu / nl), 2)
    else:
        cv_val = 0.0
    n_top = max(1, round(nl * 0.1))
    top_units = sum(sorted(venue_units, reverse=True)[:n_top])
    t10_val = round(top_units / tu * 100, 1) if tu > 0 else 0
    ps_prods_list.append({
        "name": d["name"], "cat": d["sub_cat"],
        "tu": tu, "tr": tr, "nl": nl,
        "avg": avg_val, "med": med_val, "cv": cv_val, "t10": t10_val,
        "locs": locs
    })

ps_output = {
    "products": ps_prods_list,
    "total_locations": len(all_ps_venues),
    "meta": {"generated": datetime.now().strftime("%Y-%m-%d %H:%M")}
}

ps_json = json.dumps(ps_output, ensure_ascii=False)
with open("product_search_data.json", "w") as f:
    f.write(ps_json)
print(f"  Product Search: {len(ps_prods_list)} products, {len(all_ps_venues)} locations, saved ({len(ps_json):,} bytes)")

print("\n=== ALL INTERMEDIATE JSONs GENERATED ===")
