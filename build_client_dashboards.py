#!/usr/bin/env python3
"""
QiBi Client Dashboard Builder v2 — Sales + Wastage
KEY FIX: Aggregates by VENUE per transaction (not fridge with static mapping).
Fridges move between venues over time — each transaction's venue is used as-is.

Processes 5 input files, outputs dashboard_data.json for HTML dashboards.
"""
import csv
import json
import sys
from datetime import datetime, timedelta
from collections import defaultdict

# ============================================================
# CONFIG
# ============================================================
SALES_FILE = "mnt/uploads/1-All_machine_Sales_Report_29_12_2024_to_17_05_2026_on_21_05_2026_11_15_08.csv"
STOCK_VL_FILE = "mnt/uploads/1-All_machine_Stock_Movements_Report_05_01_2025_to_18_05_2026_on_21_05_2026_10_57_36.csv"
CRYO_SALES_FILE = "mnt/uploads/3593 - 2026-05-21T124109.345.csv"
CRYO_STOCK_FILE = "mnt/uploads/5435 (8).csv"
MELBA_FILE = "mnt/uploads/melba_recipes_2026-05-21.csv"

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

# Category group mapping (SKU prefix → dashboard group)
def get_category_group(sku):
    prefix = "".join(c for c in sku if c.isalpha())
    if prefix in ("PLT","SAL","WRA","DES","PTD","SOU","COL","ENT"):
        return "Fresh Food"
    elif prefix == "SNK":
        return "Sweet Snacks"
    elif prefix == "SNKS":
        return "Savoury Snacks"
    elif prefix == "DRK":
        return "Drinks"
    elif prefix == "YOG":
        return "Sweet Snacks"
    elif prefix == "OTH":
        return "Other"
    return "Other"

# Sub-category mapping
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

# Cryo category → category group
CRYO_GROUP_MAP = {
    "Plats chauds": "Fresh Food", "Desserts": "Fresh Food",
    "Salades": "Fresh Food", "Sandwichs": "Fresh Food",
    "Wraps": "Fresh Food", "Poke Bowls": "Fresh Food",
    "Petits-déjeuners": "Fresh Food", "Soupes": "Fresh Food",
    "Bagels": "Fresh Food", "Collations": "Fresh Food",
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

# Category averages for SNK/SNKS/DRK/YOG (wholesale, no Melba COGS)
WHOLESALE_COGS_RATE = {"Sweet Snacks": 0.55, "Savoury Snacks": 0.55, "Drinks": 0.50, "Other": 0.50}

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
pending_rows = []  # (dt, week, venue, sku, name, cat_group, sub_cat, price, tag_id)

with open(SALES_FILE, "r", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        refund_val = row.get("is_refunded","").strip()
        if refund_val:  # any non-empty value = refunded, skip
            refund_skipped += 1
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
        cat_group = get_category_group(sku)
        sub_cat = get_sub_category(sku)
        tag_id = row.get("item_tag_id","").strip()

        pending_rows.append((dt, week, venue, sku, name, cat_group, sub_cat, price, tag_id))

# EPC dedup: for each EPC with multiple rows, keep only the LATEST (by timestamp)
# Rows without EPC (empty or "-") pass through as-is
epc_latest = {}  # tag_id → index in pending_rows (latest dt wins)
no_epc_rows = []
epc_dupes_discarded = 0

for i, (dt, week, venue, sku, name, cat_group, sub_cat, price, tag_id) in enumerate(pending_rows):
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
    dt, week, venue, sku, name, cat_group, sub_cat, price, tag_id = pending_rows[i]
    sales_data.append((week, venue, sku, name, cat_group, sub_cat, price, 1))

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
        cat_group = CRYO_GROUP_MAP.get(cryo_cat, get_category_group(sku))
        sub_cat = CRYO_CAT_MAP.get(cryo_cat, get_sub_category(sku))

        # Cryo: location IS the venue
        sales_data.append((week, location, sku, name, cat_group, sub_cat, price, 1))
        cryo_sales_count += 1

print(f"  Cryo sales added: {cryo_sales_count:,}")
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
# intro/waste: (week, venue, product_name, product_id, cat_group, sub_cat, units)
intro_data = []
waste_data = []
seen_epcs = set()

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

    # Map VendLive category to our groups
    vl_cat_map = {
        "Hot": ("Fresh Food", "Hot Dishes"),
        "Cold": ("Fresh Food", "Salads & Bowls"),
        "Sweet Snacks": ("Sweet Snacks", "Sweet Snacks"),
        "Savory Snacks": ("Savoury Snacks", "Savoury Snacks"),
        "Drinks": ("Drinks", "Drinks"),
        "New in the fridge": ("Fresh Food", "Hot Dishes"),
        "Salades": ("Fresh Food", "Salads & Bowls"),
    }

    cat_group, sub_cat = vl_cat_map.get(vl_cat, ("Other", "Other"))
    week = get_week_key(dt)

    if typ in ("In", "Add", "Found"):
        if epc and epc != "-" and epc in seen_epcs:
            continue
        if epc and epc != "-":
            seen_epcs.add(epc)
        # KEY: store venue from this row
        intro_data.append((week, venue, product_name, product_id, cat_group, sub_cat, qty))
    elif typ in ("Wasted", "Remove"):
        waste_data.append((week, venue, product_name, product_id, cat_group, sub_cat, qty))

print(f"  Introductions: {sum(q for *_,q in intro_data):,} units ({len(intro_data):,} rows)")
print(f"  Wastage: {sum(q for *_,q in waste_data):,} units ({len(waste_data):,} rows)")
print(f"  Unique EPCs tracked: {len(seen_epcs):,}")

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

        cat_group = CRYO_GROUP_MAP.get(cryo_cat, "Other")
        sub_cat = CRYO_CAT_MAP.get(cryo_cat, "Other")
        week = get_week_key(dt)

        if action == "Add":
            if epc and epc in seen_epcs:
                continue
            if epc:
                seen_epcs.add(epc)
            # Cryo: location IS the venue
            intro_data.append((week, location, name, "", cat_group, sub_cat, 1))
            cryo_stock_count += 1
        elif action == "Remove":
            waste_data.append((week, location, name, "", cat_group, sub_cat, 1))

print(f"  Cryo introductions: {cryo_stock_count:,}")

# ============================================================
# STEP 4: AGGREGATE DATA — all by VENUE, not fridge
# ============================================================
print("\nStep 4: Aggregating by venue...")

# Sales: (week, venue, sku) → detail
sales_product = defaultdict(lambda: {"units":0,"revenue":0.0,"name":"","cat_group":"","sub_cat":""})

all_weeks = set()
all_venues = set()

for week, venue, sku, name, cat_group, sub_cat, price, units in sales_data:
    key = (week, venue, sku)
    sales_product[key]["units"] += units
    sales_product[key]["revenue"] += price
    sales_product[key]["name"] = name
    sales_product[key]["cat_group"] = cat_group
    sales_product[key]["sub_cat"] = sub_cat
    all_weeks.add(week)
    all_venues.add(venue)

# Stock: (week, venue, product_name) → {introduced, wasted}
stock_agg = defaultdict(lambda: {"introduced":0, "wasted":0})

for week, venue, name, pid, cat_group, sub_cat, qty in intro_data:
    key = (week, venue, name)
    stock_agg[key]["introduced"] += qty
    stock_agg[key]["cat_group"] = cat_group
    stock_agg[key]["sub_cat"] = sub_cat
    all_weeks.add(week)
    all_venues.add(venue)

for week, venue, name, pid, cat_group, sub_cat, qty in waste_data:
    key = (week, venue, name)
    stock_agg[key]["wasted"] += qty
    if "cat_group" not in stock_agg[key]:
        stock_agg[key]["cat_group"] = cat_group
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
# Aggregate: venue → week → {units, revenue}
sales_by_venue_week = defaultdict(lambda: defaultdict(lambda: {"units":0,"revenue":0.0}))

for (week, venue, sku), data in sales_product.items():
    sales_by_venue_week[venue][week]["units"] += data["units"]
    sales_by_venue_week[venue][week]["revenue"] += data["revenue"]

# Build venue-level weekly arrays
venue_sales = {}
for venue in venues_filtered:
    weeks_data = {}
    ytd_units = 0
    ytd_revenue = 0.0
    for week in weeks_sorted:
        d = sales_by_venue_week[venue].get(week, {"units":0,"revenue":0.0})
        weeks_data[week] = {"u": d["units"], "r": round(d["revenue"],2)}
        ytd_units += d["units"]
        ytd_revenue += d["revenue"]
    venue_sales[venue] = {
        "venue": venue,
        "weeks": weeks_data,
        "ytd_u": ytd_units,
        "ytd_r": round(ytd_revenue, 2)
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

CAT_AVG_COGS = {"Fresh Food": 2.94, "Sweet Snacks": 1.20, "Savoury Snacks": 1.30, "Drinks": 1.25, "Other": 2.00}

# Aggregate wastage by venue
wastage_by_venue_week = defaultdict(lambda: defaultdict(lambda: {"intro":0,"wasted":0,"waste_cost":0.0}))

for key, data in stock_agg.items():
    week, venue, product_name = key
    intro = data["introduced"]
    wasted = data["wasted"]
    cat_group = data.get("cat_group", "Other")

    sku = name_to_sku.get(product_name, "")
    sku = SKU_FIXES.get(sku, sku)
    unit_cost = COGS.get(sku, CAT_AVG_COGS.get(cat_group, 2.94))
    waste_cost = wasted * unit_cost

    wastage_by_venue_week[venue][week]["intro"] += intro
    wastage_by_venue_week[venue][week]["wasted"] += wasted
    wastage_by_venue_week[venue][week]["waste_cost"] += waste_cost

# Build venue-level wastage arrays
venue_wastage = {}
for venue in venues_filtered:
    weeks_data = {}
    ytd_intro = 0
    ytd_wasted = 0
    ytd_waste_cost = 0.0
    for week in weeks_sorted:
        d = wastage_by_venue_week[venue].get(week, {"intro":0,"wasted":0,"waste_cost":0.0})
        weeks_data[week] = {
            "i": d["intro"],
            "w": d["wasted"],
            "c": round(d["waste_cost"], 2)
        }
        ytd_intro += d["intro"]
        ytd_wasted += d["wasted"]
        ytd_waste_cost += d["waste_cost"]

    venue_wastage[venue] = {
        "venue": venue,
        "weeks": weeks_data,
        "ytd_i": ytd_intro,
        "ytd_w": ytd_wasted,
        "ytd_c": round(ytd_waste_cost, 2)
    }

# --- PRODUCT-LEVEL DATA for filters ---
product_sales_agg = defaultdict(lambda: {"units":0,"revenue":0.0,"cat_group":"","sub_cat":"","name":"","sku":""})
for (week, venue, sku), data in sales_product.items():
    key = sku if sku else data["name"]
    product_sales_agg[key]["units"] += data["units"]
    product_sales_agg[key]["revenue"] += data["revenue"]
    product_sales_agg[key]["cat_group"] = data.get("cat_group","")
    product_sales_agg[key]["sub_cat"] = data.get("sub_cat","")
    product_sales_agg[key]["name"] = data["name"]
    product_sales_agg[key]["sku"] = sku

product_wastage_agg = defaultdict(lambda: {"intro":0,"wasted":0,"waste_cost":0.0,"cat_group":"","sub_cat":"","name":""})
for key, data in stock_agg.items():
    week, venue, product_name = key
    cat_group = data.get("cat_group","Other")
    sub_cat = data.get("sub_cat","Other")
    sku = name_to_sku.get(product_name,"")
    sku = SKU_FIXES.get(sku, sku)
    unit_cost = COGS.get(sku, CAT_AVG_COGS.get(cat_group, 2.94))

    pkey = sku if sku else product_name
    product_wastage_agg[pkey]["intro"] += data["introduced"]
    product_wastage_agg[pkey]["wasted"] += data["wasted"]
    product_wastage_agg[pkey]["waste_cost"] += data["wasted"] * unit_cost
    product_wastage_agg[pkey]["cat_group"] = cat_group
    product_wastage_agg[pkey]["sub_cat"] = sub_cat
    product_wastage_agg[pkey]["name"] = product_name

products_list = []
for key, d in product_sales_agg.items():
    sku = d.get("sku", key)
    products_list.append({
        "sku": sku,
        "name": d["name"],
        "cat_group": d["cat_group"],
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
        "cat_group": d["cat_group"],
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
