from __future__ import annotations

from typing import Dict, List, Tuple


def validate_dataset_size(num_samples: int, *, min_samples: int = 100, max_samples: int = 1_000_000) -> List[str]:
    warnings: List[str] = []
    if num_samples < min_samples:
        warnings.append(
            f"tiny-dataset: dataset has {num_samples} samples; DP may degrade utility. Consider collecting more data or aggregating rounds."
        )
    if num_samples > max_samples:
        warnings.append(
            f"massive-dataset: dataset has {num_samples} samples; enable streaming/batching and monitor memory."
        )
    return warnings


def detect_imbalance(class_counts: Dict[str, int], *, severe_ratio: float = 0.01) -> List[str]:
    warnings: List[str] = []
    total = sum(class_counts.values()) or 1
    min_ratio = min(c / total for c in class_counts.values()) if class_counts else 1.0
    if min_ratio <= severe_ratio:
        warnings.append(
            f"class-imbalance: minority class ratio {min_ratio:.4f} ≤ {severe_ratio}; consider reweighting/oversampling."
        )
    return warnings


def check_missing_values(missing_fraction: float, *, high: float = 0.1) -> List[str]:
    warnings: List[str] = []
    if missing_fraction > 0:
        warnings.append("missing-values: dataset contains missing values; apply imputation or drop rows/cols.")
    if missing_fraction >= high:
        warnings.append(
            f"high-missingness: missing fraction {missing_fraction:.2f} ≥ {high}; results may be unreliable."
        )
    return warnings


def check_high_dimensionality(num_features: int, *, high_dim_threshold: int = 10_000) -> List[str]:
    warnings: List[str] = []
    if num_features >= high_dim_threshold:
        warnings.append(
            f"high-dimensional: {num_features} features ≥ {high_dim_threshold}; consider PCA/feature selection and adjust DP budget."
        )
    return warnings


def validate_schema(participant_schemas: Dict[str, List[str]]) -> Tuple[bool, List[str]]:
    """Return (is_consistent, warnings) based on feature name alignment across participants."""
    warnings: List[str] = []
    if not participant_schemas:
        return True, warnings
    schemas = list(participant_schemas.values())
    base = set(schemas[0])
    for pid, schema in participant_schemas.items():
        if set(schema) != base:
            warnings.append(f"schema-mismatch: participant {pid} schema differs; harmonize features.")
    return len(warnings) == 0, warnings
