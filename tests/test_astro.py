"""The ephemeris pinned to things that cannot be argued with: a known full
Moon, a known eclipse seen from two places, and the geometry of a radiant.
Everything is computed, so these are offline and deterministic."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import server  # noqa: E402

astro = server.astro

MELBOURNE = (-37.81, 144.96)
LONDON = (51.5, -0.12)
REYKJAVIK = (64.15, -21.94)
GREATEST_2026_03_03 = datetime(2026, 3, 3, 11, 34, tzinfo=timezone.utc)


def test_full_moon_on_2026_03_03():
    """NASA's total lunar eclipse of 2026 March 3: the Moon is full to the
    last fraction of a percent at greatest eclipse."""
    m = astro.moon(astro.day_number_from(GREATEST_2026_03_03))
    assert m["illum"] > 0.995
    assert astro.phase_name(m["illum"], m["waxing"]) == "Full moon"


def test_new_moon_two_weeks_later_is_dark():
    m = astro.moon(astro.day_number_from(GREATEST_2026_03_03 + timedelta(days=15.2)))
    assert m["illum"] < 0.05


def test_moon_altitude_sign_at_greatest_eclipse():
    """NASA lists the 2026 March 3 eclipse as visible from Australia and the
    Americas, not Europe. At 11:34 UT the Moon is up over Melbourne (late
    evening there) and below the horizon in London (late morning)."""
    assert astro.body_altitude("moon", GREATEST_2026_03_03, *MELBOURNE) > 20
    assert astro.body_altitude("moon", GREATEST_2026_03_03, *LONDON) < -20


def test_sun_is_up_at_noon_and_down_at_midnight():
    noon = datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc)
    assert astro.body_altitude("sun", noon, *LONDON) > 55
    assert astro.body_altitude("sun", noon + timedelta(hours=12), *LONDON) < -10


def test_geminid_radiant_altitude_follows_latitude():
    """The Geminid radiant sits at Dec +33, so it culminates at 90 - |lat - 33|:
    about 19 degrees from Melbourne and 59 from Reykjavik. Melbourne gets the
    shower low in the north; Reykjavik gets it high."""
    mel = datetime(2026, 12, 14, 2, 0, tzinfo=timezone(timedelta(hours=11)))
    rey = datetime(2026, 12, 14, 2, 0, tzinfo=timezone.utc)
    alt_mel, az_mel = astro.radiant_alt_az(112, 33, mel, *MELBOURNE)
    alt_rey, _az = astro.radiant_alt_az(112, 33, rey, *REYKJAVIK)
    assert 10 < alt_mel < 20
    assert 50 < alt_rey < 60
    assert alt_rey > alt_mel
    assert az_mel < 45 or az_mel > 315  # due north-ish from the south


def test_solar_longitude_instants_land_on_the_imo_dates():
    """Every 2026 maximum computed from the IMO's solar longitude should fall
    on the date the IMO printed for 2026 (give or take the UT day boundary
    for the handful that peak within an hour of midnight)."""
    tz = timezone.utc
    for row in server.data.SHOWERS:
        s = dict(zip(server.data.SHOWER_FIELDS, row))
        peak = server.shower_peak(s, 2026, tz)
        printed = datetime(2026, s["max"][0], s["max"][1], tzinfo=tz)
        assert abs((peak - printed).total_seconds()) < 36 * 3600, s["code"]
