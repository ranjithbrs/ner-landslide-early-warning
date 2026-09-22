"""
Feature engineering and preprocessing pipeline definitions for Landslide Prediction.
Ensures strict featurization ordering and clean separation of numerical and categorical variables.
"""

from typing import List, Tuple
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Numerical features representing continuous geomorphological, meteorological, and sensor readings
NUMERICAL_FEATURES: List[str] = [
    "elevation_m",
    "slope_deg",
    "aspect_deg",
    "profile_curvature",
    "plan_curvature",
    "topographic_wetness_index",
    "dist_to_fault_m",
    "dist_to_drainage_m",
    "rainfall_24h_mm",
    "rainfall_72h_antecedent_mm",
    "rainfall_intensity_mm_h",
    "soil_moisture_pct",
    "pore_water_pressure_kpa",
    "tilt_rate_mm_h",
]

# Categorical features representing discrete geological classes and land use categories
CATEGORICAL_FEATURES: List[str] = [
    "lithology_code",
    "lulc_code",
]

ALL_MODEL_FEATURES: List[str] = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
TARGET_COLUMN: str = "landslide_occurred"


def build_preprocessor() -> ColumnTransformer:
    """
    Builds a scikit-learn ColumnTransformer for preprocessing.
    - Numerical: Median Imputation -> StandardScaler
    - Categorical: Most Frequent Imputation -> OneHotEncoder
    """
    numerical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numerical_transformer, NUMERICAL_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )
    return preprocessor


def extract_feature_matrix(df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
    """Extracts feature DataFrame X and binary label vector y from a dataset."""
    missing_cols = [col for col in ALL_MODEL_FEATURES if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset is missing required feature columns: {missing_cols}")

    X = df[ALL_MODEL_FEATURES].copy()
    y = df[TARGET_COLUMN].values.astype(int) if TARGET_COLUMN in df.columns else None
    return X, y
