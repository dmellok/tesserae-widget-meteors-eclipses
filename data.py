"""Bundled tables: the IMO working list of annual showers, NASA's eclipses
for 2026 to 2030, and a rough continent lookup.

Showers follow the International Meteor Organization's 2026 Meteor Shower
Calendar (Rendtel, IMO INFO(3-25)), Table 5. The maximum is kept as a solar
longitude (equinox J2000.0, as the IMO prints it) so the peak can be found
in any year rather than only in 2026; the printed date is there as a
sanity check. ZHR is the rate under a perfect sky with the radiant
overhead, which nobody ever gets.

Eclipses are NASA's Five Millennium Canon as summarised on the GSFC decade
pages, with the time of greatest eclipse in Terrestrial Dynamical Time as
printed; the server converts to UT with a fixed delta-T.
"""

from __future__ import annotations

# (code, name, start (m, d), end (m, d), printed max (m, d), solar longitude,
#  radiant RA, radiant Dec, ZHR, ZHR is variable, parent body)
SHOWERS = [
    (
        "QUA",
        "Quadrantids",
        (12, 28),
        (1, 12),
        (1, 3),
        283.15,
        230,
        49,
        80,
        False,
        "asteroid 2003 EH1",
    ),
    (
        "LYR",
        "Lyrids",
        (4, 14),
        (4, 30),
        (4, 22),
        32.32,
        271,
        34,
        18,
        False,
        "comet C/1861 G1 Thatcher",
    ),
    (
        "ETA",
        "eta Aquariids",
        (4, 19),
        (5, 28),
        (5, 6),
        45.5,
        338,
        -1,
        50,
        False,
        "comet 1P/Halley",
    ),
    (
        "SDA",
        "Southern delta Aquariids",
        (7, 12),
        (8, 23),
        (7, 31),
        128.0,
        340,
        -16,
        25,
        False,
        "comet 96P/Machholz, probably",
    ),
    (
        "CAP",
        "alpha Capricornids",
        (7, 3),
        (8, 15),
        (7, 31),
        128.0,
        307,
        -10,
        5,
        False,
        "comet 169P/NEAT",
    ),
    (
        "PER",
        "Perseids",
        (7, 17),
        (8, 24),
        (8, 13),
        140.0,
        48,
        58,
        100,
        False,
        "comet 109P/Swift-Tuttle",
    ),
    (
        "DRA",
        "Draconids",
        (10, 6),
        (10, 10),
        (10, 9),
        195.4,
        262,
        54,
        5,
        True,
        "comet 21P/Giacobini-Zinner",
    ),
    (
        "ORI",
        "Orionids",
        (10, 2),
        (11, 7),
        (10, 21),
        208.0,
        95,
        16,
        20,
        False,
        "comet 1P/Halley",
    ),
    (
        "STA",
        "Southern Taurids",
        (9, 20),
        (11, 20),
        (11, 5),
        223.0,
        52,
        15,
        7,
        False,
        "comet 2P/Encke",
    ),
    (
        "NTA",
        "Northern Taurids",
        (10, 20),
        (12, 10),
        (11, 12),
        230.0,
        58,
        22,
        5,
        False,
        "comet 2P/Encke",
    ),
    (
        "LEO",
        "Leonids",
        (11, 6),
        (11, 30),
        (11, 17),
        235.27,
        152,
        22,
        15,
        False,
        "comet 55P/Tempel-Tuttle",
    ),
    (
        "GEM",
        "Geminids",
        (12, 4),
        (12, 20),
        (12, 14),
        262.2,
        112,
        33,
        150,
        False,
        "asteroid 3200 Phaethon",
    ),
    (
        "URS",
        "Ursids",
        (12, 17),
        (12, 26),
        (12, 22),
        270.7,
        217,
        76,
        10,
        False,
        "comet 8P/Tuttle",
    ),
]

SHOWER_FIELDS = (
    "code",
    "name",
    "start",
    "end",
    "max",
    "solar_lon",
    "ra",
    "dec",
    "zhr",
    "variable",
    "parent",
)

# Solar eclipses: (date, greatest eclipse TD "HH:MM:SS", kind, where the
# central line runs (empty for a partial), the whole region that sees any of
# it as NASA prints it, and that region as continent tags).
SOLAR_ECLIPSES = [
    (
        "2026-02-17",
        "12:13:05",
        "annular",
        "Antarctica",
        "southern Argentina and Chile, southern Africa, Antarctica",
        ("south_america", "africa", "antarctica"),
    ),
    (
        "2026-08-12",
        "17:47:05",
        "total",
        "the Arctic, Greenland, Iceland, Spain",
        "northern North America, western Africa, Europe",
        ("north_america", "africa", "europe"),
    ),
    (
        "2027-02-06",
        "16:00:47",
        "annular",
        "Chile, Argentina, the Atlantic",
        "South America, Antarctica, western and southern Africa",
        ("south_america", "antarctica", "africa"),
    ),
    (
        "2027-08-02",
        "10:07:49",
        "total",
        "Morocco, Spain, Algeria, Libya, Egypt, Saudi Arabia, Yemen, Somalia",
        "Africa, Europe, the Middle East, western and southern Asia",
        ("africa", "europe", "asia"),
    ),
    (
        "2028-01-26",
        "15:08:58",
        "annular",
        "Ecuador, Peru, Brazil, Suriname, Spain, Portugal",
        "eastern North America, Central and South America, western Europe, north-west Africa",
        ("north_america", "south_america", "europe", "africa"),
    ),
    (
        "2028-07-22",
        "02:56:39",
        "total",
        "Australia, New Zealand",
        "South-east Asia, the East Indies, Australia, New Zealand",
        ("asia", "oceania"),
    ),
    (
        "2029-01-14",
        "17:13:47",
        "partial",
        "",
        "North America, Central America",
        ("north_america",),
    ),
    (
        "2029-06-12",
        "04:06:13",
        "partial",
        "",
        "the Arctic, Scandinavia, Alaska, northern Asia, northern Canada",
        ("europe", "north_america", "asia"),
    ),
    (
        "2029-07-11",
        "15:37:18",
        "partial",
        "",
        "southern Chile, southern Argentina",
        ("south_america",),
    ),
    (
        "2029-12-05",
        "15:03:57",
        "partial",
        "",
        "southern Argentina, southern Chile, Antarctica",
        ("south_america", "antarctica"),
    ),
    (
        "2030-06-01",
        "06:29:13",
        "annular",
        "Algeria, Tunisia, Greece, Turkey, Russia, northern China, Japan",
        "Europe, northern Africa, the Middle East, Asia, the Arctic, Alaska",
        ("europe", "africa", "asia", "north_america"),
    ),
    (
        "2030-11-25",
        "06:51:37",
        "total",
        "Botswana, South Africa, Australia",
        "southern Africa, the southern Indian Ocean, the East Indies, Australia, Antarctica",
        ("africa", "asia", "oceania", "antarctica"),
    ),
]

# Lunar eclipses: (date, greatest eclipse TD, kind, umbral magnitude, region
# as NASA prints it). Visibility is computed from the Moon's altitude at
# greatest eclipse, so the region text is only there for the caption.
LUNAR_ECLIPSES = [
    (
        "2026-03-03",
        "11:34:52",
        "total",
        1.151,
        "eastern Asia, Australia, the Pacific, the Americas",
    ),
    (
        "2026-08-28",
        "04:14:04",
        "partial",
        0.930,
        "the eastern Pacific, the Americas, Europe, Africa",
    ),
    (
        "2027-02-20",
        "23:14:06",
        "penumbral",
        -0.057,
        "the Americas, Europe, Africa, Asia",
    ),
    (
        "2027-07-18",
        "16:04:09",
        "penumbral",
        -1.068,
        "eastern Africa, Asia, Australia, the Pacific",
    ),
    ("2027-08-17", "07:14:59", "penumbral", -0.525, "the Pacific, the Americas"),
    ("2028-01-12", "04:14:13", "partial", 0.066, "the Americas, Europe, Africa"),
    ("2028-07-06", "18:20:57", "partial", 0.389, "Europe, Africa, Asia, Australia"),
    (
        "2028-12-31",
        "16:53:15",
        "total",
        1.246,
        "Europe, Africa, Asia, Australia, the Pacific",
    ),
    (
        "2029-06-26",
        "03:23:22",
        "total",
        1.844,
        "the Americas, Europe, Africa, the Middle East",
    ),
    ("2029-12-20", "22:43:12", "total", 1.117, "the Americas, Europe, Africa, Asia"),
    ("2030-06-15", "18:34:34", "partial", 0.502, "Europe, Africa, Asia, Australia"),
    (
        "2030-12-09",
        "22:28:51",
        "penumbral",
        -0.163,
        "the Americas, Europe, Africa, Asia",
    ),
]

# TD minus UT, seconds, flat across 2026 to 2030 (it drifts by about a
# second a year, which is nothing against a caption printed to the minute).
DELTA_T_S = 69

CONTINENT_NAMES = {
    "north_america": "North America",
    "south_america": "South America",
    "europe": "Europe",
    "africa": "Africa",
    "asia": "Asia",
    "oceania": "Australia and the Pacific",
    "antarctica": "Antarctica",
}


def continent(lat: float, lon: float) -> str:
    """A continent tag from latitude and longitude, by coarse boxes.

    This is deliberately rough: it answers "which of NASA's regions am I
    in", and the regions themselves are whole continents. Islands and
    borderlands can land on the wrong side; the widget says so in its
    README and marks solar eclipses as approximate.
    """
    if lat < -60:
        return "antarctica"
    if lon < -30:
        if lat < 12:
            return "south_america"
        if lat < 30 and lon < -150:
            return "oceania"
        return "north_america"
    if lon >= 160 or (lon >= 110 and lat < 10):
        return "oceania"
    if lat >= 36 and lon < 60:
        return "europe" if not (lon > 26 and lat < 42) else "asia"
    if lon < 32 or (lon < 52 and lat < 12):
        return "africa"
    return "asia"
