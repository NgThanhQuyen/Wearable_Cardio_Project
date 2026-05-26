from pathlib import Path

from backend.core import database


def test_save_alert_and_recent_history(tmp_path, monkeypatch):
    db_file = tmp_path / "history.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))

    database.init_db()
    database.save_alert("PT-001", 82.5, 97.2, 12.3)

    history = database.get_recent_history(limit=1)

    assert len(history) == 1
    row = history[0]
    assert row["patient_id"] == "PT-001"
    assert row["hr"] == 82.5
    assert row["spo2"] == 97.2
    assert row["risk_score"] == 12.3
    assert "T" in row["timestamp"]
    assert row["timestamp"].endswith("+00:00")