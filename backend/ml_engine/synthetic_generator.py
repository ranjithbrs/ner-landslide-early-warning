"""
Synthetic / Prototype Dataset Generator for NER Landslide Risk Modeling.

IMPORTANT NOTICE:
This dataset is synthetically generated using empirical geomorphological, hydrological,
and geotechnical relationships calibrated to the terrain patterns of the North Eastern
Region (NER) of India (Eastern Himalayas and Indo-Burman ranges).
It is intended solely for prototype development, ML pipeline verification, and system
architecture testing. It does NOT claim to represent official Geological Survey of India (GSI)
or India Meteorological Department (IMD) field telemetry.
"""

import numpy as np
import pandas as pd
from pathlib import Path

# Key representative vulnerable corridors across the 8 NER states
NER_REFERENCE_ZONES = [
    {"state": "Sikkim", "district": "Pakyong", "location": "NH-10 Sevoke-Gangtok Corridor", "base_elev": 1100, "base_slope": 38.0, "lithology": 4},
    {"state": "Sikkim", "district": "Mangan", "location": "North Sikkim Highway (Chungthang)", "base_elev": 1800, "base_slope": 44.0, "lithology": 5},
    {"state": "Nagaland", "district": "Kohima", "location": "NH-29 Dimapur-Kohima By-pass", "base_elev": 1400, "base_slope": 34.0, "lithology": 3},
    {"state": "Nagaland", "district": "Phek", "location": "Phek-Meluri Road Corridor", "base_elev": 1650, "base_slope": 36.0, "lithology": 3},
    {"state": "Meghalaya", "district": "East Khasi Hills", "location": "NH-6 Shillong-Tamabil Highway", "base_elev": 1500, "base_slope": 32.0, "lithology": 2},
    {"state": "Meghalaya", "district": "South West Khasi Hills", "location": "Mawsynram Valley Slopes", "base_elev": 1300, "base_slope": 35.0, "lithology": 2},
    {"state": "Assam", "district": "Dima Hasao", "location": "NH-27 Lumding-Haflong Hill Cut", "base_elev": 750, "base_slope": 33.0, "lithology": 1},
    {"state": "Assam", "district": "Karbi Anglong", "location": "Diphu-Bokajan Escarpment", "base_elev": 450, "base_slope": 26.0, "lithology": 1},
    {"state": "Arunachal Pradesh", "district": "West Kameng", "location": "Bhalukpong-Bomdila-Tawang Route", "base_elev": 2200, "base_slope": 42.0, "lithology": 5},
    {"state": "Arunachal Pradesh", "district": "Lower Subansiri", "location": "Ziro Foothill Section", "base_elev": 1550, "base_slope": 31.0, "lithology": 4},
    {"state": "Manipur", "district": "Noney", "location": "Tupul Railway Corridor Section", "base_elev": 820, "base_slope": 39.0, "lithology": 3},
    {"state": "Manipur", "district": "Chandel", "location": "NH-102 Imphal-Moreh Corridor", "base_elev": 950, "base_slope": 30.0, "lithology": 3},
    {"state": "Mizoram", "district": "Aizawl", "location": "Aizawl-Lunglei Road Slopes", "base_elev": 1150, "base_slope": 37.0, "lithology": 2},
    {"state": "Mizoram", "district": "Champhai", "location": "Champhai-Zokhawthar Border Cut", "base_elev": 1350, "base_slope": 33.0, "lithology": 2},
    {"state": "Tripura", "district": "North Tripura", "location": "Jampui Hills Ridge Corridor", "base_elev": 650, "base_slope": 28.0, "lithology": 1},
]


def generate_synthetic_ner_dataset(n_samples: int = 5000, random_seed: int = 42) -> pd.DataFrame:
    """
    Generates a realistic synthetic geomorphological and hydrometeorological dataset.

    Physics-guided empirical logic:
    - High slope inclination (> 30 deg), low distance to thrust/faults, and high TWI
      increase baseline terrain susceptibility.
    - Extreme 24h rainfall (> 60 mm) and high 72h antecedent rainfall saturate soil moisture
      and spike pore water pressure, triggering slope movement.
    """
    rng = np.random.default_rng(random_seed)

    records = []
    zone_indices = rng.choice(len(NER_REFERENCE_ZONES), size=n_samples)

    for i in range(n_samples):
        zone = NER_REFERENCE_ZONES[zone_indices[i]]

        # 1. Terrain Geomorphology (DEM derivatives)
        elevation_m = max(50.0, rng.normal(zone["base_elev"], 250.0))
        # Slope with realistic natural spread around representative location
        slope_deg = np.clip(rng.normal(zone["base_slope"], 8.0), 2.0, 75.0)
        aspect_deg = rng.uniform(0.0, 360.0)
        profile_curvature = rng.normal(0.0, 0.05)
        plan_curvature = rng.normal(0.0, 0.05)
        # Topographic Wetness Index: higher in concavities and base of slopes
        twi = np.clip(rng.normal(8.0 - (slope_deg * 0.08), 1.5), 2.0, 18.0)

        # Distance to geological fault/thrust line (meters)
        dist_to_fault_m = rng.exponential(scale=1200.0)
        # Distance to drainage/river (meters)
        dist_to_drainage_m = rng.exponential(scale=350.0)

        # Lithology code: 1: Alluvium/Terrace, 2: Sandstone/Shale, 3: Flysch/Siltstone, 4: Schist/Phyllite, 5: Gneiss/Quartzite
        lithology_code = int(np.clip(rng.normal(zone["lithology"], 0.6), 1, 5))
        # LULC code: 1: Dense Forest, 2: Open Scrub, 3: Road Cut / Deforested Slope, 4: Built-up / Settlement
        lulc_code = rng.choice([1, 2, 3, 4], p=[0.35, 0.25, 0.25, 0.15])

        # 2. Hydrometeorological Factors
        # Monsoon precipitation simulation (skewed distribution)
        is_monsoon_event = rng.random() < 0.40
        if is_monsoon_event:
            rainfall_24h_mm = rng.gamma(shape=3.0, scale=35.0)  # Heavy rain regime
            rainfall_72h_antecedent_mm = rainfall_24h_mm * rng.uniform(1.5, 3.2)
            rainfall_intensity_mm_h = np.clip(rainfall_24h_mm / rng.uniform(3.0, 8.0), 0.0, 80.0)
        else:
            rainfall_24h_mm = rng.exponential(scale=12.0)  # Dry/light rain regime
            rainfall_72h_antecedent_mm = rainfall_24h_mm * rng.uniform(0.5, 1.8)
            rainfall_intensity_mm_h = np.clip(rainfall_24h_mm / rng.uniform(6.0, 15.0), 0.0, 20.0)

        # 3. Geotechnical / Ground Sensors
        # Soil moisture is driven by antecedent rain and drainage
        moisture_base = 35.0 + min(rainfall_72h_antecedent_mm * 0.25, 45.0) + (10.0 if twi > 10.0 else 0.0)
        soil_moisture_pct = np.clip(rng.normal(moisture_base, 6.0), 10.0, 98.0)

        # Pore water pressure in kPa (increases rapidly when soil moisture nears saturation > 75%)
        if soil_moisture_pct > 75.0:
            pore_pressure_kpa = (soil_moisture_pct - 75.0) * rng.uniform(1.2, 2.5) + rng.normal(8.0, 2.0)
        else:
            pore_pressure_kpa = rng.normal(2.0, 1.5)
        pore_pressure_kpa = max(0.0, pore_pressure_kpa)

        # Ground displacement / tilt rate (mm/hour)
        if soil_moisture_pct > 82.0 and slope_deg > 32.0 and rainfall_24h_mm > 50.0:
            tilt_rate_mm_h = rng.exponential(scale=2.5)
        else:
            tilt_rate_mm_h = max(0.0, rng.normal(0.05, 0.04))

        # 4. Physical Slope Failure Probability (Latent score)
        # Factor 1: Static Susceptibility (Terrain + Geology + Road Cut)
        f_slope = (slope_deg / 45.0) ** 1.8
        f_fault = np.exp(-dist_to_fault_m / 800.0) * 1.5
        f_drainage = np.exp(-dist_to_drainage_m / 250.0) * 1.2
        f_litho = (lithology_code / 5.0) * 1.4
        f_lulc = 1.8 if lulc_code == 3 else (1.2 if lulc_code == 2 else 0.6)  # Road cuts are highly vulnerable
        static_score = 0.35 * f_slope + 0.15 * f_fault + 0.15 * f_drainage + 0.15 * f_litho + 0.20 * f_lulc

        # Factor 2: Dynamic Trigger (Rainfall intensity-duration + saturation + pore pressure)
        rain_trigger = (rainfall_24h_mm / 90.0) + (rainfall_72h_antecedent_mm / 180.0)
        moisture_trigger = (soil_moisture_pct / 85.0) ** 2.2
        pressure_trigger = min(pore_pressure_kpa / 25.0, 2.0)
        tilt_trigger = min(tilt_rate_mm_h / 2.0, 2.5)
        dynamic_score = 0.40 * rain_trigger + 0.30 * moisture_trigger + 0.15 * pressure_trigger + 0.15 * tilt_trigger

        # Total combined risk logit
        combined_logit = -4.5 + 2.8 * static_score + 2.4 * dynamic_score + rng.normal(0.0, 0.35)
        probability = 1.0 / (1.0 + np.exp(-combined_logit))

        # Binary label (1: Landslide occurred, 0: Stable slope)
        landslide_occurred = int(probability >= 0.50)

        records.append({
            "sample_id": f"NER-SIM-{i+1:05d}",
            "state": zone["state"],
            "district": zone["district"],
            "location_name": zone["location"],
            "elevation_m": round(elevation_m, 1),
            "slope_deg": round(slope_deg, 2),
            "aspect_deg": round(aspect_deg, 1),
            "profile_curvature": round(profile_curvature, 4),
            "plan_curvature": round(plan_curvature, 4),
            "topographic_wetness_index": round(twi, 2),
            "dist_to_fault_m": round(dist_to_fault_m, 1),
            "dist_to_drainage_m": round(dist_to_drainage_m, 1),
            "lithology_code": lithology_code,
            "lulc_code": lulc_code,
            "rainfall_24h_mm": round(rainfall_24h_mm, 1),
            "rainfall_72h_antecedent_mm": round(rainfall_72h_antecedent_mm, 1),
            "rainfall_intensity_mm_h": round(rainfall_intensity_mm_h, 2),
            "soil_moisture_pct": round(soil_moisture_pct, 1),
            "pore_water_pressure_kpa": round(pore_pressure_kpa, 2),
            "tilt_rate_mm_h": round(tilt_rate_mm_h, 3),
            "failure_probability": round(probability, 4),
            "landslide_occurred": landslide_occurred,
        })

    df = pd.DataFrame(records)
    return df


def save_prototype_dataset(output_path: str = "data/raw/ner_landslide_simulated_dataset.csv", n_samples: int = 6000) -> Path:
    """Generates and persists the prototype dataset to disk."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    df = generate_synthetic_ner_dataset(n_samples=n_samples, random_seed=42)
    df.to_csv(out_file, index=False)
    print(f"Generated prototype dataset: {out_file} ({len(df)} samples, {df['landslide_occurred'].mean():.1%} positive rate)")
    return out_file


if __name__ == "__main__":
    save_prototype_dataset()
