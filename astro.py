"""Small low-precision ephemerides for the Meteors & Eclipses widget.

Everything here is a few lines of Keplerian orbit arithmetic after Paul
Schlyter's "How to compute planetary positions". The Sun comes out to a
few arcminutes and the Moon to a fraction of a degree, which is more than
enough to say whether the Moon is above the horizon, how full it is and
how high a shower's radiant climbs. Nothing is fetched; nothing depends on
the clock except what the caller passes in.

Conventions: angles in degrees, times in UT, "d" is Schlyter's day number
(days since 2000 January 0.0), longitudes east-positive.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

RAD = math.pi / 180.0
DEG = 180.0 / math.pi


def wrap(x: float) -> float:
    """Fold an angle into [0, 360)."""
    return x % 360.0


def day_number(year: int, month: int, day: int, ut_hours: float = 0.0) -> float:
    """Schlyter's day number: days since 2000 Jan 0.0, with a fraction."""
    whole = (
        367 * year
        - 7 * (year + (month + 9) // 12) // 4
        + 275 * month // 9
        + day
        - 730530
    )
    return whole + ut_hours / 24.0


def day_number_from(when: datetime) -> float:
    """Day number for an aware datetime (converted to UT first)."""
    u = when.astimezone(timezone.utc)
    hours = u.hour + u.minute / 60.0 + u.second / 3600.0
    return day_number(u.year, u.month, u.day, hours)


def obliquity(d: float) -> float:
    return 23.4393 - 3.563e-7 * d


def _kepler(mean_anomaly: float, e: float) -> float:
    """Eccentric anomaly from the mean anomaly, iterated to a milli-degree."""
    m = mean_anomaly * RAD
    ecc = m + e * math.sin(m) * (1.0 + e * math.cos(m))
    for _ in range(6):
        step = (ecc - e * math.sin(ecc) - m) / (1.0 - e * math.cos(ecc))
        ecc -= step
        if abs(step) < 1e-7:
            break
    return ecc * DEG


def _true_anomaly_and_distance(mean_anomaly: float, e: float, a: float):
    ecc = _kepler(mean_anomaly, e) * RAD
    xv = a * (math.cos(ecc) - e)
    yv = a * math.sqrt(1.0 - e * e) * math.sin(ecc)
    return wrap(math.atan2(yv, xv) * DEG), math.hypot(xv, yv)


def _ecliptic_to_equatorial(lon: float, lat: float, obl: float):
    """Ecliptic lon/lat (deg) -> RA/Dec (deg)."""
    cl = math.cos(lat * RAD)
    x = cl * math.cos(lon * RAD)
    y = cl * math.sin(lon * RAD)
    z = math.sin(lat * RAD)
    ye = y * math.cos(obl * RAD) - z * math.sin(obl * RAD)
    ze = y * math.sin(obl * RAD) + z * math.cos(obl * RAD)
    ra = wrap(math.atan2(ye, x) * DEG)
    dec = math.atan2(ze, math.hypot(x, ye)) * DEG
    return ra, dec


def sun(d: float) -> dict:
    """The Sun: RA, Dec, ecliptic longitude and the mean elements it needs."""
    w = 282.9404 + 4.70935e-5 * d
    e = 0.016709 - 1.151e-9 * d
    mean = wrap(356.0470 + 0.9856002585 * d)
    v, r = _true_anomaly_and_distance(mean, e, 1.0)
    lon = wrap(v + w)
    ra, dec = _ecliptic_to_equatorial(lon, 0.0, obliquity(d))
    return {"ra": ra, "dec": dec, "lon": lon, "r": r, "M": mean, "w": w}


def sidereal(d: float, ut_hours: float, lon_east: float) -> float:
    """Local sidereal time in degrees."""
    s = sun(d)
    gmst0 = wrap(s["M"] + s["w"] + 180.0)
    return wrap(gmst0 + ut_hours * 15.0 + lon_east)


def sidereal_at(when: datetime, lon_east: float) -> float:
    u = when.astimezone(timezone.utc)
    hours = u.hour + u.minute / 60.0 + u.second / 3600.0
    return sidereal(day_number(u.year, u.month, u.day, hours), hours, lon_east)


def alt_az(ra: float, dec: float, lst: float, lat: float):
    """Equatorial -> (altitude, azimuth from north through east), degrees."""
    h = (lst - ra) * RAD
    dr, lr = dec * RAD, lat * RAD
    s = math.sin(dr) * math.sin(lr) + math.cos(dr) * math.cos(lr) * math.cos(h)
    alt = math.asin(max(-1.0, min(1.0, s))) * DEG
    az = math.atan2(
        -math.cos(dr) * math.sin(h),
        math.sin(dr) * math.cos(lr) - math.cos(dr) * math.sin(lr) * math.cos(h),
    )
    return alt, wrap(az * DEG)


def moon(d: float) -> dict:
    """The Moon: RA, Dec, illuminated fraction and whether it is waxing.

    Schlyter's elements with the dozen largest perturbation terms, which
    brings the longitude to about a tenth of a degree. Good enough to call
    the horizon and the phase; nowhere near good enough for an eclipse,
    which is why eclipse timings come from NASA's table and not from here.
    """
    node = wrap(125.1228 - 0.0529538083 * d)
    incl = 5.1454
    perihelion = wrap(318.0634 + 0.1643573223 * d)
    a = 60.2666
    e = 0.054900
    mean = wrap(115.3654 + 13.0649929509 * d)

    v, r = _true_anomaly_and_distance(mean, e, a)
    arg = (v + perihelion) * RAD
    xh = r * (
        math.cos(node * RAD) * math.cos(arg)
        - math.sin(node * RAD) * math.sin(arg) * math.cos(incl * RAD)
    )
    yh = r * (
        math.sin(node * RAD) * math.cos(arg)
        + math.cos(node * RAD) * math.sin(arg) * math.cos(incl * RAD)
    )
    zh = r * math.sin(arg) * math.sin(incl * RAD)
    lon = wrap(math.atan2(yh, xh) * DEG)
    lat = math.atan2(zh, math.hypot(xh, yh)) * DEG

    s = sun(d)
    sun_lon = s["lon"]
    sun_mean = s["M"]
    moon_mean_lon = wrap(node + perihelion + mean)
    elong_mean = wrap(moon_mean_lon - sun_lon)  # D
    lat_arg = wrap(moon_mean_lon - node)  # F
    mm = mean  # Mm

    def sn(x: float) -> float:
        return math.sin(x * RAD)

    def cs(x: float) -> float:
        return math.cos(x * RAD)

    lon += (
        -1.274 * sn(mm - 2 * elong_mean)
        + 0.658 * sn(2 * elong_mean)
        - 0.186 * sn(sun_mean)
        - 0.059 * sn(2 * mm - 2 * elong_mean)
        - 0.057 * sn(mm - 2 * elong_mean + sun_mean)
        + 0.053 * sn(mm + 2 * elong_mean)
        + 0.046 * sn(2 * elong_mean - sun_mean)
        + 0.041 * sn(mm - sun_mean)
        - 0.035 * sn(elong_mean)
        - 0.031 * sn(mm + sun_mean)
        - 0.015 * sn(2 * lat_arg - 2 * elong_mean)
        + 0.011 * sn(mm - 4 * elong_mean)
    )
    lat += (
        -0.173 * sn(lat_arg - 2 * elong_mean)
        - 0.055 * sn(mm - lat_arg - 2 * elong_mean)
        - 0.046 * sn(mm + lat_arg - 2 * elong_mean)
        + 0.033 * sn(lat_arg + 2 * elong_mean)
        + 0.017 * sn(2 * mm + lat_arg)
    )
    r += -0.58 * cs(mm - 2 * elong_mean) - 0.46 * cs(2 * elong_mean)

    ra, dec = _ecliptic_to_equatorial(wrap(lon), lat, obliquity(d))
    elongation = math.acos(max(-1.0, min(1.0, cs(lon - sun_lon) * cs(lat)))) * DEG
    illum = (1.0 + math.cos((180.0 - elongation) * RAD)) / 2.0
    waxing = sn(lon - sun_lon) >= 0.0
    return {
        "ra": ra,
        "dec": dec,
        "illum": illum,
        "waxing": waxing,
        "elongation": elongation,
    }


def body_altitude(body: str, when: datetime, lat: float, lon: float) -> float:
    """Altitude of 'sun' or 'moon' at an aware datetime, from lat/lon."""
    d = day_number_from(when)
    pos = sun(d) if body == "sun" else moon(d)
    lst = sidereal_at(when, lon)
    return alt_az(pos["ra"], pos["dec"], lst, lat)[0]


def radiant_alt_az(ra: float, dec: float, when: datetime, lat: float, lon: float):
    """Altitude and azimuth of a fixed RA/Dec at an aware datetime."""
    return alt_az(ra, dec, sidereal_at(when, lon), lat)


def solar_longitude_instant(year: int, target_lon: float, guess: datetime) -> datetime:
    """The UT instant in the days around `guess` when the Sun reaches `target_lon`.

    The Sun moves about a degree a day, so a shower's maximum, which the
    IMO gives as a solar longitude, is found by walking the longitude
    difference to zero. Used so the peak date is right in every year, not
    only the year the printed calendar was made for.
    """
    t = guess.astimezone(timezone.utc)
    for _ in range(8):
        lon_now = sun(day_number_from(t))["lon"]
        diff = ((target_lon - lon_now + 180.0) % 360.0) - 180.0
        if abs(diff) < 1e-4:
            break
        t += timedelta(days=diff / 0.98565)
    return t


def phase_name(illum: float, waxing: bool) -> str:
    if illum < 0.03:
        return "New moon"
    if illum > 0.97:
        return "Full moon"
    if abs(illum - 0.5) < 0.04:
        return "First quarter" if waxing else "Last quarter"
    if illum < 0.5:
        return "Waxing crescent" if waxing else "Waning crescent"
    return "Waxing gibbous" if waxing else "Waning gibbous"
