"""The shaping: next-event picking across a year end, eclipse visibility,
the continent lookup, and fetch() never raising."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import server  # noqa: E402

data = server.data
MEL_TZ = ZoneInfo("Australia/Melbourne")
LON_TZ = ZoneInfo("Europe/London")
MEL = (-37.81, 144.96)
LON = (51.5, -0.12)


def _build(now, lat, lon, tz, **opts):
    return server.build({"timezone": tz.key, **opts}, now, lat, lon, tz)


def test_next_event_crosses_the_year_boundary():
    """On 30 December 2026 from London the Geminids and Ursids are gone and
    the next event is the Quadrantids: the IMO maximum is 2027 January 3 at
    about 21:40 UT, so the night of 3 to 4 January."""
    out = _build(datetime(2026, 12, 30, 20, 0, tzinfo=LON_TZ), *LON, LON_TZ)
    nxt = out["events"][out["next"]]
    assert nxt["code"] == "QUA"
    assert nxt["date"] == "2027-01-03"
    assert nxt["night"] == "3–4 Jan"
    assert nxt["days_to"] == 4
    passed = [e["code"] for e in out["events"] if e["past"]]
    assert "GEM" in passed and "URS" in passed


def test_peak_night_in_progress_still_counts_as_tonight():
    """The 2026 Geminid maximum is December 14 at about 14 h UT, so the peak
    night is 14 to 15 December. At 1 am on the 15th the night is not over."""
    out = _build(datetime(2026, 12, 15, 1, 0, tzinfo=LON_TZ), *LON, LON_TZ)
    gem = next(e for e in out["events"] if e["code"] == "GEM")
    assert gem["night"] == "14–15 Dec"
    assert gem["days_to"] == 0
    assert not gem["past"]


def test_span_and_positions():
    out = _build(datetime(2026, 10, 28, 12, 0, tzinfo=MEL_TZ), *MEL, MEL_TZ, months="4")
    assert out["span"]["start"] == "2026-10-01"
    assert out["span"]["end"] == "2027-02-01"
    assert [m["short"] for m in out["span"]["months"]] == ["Oct", "Nov", "Dec", "Jan"]
    assert out["span"]["days"] == 31 + 30 + 31 + 31
    for e in out["events"]:
        assert e["in_span"] == (0.0 <= e["pos"] <= 1.0)


def test_lunar_eclipse_visibility_depends_on_the_place():
    """2026 March 3, total: up over Melbourne, below the horizon in London."""
    mel = _build(datetime(2026, 2, 20, 12, 0, tzinfo=MEL_TZ), *MEL, MEL_TZ)
    lon = _build(datetime(2026, 2, 20, 12, 0, tzinfo=LON_TZ), *LON, LON_TZ)
    assert next(e for e in mel["events"] if e["code"] == "LE2026-03-03")["visible"]
    assert not next(e for e in lon["events"] if e["code"] == "LE2026-03-03")["visible"]


def test_solar_eclipse_visibility_by_continent():
    """2026 August 12: Europe sees partial phases, Australia sees nothing."""
    mel = _build(datetime(2026, 8, 1, 12, 0, tzinfo=MEL_TZ), *MEL, MEL_TZ)
    lon = _build(datetime(2026, 8, 1, 12, 0, tzinfo=LON_TZ), *LON, LON_TZ)
    assert next(e for e in lon["events"] if e["code"] == "SE2026-08-12")["visible"]
    assert not next(e for e in mel["events"] if e["code"] == "SE2026-08-12")["visible"]


def test_eclipse_time_is_ut_from_td_in_local_clock():
    """Greatest eclipse 11:34:52 TD minus 69 s is 11:33:43 UT, which is
    22:33 in Melbourne (UT+11 in March)."""
    out = _build(datetime(2026, 2, 20, 12, 0, tzinfo=MEL_TZ), *MEL, MEL_TZ)
    e = next(e for e in out["events"] if e["code"] == "LE2026-03-03")
    assert e["time"] == "22:33"
    assert e["date"] == "2026-03-03"


def test_only_visible_hides_what_cannot_be_seen():
    out = _build(
        datetime(2026, 10, 28, 12, 0, tzinfo=MEL_TZ), *MEL, MEL_TZ, only_visible=True
    )
    assert all(e["visible"] for e in out["events"])
    codes = {e["code"] for e in out["events"]}
    assert "GEM" in codes
    assert "URS" not in codes  # Dec +76 never rises from 38 S


def test_show_eclipses_off_drops_them():
    out = _build(
        datetime(2026, 10, 28, 12, 0, tzinfo=MEL_TZ), *MEL, MEL_TZ, show_eclipses=False
    )
    assert all(e["kind"] == "shower" for e in out["events"])


def test_moon_report_words_are_well_formed():
    out = _build(datetime(2026, 10, 28, 12, 0, tzinfo=MEL_TZ), *MEL, MEL_TZ)
    for e in out["events"]:
        if e["kind"] != "shower":
            continue
        note = e["moon"]["note"]
        assert note == "No moonlight" or note.startswith("Moon ")
        assert (
            e["radiant"]["words"] in ("well placed", "below the horizon")
            or " in the " in e["radiant"]["words"]
        )


def test_continent_lookup():
    assert data.continent(-37.81, 144.96) == "oceania"
    assert data.continent(51.5, -0.12) == "europe"
    assert data.continent(40.7, -74.0) == "north_america"
    assert data.continent(-34.6, -58.4) == "south_america"
    assert data.continent(-33.9, 18.4) == "africa"
    assert data.continent(30.0, 31.2) == "africa"
    assert data.continent(35.7, 139.7) == "asia"
    assert data.continent(19.1, 72.9) == "asia"
    assert data.continent(64.15, -21.94) == "europe"
    assert data.continent(-36.8, 174.8) == "oceania"
    assert data.continent(21.3, -157.9) == "oceania"
    assert data.continent(-75.0, 0.0) == "antarctica"


def test_tables_are_well_formed():
    assert len(data.SHOWERS) == 13
    for row in data.SHOWERS:
        s = dict(zip(data.SHOWER_FIELDS, row))
        assert 0 <= s["ra"] < 360 and -90 <= s["dec"] <= 90
        assert s["zhr"] > 0 and 0 <= s["solar_lon"] < 360
    assert len(data.SOLAR_ECLIPSES) == 12 and len(data.LUNAR_ECLIPSES) == 12
    for row in data.SOLAR_ECLIPSES:
        assert row[2] in ("total", "annular", "partial")
        assert set(row[5]) <= set(data.CONTINENT_NAMES)
    for row in data.LUNAR_ECLIPSES:
        assert row[2] in ("total", "partial", "penumbral")


def test_fetch_without_a_place_returns_an_error_dict():
    out = server.fetch({}, {}, ctx={"data_dir": "/nonexistent"})
    assert "error" in out and "place" in out["error"]
    out = server.fetch({"latitude": "x", "longitude": 1}, {}, ctx={})
    assert "error" in out


def test_fetch_with_a_place_returns_data_without_network():
    out = server.fetch(
        {
            "latitude": -37.81,
            "longitude": 144.96,
            "label": "Melbourne",
            "timezone": "Australia/Melbourne",
        },
        {},
        ctx={"data_dir": "/nonexistent", "preview": True},
    )
    assert "error" not in out
    assert out["label"] == "Melbourne" and out["south"] is True
    assert out["next"] is not None and out["events"]
    assert out["title"] == "Meteors & Eclipses"
