from app.services.anomaly import detect_anomalies, isolation_forest_flags, zscore_flags


def test_zscore_flags_identifies_outliers():
    flags = zscore_flags([1, 1, 1, 20], threshold=1.5)
    assert flags[-1] == 1
    assert sum(flags) == 1


def test_isolation_forest_flags_marks_outlier():
    flags = isolation_forest_flags([1, 1, 2, 50], contamination=0.25)
    assert len(flags) == 4
    assert sum(flags) >= 1


def test_detect_anomalies_combines_methods():
    result = detect_anomalies({"latency_ms": [10, 11, 9, 100]}, threshold=2.0, contamination=0.2)
    assert "latency_ms" in result
    assert "zscore" in result["latency_ms"]
    assert len(result["latency_ms"]["zscore"]) == 4
