"""End-to-end smoke verification tests corresponding to scripts/smoke.sh and TESTING.md §9."""

def test_smoke_endpoints_suite(app_client):
    # 1. Health check: 200 OK
    res_health = app_client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"

    # 2. Meta endpoint: 200 OK with window metadata
    res_meta = app_client.get("/api/meta")
    assert res_meta.status_code == 200
    meta_json = res_meta.json()
    assert meta_json["window"]["expected_periods"] == 744
    assert meta_json["window"]["start_date"] == "2026-01-01"
    assert meta_json["window"]["end_date"] == "2026-01-31"

    # 3. Summary endpoint: 200 OK with positive matched count and non-null MAE
    res_summary = app_client.get("/api/summary?cutoff_time=09:00")
    assert res_summary.status_code == 200
    summary_json = res_summary.json()
    assert summary_json["metrics"]["n_matched"] > 0
    assert summary_json["metrics"]["mae_mw"] is not None

    # 4. Series endpoint: 200 OK with non-empty points array
    res_series = app_client.get("/api/series?granularity=hourly")
    assert res_series.status_code == 200
    series_json = res_series.json()
    assert isinstance(series_json["points"], list)
    assert len(series_json["points"]) > 0

    # 5. Records endpoint: 200 OK with items list <= page_size
    res_records = app_client.get("/api/records?page=1&page_size=50")
    assert res_records.status_code == 200
    records_json = res_records.json()
    assert isinstance(records_json["items"], list)
    assert 0 < len(records_json["items"]) <= 50

    # 6. Parameter validation: 400 Bad Request on invalid cutoff
    res_invalid = app_client.get("/api/summary?cutoff_time=99:99")
    assert res_invalid.status_code == 400
    assert res_invalid.json()["error"]["code"] == "INVALID_PARAMETER"

