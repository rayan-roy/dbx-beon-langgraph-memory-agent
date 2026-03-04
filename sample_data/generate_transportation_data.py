#!/usr/bin/env python3
"""
Generate synthetic transportation and supply chain data for analysis.

Produces CSV files with realistic freight, shipment, and customer data
suitable for testing the CSV upload agent.

Usage:
    python generate_transportation_data.py
    python generate_transportation_data.py --rows 5000 --output-dir ./output
"""

import argparse
import csv
import os
import random
from datetime import datetime, timedelta

# --- Reference data ---

CUSTOMERS = [
    ("C001", "Acme Manufacturing", "Automotive"),
    ("C002", "GlobalTech Solutions", "Electronics"),
    ("C003", "FreshHarvest Foods", "Food & Beverage"),
    ("C004", "MedSupply Corp", "Healthcare"),
    ("C005", "BuildRight Materials", "Construction"),
    ("C006", "PetroChem Industries", "Chemicals"),
    ("C007", "TextileWorld Inc", "Textiles"),
    ("C008", "SteelForge Ltd", "Metals"),
    ("C009", "AgroFarm Supplies", "Agriculture"),
    ("C010", "QuickRetail Group", "Retail"),
    ("C011", "PackLogic Systems", "Packaging"),
    ("C012", "EnergyFlow Corp", "Energy"),
    ("C013", "PharmaDist Inc", "Pharmaceuticals"),
    ("C014", "AutoParts Direct", "Automotive"),
    ("C015", "ColdChain Express", "Food & Beverage"),
]

ORIGINS = [
    ("Los Angeles, CA", "US-West"),
    ("Chicago, IL", "US-Midwest"),
    ("Houston, TX", "US-South"),
    ("Newark, NJ", "US-East"),
    ("Atlanta, GA", "US-South"),
    ("Seattle, WA", "US-West"),
    ("Dallas, TX", "US-South"),
    ("Memphis, TN", "US-South"),
    ("Louisville, KY", "US-East"),
    ("Columbus, OH", "US-Midwest"),
]

DESTINATIONS = [
    ("New York, NY", "US-East"),
    ("Miami, FL", "US-South"),
    ("San Francisco, CA", "US-West"),
    ("Denver, CO", "US-West"),
    ("Boston, MA", "US-East"),
    ("Phoenix, AZ", "US-West"),
    ("Detroit, MI", "US-Midwest"),
    ("Minneapolis, MN", "US-Midwest"),
    ("Portland, OR", "US-West"),
    ("Nashville, TN", "US-South"),
    ("Toronto, ON", "Canada"),
    ("Vancouver, BC", "Canada"),
    ("Monterrey, MX", "Mexico"),
]

TRANSPORT_MODES = ["Truck (FTL)", "Truck (LTL)", "Rail", "Intermodal", "Air Freight", "Ocean"]
CARRIERS = [
    "SwiftHaul Logistics", "TransNational Freight", "BlueWave Shipping",
    "IronRail Transport", "SkyBridge Air Cargo", "PrimeMove Carriers",
    "Continental Express", "Pacific Route Lines", "Heartland Trucking",
    "Apex Freight Solutions",
]
SHIPMENT_STATUSES = ["Delivered", "Delivered", "Delivered", "Delivered", "In Transit", "Delayed", "Cancelled"]
COMMODITY_TYPES = [
    "General Merchandise", "Refrigerated Goods", "Hazardous Materials",
    "Oversized Load", "Fragile Items", "Bulk Commodities", "High-Value Goods",
    "Raw Materials", "Finished Products", "Machinery & Equipment",
]

# Cost/weight ranges by transport mode
MODE_PROFILES = {
    "Truck (FTL)": {"weight_range": (5000, 45000), "rate_per_lb": (0.04, 0.12), "transit_days": (1, 7)},
    "Truck (LTL)": {"weight_range": (100, 10000), "rate_per_lb": (0.08, 0.25), "transit_days": (2, 10)},
    "Rail":        {"weight_range": (20000, 200000), "rate_per_lb": (0.02, 0.06), "transit_days": (5, 14)},
    "Intermodal":  {"weight_range": (10000, 80000), "rate_per_lb": (0.03, 0.08), "transit_days": (4, 12)},
    "Air Freight": {"weight_range": (50, 5000), "rate_per_lb": (0.50, 2.50), "transit_days": (1, 3)},
    "Ocean":       {"weight_range": (10000, 500000), "rate_per_lb": (0.01, 0.04), "transit_days": (14, 45)},
}


def generate_shipments(num_rows: int, seed: int = 42) -> list[dict]:
    random.seed(seed)
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 12, 31)
    date_range = (end_date - start_date).days

    rows = []
    for i in range(1, num_rows + 1):
        customer_id, customer_name, industry = random.choice(CUSTOMERS)
        origin_city, origin_region = random.choice(ORIGINS)
        dest_city, dest_region = random.choice(DESTINATIONS)
        mode = random.choice(TRANSPORT_MODES)
        carrier = random.choice(CARRIERS)
        commodity = random.choice(COMMODITY_TYPES)
        status = random.choice(SHIPMENT_STATUSES)

        profile = MODE_PROFILES[mode]
        weight_lbs = round(random.uniform(*profile["weight_range"]), 1)
        rate_per_lb = round(random.uniform(*profile["rate_per_lb"]), 4)
        base_cost = weight_lbs * rate_per_lb

        # Add surcharges
        fuel_surcharge = round(base_cost * random.uniform(0.08, 0.18), 2)
        accessorial_charges = round(random.uniform(0, 500), 2) if random.random() > 0.4 else 0
        total_freight_cost = round(base_cost + fuel_surcharge + accessorial_charges, 2)

        ship_date = start_date + timedelta(days=random.randint(0, date_range))
        transit_days = random.randint(*profile["transit_days"])
        if status == "Delayed":
            transit_days += random.randint(1, 5)
        delivery_date = ship_date + timedelta(days=transit_days) if status != "Cancelled" else None

        num_pallets = max(1, int(weight_lbs / random.uniform(800, 2000)))
        on_time = status == "Delivered" and transit_days <= profile["transit_days"][1]
        damage_claim = random.random() < 0.03  # 3% damage rate

        rows.append({
            "shipment_id": f"SHP-{i:06d}",
            "customer_id": customer_id,
            "customer_name": customer_name,
            "industry": industry,
            "origin_city": origin_city,
            "origin_region": origin_region,
            "destination_city": dest_city,
            "destination_region": dest_region,
            "transport_mode": mode,
            "carrier": carrier,
            "commodity_type": commodity,
            "weight_lbs": weight_lbs,
            "num_pallets": num_pallets,
            "ship_date": ship_date.strftime("%Y-%m-%d"),
            "delivery_date": delivery_date.strftime("%Y-%m-%d") if delivery_date else "",
            "transit_days": transit_days if status != "Cancelled" else "",
            "status": status,
            "on_time_delivery": on_time if status == "Delivered" else "",
            "base_freight_cost": round(base_cost, 2),
            "fuel_surcharge": fuel_surcharge,
            "accessorial_charges": accessorial_charges,
            "total_freight_cost": total_freight_cost,
            "cost_per_lb": round(total_freight_cost / weight_lbs, 4) if weight_lbs else 0,
            "damage_claim": damage_claim,
            "damage_amount": round(random.uniform(200, 5000), 2) if damage_claim else 0,
        })

    return rows


def generate_customer_summary(shipments: list[dict]) -> list[dict]:
    """Aggregate shipment data into a customer-level summary."""
    customers = {}
    for s in shipments:
        cid = s["customer_id"]
        if cid not in customers:
            customers[cid] = {
                "customer_id": cid,
                "customer_name": s["customer_name"],
                "industry": s["industry"],
                "total_shipments": 0,
                "total_weight_lbs": 0,
                "total_freight_cost": 0,
                "delivered_count": 0,
                "on_time_count": 0,
                "delayed_count": 0,
                "cancelled_count": 0,
                "damage_claims": 0,
                "damage_cost": 0,
                "modes_used": set(),
            }
        c = customers[cid]
        c["total_shipments"] += 1
        c["total_weight_lbs"] += s["weight_lbs"]
        c["total_freight_cost"] += s["total_freight_cost"]
        c["modes_used"].add(s["transport_mode"])
        if s["status"] == "Delivered":
            c["delivered_count"] += 1
            if s["on_time_delivery"] is True:
                c["on_time_count"] += 1
        elif s["status"] == "Delayed":
            c["delayed_count"] += 1
        elif s["status"] == "Cancelled":
            c["cancelled_count"] += 1
        if s["damage_claim"]:
            c["damage_claims"] += 1
            c["damage_cost"] += s["damage_amount"]

    rows = []
    for c in customers.values():
        delivered = c["delivered_count"]
        rows.append({
            "customer_id": c["customer_id"],
            "customer_name": c["customer_name"],
            "industry": c["industry"],
            "total_shipments": c["total_shipments"],
            "total_weight_lbs": round(c["total_weight_lbs"], 1),
            "total_freight_cost": round(c["total_freight_cost"], 2),
            "avg_cost_per_shipment": round(c["total_freight_cost"] / c["total_shipments"], 2),
            "avg_cost_per_lb": round(c["total_freight_cost"] / c["total_weight_lbs"], 4) if c["total_weight_lbs"] else 0,
            "delivered_count": delivered,
            "on_time_pct": round(c["on_time_count"] / delivered * 100, 1) if delivered else 0,
            "delayed_count": c["delayed_count"],
            "cancelled_count": c["cancelled_count"],
            "damage_claims": c["damage_claims"],
            "total_damage_cost": round(c["damage_cost"], 2),
            "transport_modes_used": ", ".join(sorted(c["modes_used"])),
        })

    return sorted(rows, key=lambda x: x["total_freight_cost"], reverse=True)


def generate_lane_analysis(shipments: list[dict]) -> list[dict]:
    """Aggregate shipment data into origin-destination lane analysis."""
    lanes = {}
    for s in shipments:
        if s["status"] == "Cancelled":
            continue
        key = (s["origin_city"], s["destination_city"])
        if key not in lanes:
            lanes[key] = {
                "origin": key[0],
                "destination": key[1],
                "origin_region": s["origin_region"],
                "destination_region": s["destination_region"],
                "shipment_count": 0,
                "total_weight": 0,
                "total_cost": 0,
                "transit_days_sum": 0,
                "on_time_count": 0,
                "delivered_count": 0,
                "modes": set(),
                "carriers": set(),
            }
        l = lanes[key]
        l["shipment_count"] += 1
        l["total_weight"] += s["weight_lbs"]
        l["total_cost"] += s["total_freight_cost"]
        if s["transit_days"]:
            l["transit_days_sum"] += int(s["transit_days"])
        if s["status"] == "Delivered":
            l["delivered_count"] += 1
            if s["on_time_delivery"] is True:
                l["on_time_count"] += 1
        l["modes"].add(s["transport_mode"])
        l["carriers"].add(s["carrier"])

    rows = []
    for l in lanes.values():
        rows.append({
            "origin": l["origin"],
            "destination": l["destination"],
            "origin_region": l["origin_region"],
            "destination_region": l["destination_region"],
            "shipment_count": l["shipment_count"],
            "total_weight_lbs": round(l["total_weight"], 1),
            "total_freight_cost": round(l["total_cost"], 2),
            "avg_cost_per_shipment": round(l["total_cost"] / l["shipment_count"], 2),
            "avg_transit_days": round(l["transit_days_sum"] / l["shipment_count"], 1),
            "on_time_pct": round(l["on_time_count"] / l["delivered_count"] * 100, 1) if l["delivered_count"] else 0,
            "num_carriers": len(l["carriers"]),
            "transport_modes": ", ".join(sorted(l["modes"])),
        })

    return sorted(rows, key=lambda x: x["shipment_count"], reverse=True)


def write_csv(filepath: str, rows: list[dict]):
    if not rows:
        return
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  {filepath} ({len(rows)} rows)")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic transportation data")
    parser.add_argument("--rows", type=int, default=2000, help="Number of shipment records (default: 2000)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: same as script)")
    args = parser.parse_args()

    output_dir = args.output_dir or os.path.dirname(os.path.abspath(__file__))
    os.makedirs(output_dir, exist_ok=True)

    print(f"Generating {args.rows} shipment records (seed={args.seed})...")

    shipments = generate_shipments(args.rows, seed=args.seed)
    customer_summary = generate_customer_summary(shipments)
    lane_analysis = generate_lane_analysis(shipments)

    print("Writing CSV files:")
    write_csv(os.path.join(output_dir, "shipments.csv"), shipments)
    write_csv(os.path.join(output_dir, "customer_summary.csv"), customer_summary)
    write_csv(os.path.join(output_dir, "lane_analysis.csv"), lane_analysis)
    print("Done!")


if __name__ == "__main__":
    main()
