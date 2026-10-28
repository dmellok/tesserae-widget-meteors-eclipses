"""meteors_eclipses: the showers and eclipses coming up, worked out for one place.

Nothing is fetched. The shower list and the eclipse table are bundled in
data.py and every local detail (how high the radiant gets, whether the
Moon is up, which eclipses clear the horizon) is computed here from the
cell's latitude and longitude with the small ephemeris in astro.py.

Returns a JSON-serialisable dict or {"error": "..."}; never raises.
"""

from __future__ import annotations

import importlib.util
from datetime import date, datetime, timedelta, timezone, tzinfo
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

_HERE = Path(__file__).resolve().parent


def _sibling(name: str):
    spec = importlib.util.spec_from_file_location(
        f"_tesserae_plugins.meteors_eclipses.{name}", _HERE / f"{name}.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


astro = _sibling("astro")
data = _sibling("data")

# General precession in longitude, degrees a year: the IMO prints solar
# longitudes for equinox J2000.0 and astro.sun() gives the longitude of
# date, so a maximum has to be nudged forward to land on the right day.
PRECESSION_DEG_PER_YEAR = 0.013968
LOOKAHEAD_DAYS = 400
DARK_SUN_ALT = -12.0


# ---------------------------------------------------------------- time zone


def _tz_from_name(name: Any) -> tzinfo | None:
    if not isinstance(name, str) or not name.strip():
        return None
    try:
        return ZoneInfo(name.strip())
    except (ValueError, KeyError, OSError):
        return None


def location_tz(options: dict[str, Any], lon: float) -> tzinfo:
    """The zone the place keeps its clocks in.

    A geocoded location carries its IANA zone; a pasted coordinate does
    not, and with no network there is nothing to ask. Then the server's
    own zone is used when it is plausible for the longitude, and otherwise
    the whole-hour solar offset, which is at worst an hour or so out.
    """
    for value in (options.get("timezone"), options.get("location")):
        if isinstance(value, dict):
            value = value.get("timezone")
        tz = _tz_from_name(value)
        if tz is not None:
            return tz
    server_now = datetime.now().astimezone()
    server_offset = (server_now.utcoffset() or timedelta(0)).total_seconds() / 3600.0
    solar = round(lon / 15.0)
    gap = ((server_offset - solar + 12.0) % 24.0) - 12.0
    if abs(gap) <= 2.5:
        return server_now.tzinfo or timezone.utc
    return timezone(timedelta(hours=max(-12, min(14, solar))))


# ---------------------------------------------------------------- formatting


def fmt_date(d: date) -> str:
    return f"{d.day} {d.strftime('%b')}"


def fmt_night(morning: date) -> str:
    """'13–14 Dec', or '31 Dec–1 Jan' across a month end."""
    evening = morning - timedelta(days=1)
    if evening.month == morning.month:
        return f"{evening.day}–{morning.day} {morning.strftime('%b')}"
    return f"{fmt_date(evening)}–{fmt_date(morning)}"


def fmt_hour(hour: int) -> str:
    hour %= 24
    if hour == 0:
        return "midnight"
    if hour == 12:
        return "noon"
    return f"{hour} am" if hour < 12 else f"{hour - 12} pm"


def fmt_clock(t: datetime) -> str:
    return t.strftime("%H:%M")


def compass(az: float) -> str:
    names = [
        "north",
        "north-east",
        "east",
        "south-east",
        "south",
        "south-west",
        "west",
        "north-west",
    ]
    return names[int(((az + 22.5) % 360) // 45)]


# ---------------------------------------------------------------- showers


def shower_peak(shower: dict, year: int, tz: tzinfo) -> datetime:
    """The local instant of the shower's maximum in a given year."""
    guess = datetime(year, shower["max"][0], shower["max"][1], 12, tzinfo=timezone.utc)
    target = shower["solar_lon"] + PRECESSION_DEG_PER_YEAR * (year - 2000)
    return astro.solar_longitude_instant(year, target, guess).astimezone(tz)


def peak_night(peak_local: datetime) -> date:
    """The morning date of the night nearest the maximum.

    A night runs from one evening to the next morning and is named by the
    morning. A maximum before local noon belongs to the night just ending;
    one after noon to the night about to start.
    """
    d = peak_local.date()
    return d if peak_local.hour < 12 else d + timedelta(days=1)


def _local(
    morning: date, hour: int, minute: int, tz: tzinfo, day_offset: int = 0
) -> datetime:
    return datetime.combine(
        morning + timedelta(days=day_offset), datetime.min.time(), tz
    ).replace(hour=hour, minute=minute)


def radiant_report(
    shower: dict, morning: date, tz: tzinfo, lat: float, lon: float
) -> dict:
    """Where the radiant sits at 2 am, and the best dark hour to look."""
    at_two = _local(morning, 2, 0, tz)
    alt2, az2 = astro.radiant_alt_az(shower["ra"], shower["dec"], at_two, lat, lon)
    if alt2 >= 40:
        words = "well placed"
    elif alt2 >= 15:
        words = f"low in the {compass(az2)}"
    elif alt2 > 0:
        words = f"very low in the {compass(az2)}"
    else:
        words = "below the horizon"

    # 10 pm on the evening through 6 am, hour by hour, while the sky is dark
    hours = []
    for i in range(9):
        t = _local(morning, 22, 0, tz, day_offset=-1) + timedelta(hours=i)
        sun_alt = astro.body_altitude("sun", t, lat, lon)
        alt, _az = astro.radiant_alt_az(shower["ra"], shower["dec"], t, lat, lon)
        hours.append((t, sun_alt, alt))
    dark = [h for h in hours if h[1] < DARK_SUN_ALT]
    if not dark:  # a bright summer night at high latitude: take the darkest hour
        dark = [min(hours, key=lambda h: h[1])]
    best = max(dark, key=lambda h: h[2])
    highest = best[2]
    if highest <= 0:
        best_words = "radiant never rises"
    elif best is dark[-1] and len(dark) > 1 and dark[-1][2] > dark[-2][2]:
        best_words = "before dawn"
    else:
        best_words = f"around {fmt_hour(best[0].hour)}"
    return {
        "alt": round(alt2),
        "dir": compass(az2),
        "words": words,
        "best": best_words,
        "best_hour": best[0].hour if highest > 0 else None,
        "rises": highest > 0,
        "never_dark": all(h[1] >= DARK_SUN_ALT for h in hours),
    }


def moon_report(morning: date, tz: tzinfo, lat: float, lon: float) -> dict:
    """The Moon on one night: phase at 2 am, when it rises or sets, and
    whether it is up between midnight and 4 am."""
    at_two = _local(morning, 2, 0, tz)
    m = astro.moon(astro.day_number_from(at_two))
    illum = m["illum"]
    samples = []
    t = _local(morning, 17, 0, tz, day_offset=-1)
    end = _local(morning, 7, 0, tz)
    while t <= end:
        samples.append((t, astro.body_altitude("moon", t, lat, lon)))
        t += timedelta(minutes=10)
    rises = sets = None
    for (t0, a0), (t1, a1) in zip(samples, samples[1:]):
        if a0 <= 0 < a1 and rises is None:
            rises = t1
        if a0 > 0 >= a1 and sets is None:
            sets = t1
    small = [a for (t, a) in samples if 0 <= t.hour < 4 and t.date() == morning]
    up = any(a > 0 for a in small)
    pct = round(illum * 100)
    if illum < 0.08:
        note = "No moonlight"
        verdict = "dark"
    elif not up:
        if sets is not None and sets.date() != morning:
            note = f"Moon {pct}% lit, sets {fmt_clock(sets)}"
        elif rises is not None:
            note = f"Moon {pct}% lit, rises {fmt_clock(rises)}"
        else:
            note = f"Moon {pct}% lit, below the horizon"
        verdict = "clear"
    else:
        if rises is not None and rises.date() != morning:
            note = f"Moon {pct}% lit, rises {fmt_clock(rises)}"
        elif rises is not None:
            note = f"Moon {pct}% lit, rises {fmt_clock(rises)}"
        elif sets is not None and sets.date() == morning:
            note = f"Moon {pct}% lit, sets {fmt_clock(sets)}"
        else:
            note = f"Moon {pct}% lit, up all night"
        verdict = "bright" if illum >= 0.5 else "some"
    return {
        "illum": pct,
        "frac": round(illum, 3),
        "waxing": bool(m["waxing"]),
        "phase": astro.phase_name(illum, m["waxing"]),
        "up": up,
        "rises": fmt_clock(rises) if rises else None,
        "sets": fmt_clock(sets) if sets else None,
        "note": note,
        "verdict": verdict,
    }


def shower_events(
    now_local: datetime, since: date, tz: tzinfo, lat: float, lon: float
) -> list[dict]:
    today = (now_local - timedelta(hours=6)).date()
    until = today + timedelta(days=LOOKAHEAD_DAYS)
    out = []
    for row in data.SHOWERS:
        s = dict(zip(data.SHOWER_FIELDS, row))
        for year in (now_local.year - 1, now_local.year, now_local.year + 1):
            peak = shower_peak(s, year, tz)
            morning = peak_night(peak)
            evening = morning - timedelta(days=1)
            if evening < since or evening > until:
                continue
            radiant = radiant_report(s, morning, tz, lat, lon)
            moon = moon_report(morning, tz, lat, lon)
            days_to = (evening - today).days
            start = date(
                evening.year if s["start"][0] <= evening.month else evening.year - 1,
                *s["start"],
            )
            end = date(
                evening.year if s["end"][0] >= evening.month else evening.year + 1,
                *s["end"],
            )
            out.append(
                {
                    "kind": "shower",
                    "code": s["code"],
                    "name": s["name"],
                    "date": evening.isoformat(),
                    "when": fmt_date(evening),
                    "night": fmt_night(morning),
                    "days_to": days_to,
                    "past": days_to < 0,
                    "zhr": s["zhr"],
                    "variable": s["variable"],
                    "parent": s["parent"],
                    "active": f"{fmt_date(start)} to {fmt_date(end)}",
                    "radiant": radiant,
                    "moon": moon,
                    "visible": radiant["rises"],
                }
            )
    return out


# ---------------------------------------------------------------- eclipses


def _eclipse_instant(day: str, td: str) -> datetime:
    y, mo, d = (int(x) for x in day.split("-"))
    h, mi, s = (int(x) for x in td.split(":"))
    return datetime(y, mo, d, h, mi, s, tzinfo=timezone.utc) - timedelta(
        seconds=data.DELTA_T_S
    )


def eclipse_events(
    now_local: datetime, since: date, tz: tzinfo, lat: float, lon: float
) -> list[dict]:
    today = (now_local - timedelta(hours=6)).date()
    until = today + timedelta(days=LOOKAHEAD_DAYS)
    here = data.continent(lat, lon)
    out = []
    for day, td, kind, path, region, tags in data.SOLAR_ECLIPSES:
        at = _eclipse_instant(day, td).astimezone(tz)
        local_day = at.date()
        if local_day < since or local_day > until:
            continue
        visible = here in tags
        if visible:
            note = f"Partial phases reach {data.CONTINENT_NAMES[here]}"
        else:
            note = "Not visible from here"
        name = f"{kind.capitalize()} solar eclipse"
        out.append(
            {
                "kind": "eclipse",
                "body": "solar",
                "type": kind,
                "code": "SE" + day,
                "name": name,
                "date": local_day.isoformat(),
                "when": fmt_date(local_day),
                "time": fmt_clock(at),
                "days_to": (local_day - today).days,
                "past": local_day < today,
                "visible": visible,
                "note": note,
                "path": path,
                "region": region,
            }
        )
    for day, td, kind, mag, region in data.LUNAR_ECLIPSES:
        at_utc = _eclipse_instant(day, td)
        at = at_utc.astimezone(tz)
        local_day = at.date()
        if local_day < since or local_day > until:
            continue
        alt = astro.body_altitude("moon", at, lat, lon)
        visible = alt > 0
        if visible:
            note = f"Moon {round(alt)}° up at greatest eclipse, {fmt_clock(at)}"
        else:
            note = "Moon below the horizon at greatest eclipse"
        out.append(
            {
                "kind": "eclipse",
                "body": "lunar",
                "type": kind,
                "code": "LE" + day,
                "name": f"{kind.capitalize()} lunar eclipse",
                "date": local_day.isoformat(),
                "when": fmt_date(local_day),
                "time": fmt_clock(at),
                "days_to": (local_day - today).days,
                "past": local_day < today,
                "visible": visible,
                "alt": round(alt),
                "magnitude": mag,
                "note": note,
                "region": region,
            }
        )
    return out


# ---------------------------------------------------------------- timeline


def month_span(first: date, months: int) -> dict:
    cols = []
    cursor = first
    total = 0
    for _ in range(months):
        nxt = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
        days = (nxt - cursor).days
        cols.append(
            {
                "name": cursor.strftime("%B"),
                "short": cursor.strftime("%b"),
                "days": days,
                "offset": total,
            }
        )
        total += days
        cursor = nxt
    return {
        "start": first.isoformat(),
        "end": cursor.isoformat(),
        "days": total,
        "months": cols,
    }


def pick_next(events: list[dict]) -> int | None:
    for i, e in enumerate(events):
        if not e["past"]:
            return i
    return None


# ---------------------------------------------------------------- fetch


def _bool(v: Any, default: bool) -> bool:
    if v is None or v == "":
        return default
    if isinstance(v, str):
        return v.strip().lower() not in ("0", "false", "no", "off")
    return bool(v)


def build(
    options: dict[str, Any], now_local: datetime, lat: float, lon: float, tz: tzinfo
) -> dict:
    """Everything the client draws, from options and a clock. Pure, so tests
    can hand it any moment."""
    layout = str(options.get("layout") or "timeline")
    try:
        months = int(options.get("months") or 4)
    except (TypeError, ValueError):
        months = 4
    months = months if months in (3, 4, 6) else 4
    show_eclipses = _bool(options.get("show_eclipses"), True)
    only_visible = _bool(options.get("only_visible"), False)

    first = now_local.date().replace(day=1)
    span = month_span(first, months)
    events = shower_events(now_local, first, tz, lat, lon)
    if show_eclipses:
        events += eclipse_events(now_local, first, tz, lat, lon)
    if only_visible:
        events = [e for e in events if e["visible"]]
    events.sort(key=lambda e: (e["date"], e["kind"]))

    start = date.fromisoformat(span["start"])
    for e in events:
        offset = (date.fromisoformat(e["date"]) - start).days + 0.5
        e["pos"] = round(offset / span["days"], 4)
        e["in_span"] = 0.0 <= e["pos"] <= 1.0

    nxt = pick_next(events)
    upcoming = events[nxt + 1 : nxt + 4] if nxt is not None else []
    title = options.get("title")
    return {
        "label": str(options.get("label") or "").strip(),
        "lat": round(lat, 3),
        "lon": round(lon, 3),
        "south": lat < 0,
        "continent": data.CONTINENT_NAMES[data.continent(lat, lon)],
        "today": now_local.date().isoformat(),
        "now": now_local.strftime("%H:%M"),
        "layout": layout,
        "months": months,
        "show_eclipses": show_eclipses,
        "only_visible": only_visible,
        "title": "Meteors & Eclipses" if title is None else str(title),
        "span": span,
        "events": events,
        "next": nxt,
        "upcoming": [
            {
                "name": u["name"],
                "when": u["when"],
                "days_to": u["days_to"],
                "kind": u["kind"],
                "visible": u["visible"],
            }
            for u in upcoming
        ],
    }


def fetch(
    options: dict[str, Any], settings: dict[str, Any], *, ctx: dict[str, Any]
) -> dict[str, Any]:
    try:
        lat = float(options.get("latitude"))
        lon = float(options.get("longitude"))
    except (TypeError, ValueError):
        return {
            "error": "Set a place in this cell's settings, or an app-level location, to work out the sky from there."
        }
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return {
            "error": "That place has a latitude or longitude outside the map. Check the location in this cell's settings."
        }
    try:
        tz = location_tz(options, lon)
        now_local = datetime.now(tz)
        return build(options, now_local, lat, lon, tz)
    except Exception:  # noqa: BLE001, the cell shows a sentence rather than a trace
        return {"error": "Couldn't work out the sky for this place right now."}
