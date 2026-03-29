import json
import os
from unittest.mock import MagicMock

import pytest

from cliany_site.config import reset_config


@pytest.fixture(autouse=True)
def _reset_config_singleton():
    """每个测试前后重置 config 单例，避免测试间状态泄漏"""
    reset_config()
    yield
    reset_config()


@pytest.fixture()
def clean_env(monkeypatch):
    """清除所有 CLIANY_ 开头的环境变量"""
    for key in list(os.environ):
        if key.startswith("CLIANY_"):
            monkeypatch.delenv(key, raising=False)


@pytest.fixture
def tmp_adapters_dir(tmp_path):
    d = tmp_path / "adapters"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def mock_cdp():
    return MagicMock()


@pytest.fixture
def sample_metadata():
    return {"domain": "example.com", "commands": [], "schema_version": "1"}


@pytest.fixture
def sample_adapter_dir(tmp_path, sample_metadata):
    d = tmp_path / "adapters" / "example.com"
    d.mkdir(parents=True)
    (d / "metadata.json").write_text(json.dumps(sample_metadata))
    (d / "commands.py").write_text(
        "import click\n\n@click.group()\ndef cli():\n    pass\n"
    )
    return d
