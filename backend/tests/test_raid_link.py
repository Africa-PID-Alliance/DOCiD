"""Tests for the RAiD link stored on publication projects (RAID_LINK_BASE_URL)."""
import pytest

from config import Config
from app.routes.publications import build_raid_link


@pytest.mark.parametrize("base_url", ["https://raid.org/", "https://raid.org"])
def test_bare_id_uses_configured_base(monkeypatch, base_url):
    monkeypatch.setattr(Config, "RAID_LINK_BASE_URL", base_url)
    assert build_raid_link("10.26259/0e59e9a5") == "https://raid.org/10.26259/0e59e9a5"


def test_bare_id_uses_demo_app_base(monkeypatch):
    monkeypatch.setattr(Config, "RAID_LINK_BASE_URL", "https://app.demo.raid.org.au/raids/")
    assert build_raid_link("10.80368/b1adfb3a") == "https://app.demo.raid.org.au/raids/10.80368/b1adfb3a"


@pytest.mark.parametrize("url", [
    "https://raid.org/10.26259/0e59e9a5",
    "https://app.demo.raid.org.au/raids/10.80368/b1adfb3a",
    "http://raid.org/10.26259/0e59e9a5",
])
def test_full_url_is_kept_as_entered(monkeypatch, url):
    monkeypatch.setattr(Config, "RAID_LINK_BASE_URL", "https://raid.org/")
    assert build_raid_link(url) == url
