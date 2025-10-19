"""
Generate enhanced hurricane risk features with geographic and refinery-specific impact modeling.

This script creates comprehensive hurricane risk indicators based on:
1. Historical Gulf Coast hurricane data (2005-2024)
2. Geographic proximity to PADD 3 refinery clusters
3. Refinery capacity exposure and estimated shutdown impacts
4. Peak hurricane season patterns (Aug-Oct)

Key Enhancement: Geographic Specificity
- Only hurricanes threatening Texas/Louisiana refineries significantly impact gas prices
- Distance to Houston Ship Channel and Lake Charles refineries is critical
- Cat 2 hitting Houston > Cat 5 offshore or hitting Florida east coast

PADD 3 Refinery Context:
- 60%+ of US refining capacity in TX/LA
- Houston Ship Channel: ~3.5M bpd (29.7°N, 95.0°W)
- Lake Charles: ~900K bpd (30.2°N, 93.3°W)
- Port Arthur/Beaumont: ~1.2M bpd (29.9°N, 94.0°W)

Historical Major Hurricanes (Gas Price Impact):
- Katrina (Aug 2005): +40% gas spike, 6-month recovery
- Rita (Sep 2005): +25% gas spike
- Harvey (Aug 2017): +20% gas spike, Colonial Pipeline shutdown
- Laura (Aug 2020): Lake Charles refinery damage
- Ida (Aug 2021): +15% gas spike
- Ian (Sep 2022): $113B damage, minimal refinery impact (west FL coast)
- Idalia (Aug 2023): $3.6B damage, minimal refinery impact (FL Big Bend)

Output:
    - Gas/data/silver/hurricane_risk_features.csv with daily risk features
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional
from math import radians, sin, cos, sqrt, atan2
import pandas as pd
import numpy as np

# Paths
REPO_ROOT = Path(__file__).resolve().parents[1]
SILVER_DIR = REPO_ROOT / "data" / "silver"
OUTPUT_PATH = SILVER_DIR / "hurricane_risk_features.csv"

# PADD 3 Refinery Cluster Locations
HOUSTON_SHIP_CHANNEL = {"lat": 29.7, "lon": -95.0, "capacity_bpd": 3_500_000}
LAKE_CHARLES = {"lat": 30.2, "lon": -93.3, "capacity_bpd": 900_000}
PORT_ARTHUR = {"lat": 29.9, "lon": -94.0, "capacity_bpd": 1_200_000}
CORPUS_CHRISTI = {"lat": 27.8, "lon": -97.4, "capacity_bpd": 400_000}

REFINERY_CLUSTERS = [HOUSTON_SHIP_CHANNEL, LAKE_CHARLES, PORT_ARTHUR, CORPUS_CHRISTI]

# Hurricane risk parameters
OCTOBER_HURRICANE_PROBABILITY = 0.15  # 15% chance of Gulf hurricane in October
SEPTEMBER_HURRICANE_PROBABILITY = 0.30  # Peak season
AUGUST_HURRICANE_PROBABILITY = 0.25

# Historical hurricanes affecting Gulf Coast (Aug-Oct focus, key events all years)
HISTORICAL_HURRICANES = {
    # 2024 (placeholder - research needed)
    2024: [],
    
    # 2023
    2023: [
        {
            "date": "2023-08-30",
            "name": "Idalia",
            "category": 3,
            "max_wind_mph": 115,
            "landfall_lat": 29.8,  # Keaton Beach, FL Big Bend
            "landfall_lon": -83.6,
            "damage_usd": 3_600_000_000,
            "refinery_impact": "minimal",  # North of major refineries
        },
    ],
    
    # 2022
    2022: [
        {
            "date": "2022-09-28",
            "name": "Ian",
            "category": 4,
            "max_wind_mph": 150,
            "landfall_lat": 26.5,  # Cayo Costa Island, FL west coast
            "landfall_lon": -82.2,
            "damage_usd": 113_000_000_000,
            "refinery_impact": "minimal",  # West FL coast, not Gulf refineries
        },
    ],
    
    # 2021
    2021: [
        {
            "date": "2021-08-29",
            "name": "Ida",
            "category": 4,
            "max_wind_mph": 150,
            "landfall_lat": 29.1,  # Port Fourchon, LA
            "landfall_lon": -90.2,
            "damage_usd": 75_000_000_000,
            "refinery_impact": "major",  # +15% gas spike
            "gas_price_impact_pct": 15,
        },
        {
            "date": "2021-10-09",
            "name": "Unnamed Tropical Storm",
            "category": 0,
            "max_wind_mph": 65,
            "landfall_lat": 29.5,
            "landfall_lon": -91.0,
            "refinery_impact": "minimal",
        },
    ],
    
    # 2020
    2020: [
        {
            "date": "2020-08-27",
            "name": "Laura",
            "category": 4,
            "max_wind_mph": 150,
            "landfall_lat": 29.8,  # Cameron Parish, LA
            "landfall_lon": -93.3,  # Direct hit on Lake Charles!
            "damage_usd": 19_000_000_000,
            "refinery_impact": "major",  # Lake Charles refinery damage
            "gas_price_impact_pct": 12,
        },
        {
            "date": "2020-10-27",
            "name": "Zeta",
            "category": 2,
            "max_wind_mph": 110,
            "landfall_lat": 29.2,  # Southeast Louisiana
            "landfall_lon": -89.6,
            "refinery_impact": "moderate",
        },
    ],
    
    # Historical major events for model training context
    2017: [
        {
            "date": "2017-08-25",
            "name": "Harvey",
            "category": 4,
            "max_wind_mph": 130,
            "landfall_lat": 28.0,  # Rockport, TX
            "landfall_lon": -97.0,
            "damage_usd": 125_000_000_000,
            "refinery_impact": "catastrophic",  # Colonial Pipeline shutdown
            "gas_price_impact_pct": 20,
        },
    ],
    
    2008: [
        {
            "date": "2008-09-13",
            "name": "Ike",
            "category": 2,
            "max_wind_mph": 110,
            "landfall_lat": 29.3,  # Galveston, TX
            "landfall_lon": -94.8,  # Near Houston refineries
            "damage_usd": 38_000_000_000,
            "refinery_impact": "major",
        },
    ],
    
    2005: [
        {
            "date": "2005-08-29",
            "name": "Katrina",
            "category": 3,  # At Louisiana landfall
            "max_wind_mph": 125,
            "landfall_lat": 29.4,  # Buras-Triumph, LA
            "landfall_lon": -89.3,
            "damage_usd": 186_000_000_000,
            "refinery_impact": "catastrophic",  # +40% gas spike, 6-month recovery
            "gas_price_impact_pct": 40,
        },
        {
            "date": "2005-09-24",
            "name": "Rita",
            "category": 3,  # At landfall
            "max_wind_mph": 115,
            "landfall_lat": 29.7,  # Sabine Pass, TX/LA border
            "landfall_lon": -93.9,
            "damage_usd": 23_000_000_000,
            "refinery_impact": "major",  # +25% gas spike
            "gas_price_impact_pct": 25,
        },
    ],
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two points on Earth using Haversine formula.
    
    Returns:
        Distance in miles
    """
    R = 3959.0  # Earth's radius in miles
    
    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c


def calculate_refinery_exposure(
    hurricane_lat: float,
    hurricane_lon: float,
    hurricane_category: int,
) -> Dict[str, Any]:
    """
    Calculate refinery exposure metrics for a hurricane.
    
    Returns dict with:
    - distance_to_houston_mi
    - distance_to_lake_charles_mi
    - distance_to_nearest_refinery_mi
    - refineries_at_risk_count (within 100 mi)
    - refining_capacity_threatened_bpd
    - padd3_threat_level (0-10 scale)
    - is_gulf_coast_landfall (TX/LA coast)
    """
    
    # Calculate distances to major refinery clusters
    dist_houston = haversine_distance(hurricane_lat, hurricane_lon, 
                                       HOUSTON_SHIP_CHANNEL["lat"], HOUSTON_SHIP_CHANNEL["lon"])
    dist_lake_charles = haversine_distance(hurricane_lat, hurricane_lon,
                                            LAKE_CHARLES["lat"], LAKE_CHARLES["lon"])
    dist_port_arthur = haversine_distance(hurricane_lat, hurricane_lon,
                                          PORT_ARTHUR["lat"], PORT_ARTHUR["lon"])
    dist_corpus = haversine_distance(hurricane_lat, hurricane_lon,
                                      CORPUS_CHRISTI["lat"], CORPUS_CHRISTI["lon"])
    
    distances = [dist_houston, dist_lake_charles, dist_port_arthur, dist_corpus]
    min_distance = min(distances)
    
    # Count refineries at risk (within 100 miles of Cat 2+, 150 miles for Cat 4+)
    risk_radius = 150 if hurricane_category >= 4 else 100
    
    refineries_at_risk = 0
    capacity_threatened = 0
    
    for cluster, dist in zip(REFINERY_CLUSTERS, distances):
        if dist <= risk_radius:
            refineries_at_risk += 1
            capacity_threatened += cluster["capacity_bpd"]
    
    # Calculate PADD 3 threat level (0-10 scale)
    # Combines proximity + intensity
    if min_distance > 500:
        threat_level = 0  # Too far to matter
    else:
        # Distance factor: 10 at 0 miles, 0 at 500 miles
        distance_factor = max(0, 10 - (min_distance / 50))
        # Category factor: 0-10 scale
        category_factor = hurricane_category * 2  # Cat 5 = 10
        # Combined threat (weighted average)
        threat_level = min(10, (distance_factor * 0.6 + category_factor * 0.4))
    
    # Is this a Gulf Coast (TX/LA) landfall?
    # Texas coast: roughly 25.8°N to 30.0°N, -97.5°W to -93.8°W
    # Louisiana coast: roughly 28.9°N to 30.0°N, -93.8°W to -88.8°W
    is_gulf_landfall = (
        25.8 <= hurricane_lat <= 30.0 and
        -97.5 <= hurricane_lon <= -88.8
    )
    
    return {
        "distance_to_houston_mi": round(dist_houston, 1),
        "distance_to_lake_charles_mi": round(dist_lake_charles, 1),
        "distance_to_nearest_refinery_mi": round(min_distance, 1),
        "refineries_at_risk_count": refineries_at_risk,
        "refining_capacity_threatened_bpd": capacity_threatened,
        "padd3_threat_level": round(threat_level, 2),
        "is_gulf_coast_landfall": int(is_gulf_landfall),
    }


def estimate_shutdown_impact(category: int, distance_to_refineries: float) -> Dict[str, int]:
    """
    Estimate refinery shutdown days based on hurricane category and proximity.
    
    Returns:
        estimated_shutdown_days: Expected days of reduced operations
    """
    
    if distance_to_refineries > 150:
        return {"estimated_shutdown_days": 0}
    
    # Base shutdown days by category
    shutdown_days_map = {
        0: 1,   # Tropical storm: 1 day
        1: 2,   # Cat 1: 2 days
        2: 4,   # Cat 2: 4 days
        3: 8,   # Cat 3: 8 days
        4: 12,  # Cat 4: 12 days
        5: 18,  # Cat 5: 18 days
    }
    
    base_days = shutdown_days_map.get(category, 0)
    
    # Adjust for distance (closer = longer shutdown due to flooding, power loss)
    if distance_to_refineries < 50:
        multiplier = 1.5  # Direct hit area
    elif distance_to_refineries < 100:
        multiplier = 1.0
    else:
        multiplier = 0.5  # Peripheral impact
    
    return {"estimated_shutdown_days": int(base_days * multiplier)}


def create_hurricane_risk_features(
    start_year: int = 2005,
    end_year: int = 2025,
    months: list = [8, 9, 10],  # Aug-Oct peak season
) -> pd.DataFrame:
    """
    Create comprehensive hurricane risk features with geographic and refinery-specific modeling.
    
    Features:
    - Basic: risk_score, probability, intensity, is_event
    - Geographic: distances to refineries, landfall coordinates, threat level
    - Refinery: capacity threatened, shutdown estimates, at-risk counts
    - Lagged: days since last hurricane, rolling averages
    """
    
    records = []
    
    # Get all hurricanes in date range
    all_hurricanes = []
    for year, hurricanes in HISTORICAL_HURRICANES.items():
        if start_year <= year <= end_year and hurricanes:
            for h in hurricanes:
                h_copy = h.copy()
                h_copy["year"] = year
                all_hurricanes.append(h_copy)
    
    # Generate date range for specified months
    for year in range(start_year, end_year + 1):
        for month in months:
            # Determine days in month
            if month in [1, 3, 5, 7, 8, 10, 12]:
                days = 31
            elif month in [4, 6, 9, 11]:
                days = 30
            else:  # February
                days = 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28
            
            month_start = pd.Timestamp(f"{year}-{month:02d}-01")
            month_end = pd.Timestamp(f"{year}-{month:02d}-{days}")
            
            dates = pd.date_range(month_start, month_end, freq="D")
            
            for date in dates:
                # Base hurricane probability by month
                if date.month == 8:
                    base_prob = AUGUST_HURRICANE_PROBABILITY
                elif date.month == 9:
                    base_prob = SEPTEMBER_HURRICANE_PROBABILITY
                else:  # October
                    base_prob = OCTOBER_HURRICANE_PROBABILITY
                    # Risk declines throughout October
                    if date.day > 20:
                        base_prob *= 0.7
                    elif date.day <= 10:
                        base_prob *= 1.3
                
                # Check if actual hurricane occurred near this date
                hurricane_match = None
                days_from_event = 999
                
                for h in all_hurricanes:
                    h_date = pd.Timestamp(h["date"])
                    delta = abs((date - h_date).days)
                    if delta < days_from_event:
                        days_from_event = delta
                        if delta <= 3:  # Hurricane impact window: 3 days
                            hurricane_match = h
                
                # Build feature record
                if hurricane_match and days_from_event <= 3:
                    # Active hurricane impact period
                    is_hurricane_day = days_from_event <= 1
                    
                    # Geographic exposure
                    exposure = calculate_refinery_exposure(
                        hurricane_match["landfall_lat"],
                        hurricane_match["landfall_lon"],
                        hurricane_match["category"],
                    )
                    
                    # Shutdown estimate
                    shutdown = estimate_shutdown_impact(
                        hurricane_match["category"],
                        exposure["distance_to_nearest_refinery_mi"],
                    )
                    
                    # Intensity features
                    max_wind = hurricane_match["max_wind_mph"]
                    hurricane_intensity = min(max_wind / 155.0, 1.0)  # Normalize by Cat 5 threshold
                    
                    # Risk score elevated during event
                    if is_hurricane_day:
                        risk_score = 95.0
                        probability = 0.95
                    else:  # Days before/after
                        risk_score = 60.0
                        probability = 0.60
                        hurricane_intensity *= 0.5
                    
                    record = {
                        "date": date,
                        "hurricane_risk_score": risk_score,
                        "hurricane_probability": probability,
                        "hurricane_intensity": round(hurricane_intensity, 3),
                        "is_hurricane_event": int(is_hurricane_day),
                        "max_wind_mph": max_wind,
                        "hurricane_category": hurricane_match["category"],
                        "hurricane_name": hurricane_match.get("name", "Unnamed"),
                        "landfall_latitude": hurricane_match["landfall_lat"],
                        "landfall_longitude": hurricane_match["landfall_lon"],
                        **exposure,
                        **shutdown,
                        "refinery_impact_level": hurricane_match.get("refinery_impact", "unknown"),
                        "historical_gas_price_impact_pct": hurricane_match.get("gas_price_impact_pct", 0),
                    }
                
                else:
                    # Normal day (no hurricane)
                    record = {
                        "date": date,
                        "hurricane_risk_score": round(base_prob * 100, 2),
                        "hurricane_probability": round(base_prob, 3),
                        "hurricane_intensity": 0.0,
                        "is_hurricane_event": 0,
                        "max_wind_mph": 0,
                        "hurricane_category": 0,
                        "hurricane_name": "None",
                        "landfall_latitude": None,
                        "landfall_longitude": None,
                        "distance_to_houston_mi": None,
                        "distance_to_lake_charles_mi": None,
                        "distance_to_nearest_refinery_mi": None,
                        "refineries_at_risk_count": 0,
                        "refining_capacity_threatened_bpd": 0,
                        "padd3_threat_level": 0.0,
                        "is_gulf_coast_landfall": 0,
                        "estimated_shutdown_days": 0,
                        "refinery_impact_level": "none",
                        "historical_gas_price_impact_pct": 0,
                    }
                
                records.append(record)
    
    df = pd.DataFrame(records)
    return df


def add_lagged_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add lagged and rolling hurricane risk features."""
    
    df = df.sort_values("date").copy()
    
    # Days since last major hurricane (category 2+)
    major_hurricane_dates = df[
        (df["is_hurricane_event"] == 1) & (df["hurricane_category"] >= 2)
    ]["date"]
    
    def days_since_last_hurricane(row_date):
        past_hurricanes = major_hurricane_dates[major_hurricane_dates < row_date]
        if len(past_hurricanes) == 0:
            return 730  # Cap at 2 years
        return min((row_date - past_hurricanes.max()).days, 730)
    
    df["days_since_last_hurricane"] = df["date"].apply(days_since_last_hurricane)
    
    # 7-day rolling average of risk score
    df["hurricane_risk_7d_avg"] = df["hurricane_risk_score"].rolling(
        window=7, min_periods=1
    ).mean().round(2)
    
    # 14-day rolling max threat level (captures sustained high risk periods)
    df["padd3_threat_14d_max"] = df["padd3_threat_level"].rolling(
        window=14, min_periods=1
    ).max().round(2)
    
    # Cumulative refinery exposure in past 30 days
    df["refining_capacity_threatened_30d_cumsum"] = df["refining_capacity_threatened_bpd"].rolling(
        window=30, min_periods=1
    ).sum()
    
    # Days until next known hurricane (forward-looking for training)
    future_hurricane_dates = df[df["is_hurricane_event"] == 1]["date"]
    
    def days_until_next_hurricane(row_date):
        future_hurricanes = future_hurricane_dates[future_hurricane_dates > row_date]
        if len(future_hurricanes) == 0:
            return 365  # No upcoming hurricanes
        return min((future_hurricanes.min() - row_date).days, 365)
    
    df["days_until_next_hurricane"] = df["date"].apply(days_until_next_hurricane)
    
    return df


def main():
    print("=" * 80)
    print("GENERATING ENHANCED HURRICANE RISK FEATURES")
    print("=" * 80)
    print("\n🌀 Hurricane Season Coverage: August-October")
    print("📍 Geographic Focus: PADD 3 Gulf Coast Refineries")
    print("📊 Historical Period: 2005-2025 (major hurricanes included)")
    
    # Create features
    print("\n🔄 Creating hurricane features with geographic modeling...")
    df = create_hurricane_risk_features(
        start_year=2005,
        end_year=2025,
        months=[8, 9, 10],  # Peak hurricane season
    )
    
    # Add lagged features
    print("🔄 Adding lagged and rolling features...")
    df = add_lagged_features(df)
    
    # Save to Silver layer
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    
    print(f"\n✓ Hurricane risk features saved to: {OUTPUT_PATH}")
    print(f"  Rows: {len(df):,}")
    print(f"  Columns: {len(df.columns)}")
    print(f"  Features: {list(df.columns)}")
    
    # Summary statistics
    print(f"\n📊 Feature Statistics:")
    print(df[["hurricane_risk_score", "hurricane_probability", "padd3_threat_level"]].describe())
    
    # Show hurricane events
    hurricane_days = df[df["is_hurricane_event"] == 1].copy()
    if len(hurricane_days) > 0:
        print(f"\n🌀 Historical Hurricane Events: {len(hurricane_days)} days")
        print("=" * 80)
        
        # Group by hurricane name to avoid repetition
        unique_hurricanes = hurricane_days.drop_duplicates(subset=["hurricane_name", "date"])
        
        for _, row in unique_hurricanes.sort_values("date").iterrows():
            threat_emoji = "🔴" if row["padd3_threat_level"] >= 7 else "🟡" if row["padd3_threat_level"] >= 4 else "🟢"
            print(f"  {threat_emoji} {row['date'].strftime('%Y-%m-%d')}: {row['hurricane_name']} (Cat {row['hurricane_category']})")
            print(f"     ├─ Wind: {row['max_wind_mph']} mph")
            print(f"     ├─ Nearest refinery: {row['distance_to_nearest_refinery_mi']:.0f} mi")
            print(f"     ├─ PADD 3 threat: {row['padd3_threat_level']:.1f}/10")
            print(f"     ├─ Refineries at risk: {row['refineries_at_risk_count']}")
            print(f"     ├─ Capacity threatened: {row['refining_capacity_threatened_bpd']:,.0f} bpd")
            if row["historical_gas_price_impact_pct"] > 0:
                print(f"     └─ Historical gas impact: +{row['historical_gas_price_impact_pct']}%")
            print()
    else:
        print("\n⚠️  No major hurricane events in dataset")
    
    # Geographic coverage summary
    gulf_landfalls = df[df["is_gulf_coast_landfall"] == 1]
    print(f"\n📍 Gulf Coast (TX/LA) Landfalls: {len(gulf_landfalls)} days")
    
    high_threat_days = df[df["padd3_threat_level"] >= 7]
    print(f"🔴 High Threat Days (PADD 3 threat ≥ 7): {len(high_threat_days)} days")
    
    capacity_threatened = df[df["refining_capacity_threatened_bpd"] > 0]
    print(f"⚠️  Days with Refinery Capacity Threatened: {len(capacity_threatened)} days")
    
    print(f"\n✓ Enhanced hurricane risk features ready for Gold layer integration")
    print(f"✓ Geographic and refinery-specific features included")
    print(f"✓ Ready to merge with master dataset for model training")


if __name__ == "__main__":
    main()
