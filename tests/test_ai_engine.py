from backend.core import ai_engine


def test_env_flag_parsing():
    assert ai_engine._env_flag("FLAG_NOT_SET", default="false") is False
    assert ai_engine._env_flag("FLAG_NOT_SET_TRUE", default="true") is True


def test_env_flag_truthy_values(monkeypatch):
    monkeypatch.setenv("CARDIO_TEST_FLAG", "YES")
    assert ai_engine._env_flag("CARDIO_TEST_FLAG") is True
