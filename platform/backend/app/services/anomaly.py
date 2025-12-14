from typing import Dict, List

from sklearn.ensemble import IsolationForest


def zscore_flags(values: List[float], threshold: float = 3.0) -> List[int]:
    if not values:
        return []
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / max(len(values), 1)
    std = variance**0.5
    if std == 0:
        return [0 for _ in values]
    return [1 if abs(v - mean) / std >= threshold else 0 for v in values]


def isolation_forest_flags(values: List[float], contamination: float = 0.1) -> List[int]:
    if not values:
        return []
    model = IsolationForest(contamination=contamination, random_state=42)
    reshaped = [[v] for v in values]
    preds = model.fit_predict(reshaped)
    return [1 if p == -1 else 0 for p in preds]


def detect_anomalies(metrics: Dict[str, List[float]], threshold: float = 3.0, contamination: float = 0.1) -> Dict[str, Dict[str, List[int]]]:
    summary: Dict[str, Dict[str, List[int]]] = {}
    for key, values in metrics.items():
        summary[key] = {
            "zscore": zscore_flags(values, threshold=threshold),
            "isolation_forest": isolation_forest_flags(values, contamination=contamination),
        }
    return summary
