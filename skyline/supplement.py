"""
Published tallest-buildings lists for cities the reference database barely
covers, plus the landmarks that make those skylines theirs.

Wikidata has three buildings on record for Austin and fourteen for Nashville,
and not much more for Fort Worth. That gap is not about the cities; it is
about who has been entering data, and English-language coverage of mid-size
American downtowns is thin in a way that coverage of Manhattan is not.

So these three cities are carried here instead, transcribed from the
Wikipedia "List of tallest buildings" article for each city (retrieved 2026),
which publishes structural heights, coordinates and completion years per
building. Heights are the metres value from the article's height column.
Coordinates are the article's, which are block-level rather than surveyed - a
real limitation and a small one here: the wheel equalises angular spacing
anyway, so what a coordinate decides is the order buildings appear in, not
the gap between them.

The lists also carry the buildings a resident would name first, because they
happen to be tall enough to qualify on their own numbers:

  Austin       the Texas State Capitol (94.8 m, taller than the national
               one) and the UT Tower, plus the west-campus student
               high-rises around it.
  Nashville    the AT&T "Batman" Building, West End Tower on the Vanderbilt
               campus, and the Tennessee State Capitol - 206.6 ft (63.0 m)
               per the Society of Architectural Historians' Archipedia,
               which clears the wheel's 55 m floor on its own tower.
  Fort Worth   the Tarrant County Courthouse (194 ft, the city's tallest
               from 1895 to 1920), Pioneer Tower at the Will Rogers
               Memorial, and the Art Deco stock downtown.

What is absent, and why: nothing at TCU qualifies. Robert Carr Chapel's
spire, the campus high point, is a published 137 ft (41.8 m) - under the
55 m floor the wheel states on screen, so including it would falsify the
label. The Ryman and the Parthenon fall the same way for Nashville.

Any city listed here is marked "supplemented" in the app. Buildings from the
reference database that duplicate a row below are dropped by proximity in
build_skylines.assign(), so nothing is drawn twice under two names.
"""

# name, height in metres, lat, lon, year
AUSTIN = [
    ('Sixth and Guadalupe',                                 266.7,  30.2697,  -97.7467, 2023),
    ('The Republic',                                        216.0,  30.2669,  -97.7478, 2025),
    ('The Independent',                                     211.4,  30.2678,  -97.7511, 2019),
    ('The Austonian',                                       208.2,  30.2647,  -97.7444, 2010),
    ('ATX Tower',                                           205.7,  30.2686,  -97.7461, 2025),
    ('Modern Austin',                                       199.6,  30.2606,  -97.7386, 2025),
    ('415 Colorado Street',                                 193.1,  30.2672,  -97.7442, 2025),
    ('Fairmont Austin',                                     180.0,  30.2625,  -97.7381, 2018),
    ('360 Condominiums',                                    177.1,  30.2672,  -97.7497, 2008),
    ('Block 185',                                           175.9,  30.2656,  -97.7506, 2022),
    ('44 East Avenue',                                      174.7,  30.2558,  -97.7392, 2023),
    ('Paseo',                                               172.8,  30.2594,  -97.7389, 2025),
    ('The Travis',                                          171.3,  30.2603,  -97.7403, 2025),
    ('Indeed Tower',                                        165.2,  30.2689,  -97.7442, 2021),
    ('Hanover Republic Square',                             157.3,  30.2678,  -97.7461, 2023),
    ('Frost Bank Tower',                                    157.2,  30.2664,  -97.7428, 2004),
    ('Hanover Brazos Street',                               156.4,  30.2644,  -97.7422, 2023),
    ('700 River',                                           151.4,  30.2578,  -97.7386, 2024),
    ('W Austin Hotel & Residences',                         145.3,  30.2658,  -97.7469, 2010),
    ('Fifth & West',                                        139.9,  30.2694,  -97.7506, 2019),
    ('Vesper',                                              138.7,  30.2597,  -97.7375, 2024),
    ('300 Colorado',                                        135.8,  30.2661,  -97.7456, 2021),
    ('Spring',                                              132.3,  30.2689,  -97.7542, 2009),
    ('Northshore',                                          129.3,  30.2653,  -97.7494, 2016),
    ('The Bowie',                                           128.9,  30.2692,  -97.7553, 2015),
    ('70 Rainey',                                           127.7,  30.2586,  -97.7392, 2019),
    ('Ashton',                                              125.5,  30.2644,  -97.7453, 2009),
    ('JW Marriott Convention Hotel',                        124.4,  30.2647,  -97.7431, 2015),
    ('Four Seasons Residences Austin',                      122.3,  30.2622,  -97.7417, 2010),
    ('One American Center',                                 122.2,  30.2689,  -97.7433, 1984),
    ('500 West 2nd Street',                                 121.9,  30.2661,  -97.7492, 2017),
    ('One Eleven Congress',                                 121.3,  30.2636,  -97.7436, 1987),
    ('Colorado Tower',                                      121.0,  30.2658,  -97.7447, 2015),
    ('Austin Proper',                                       121.0,  30.2664,  -97.7500, 2019),
    ('Third + Shoal',                                       118.0,  30.2667,  -97.7500, 2018),
    ('Austin Marriott Downtown',                            117.7,  30.2628,  -97.7414, 2020),
    ('Austin Hilton Convention Center Hotel',               114.9,  30.2653,  -97.7381, 2004),
    ('The Waller',                                          113.0,  30.2711,  -97.7344, 2024),
    ('405 Colorado',                                        111.6,  30.2667,  -97.7444, 2022),
    ('Natiivo',                                             109.1,  30.2564,  -97.7389, 2022),
    ('5th & Brazos',                                        108.8,  30.2669,  -97.7411, 2021),
    ('The Quincy',                                          108.0,  30.2608,  -97.7389, 2021),
    ('Alexan Waterloo',                                     106.7,  30.2711,  -97.7339, 2022),
    ('Hyatt Centric',                                       105.2,  30.2697,  -97.7417, 2022),
    ('Seaholm Residences',                                  103.9,  30.2672,  -97.7522, 2016),
    ('Windsor on the Lake',                                 103.3,  30.2558,  -97.7394, 2008),
    ('Bank of America Center',                              102.4,  30.2678,  -97.7425, 1975),
    ('The Linden',                                          101.5,  30.2794,  -97.7422, 2023),
    ('The Domain II',                                       101.2,  30.3947,  -97.7219, 2023),
    ('Union on San Antonio',                                101.2,  30.2833,  -97.7428, 2024),
    ('300 West 6th Street',                                 100.0,  30.2692,  -97.7456, 2002),
    ('Aloft Austin Downtown and Element Austin Downtown',   100.0,  30.2689,  -97.7422, 2017),
    ('Procore Tower',                                        99.1,  30.2683,  -97.7450, 1974),
    ('The Monarch',                                          98.5,  30.2692,  -97.7522, 2008),
    ('100 Congress Avenue',                                  97.5,  30.2642,  -97.7450, 1987),
    ('Yugo Austin Waterloo',                                 97.5,  30.2883,  -97.7442, 2022),
    ('Union on 24th Street',                                 97.5,  30.2875,  -97.7453, 2024),
    ('Villas on 24th',                                       95.0,  30.2878,  -97.7444, 2025),
    ('Texas State Capitol',                                  94.8,  30.2747,  -97.7403, 1888),
    ('San Jacinto Center',                                   94.5,  30.2625,  -97.7428, 1987),
    ('UT Tower (Main Building)',                             93.6,  30.2861,  -97.7394, 1937),
    ('Dobie Center',                                         93.6,  30.2833,  -97.7414, 1971),
    ('Icon',                                                 93.6,  30.2853,  -97.7433, 2025),
    ('301 Congress Avenue',                                  93.3,  30.2653,  -97.7431, 1986),
    ('Hotel ZaZa & Apartments',                              93.0,  30.2672,  -97.7464, 2019),
]

NASHVILLE = [
    ('AT&T Building (333 Commerce)',           188.1,  36.1625,  -86.7769, 1994),
    ('Four Seasons Hotel and Residences',      165.2,  36.1603,  -86.7736, 2022),
    ('505',                                    159.1,  36.1628,  -86.7803, 2018),
    ('The Pinnacle at Nashville Yards',        153.6,  36.1597,  -86.7856, 2025),
    ('Prime',                                  139.0,  36.1614,  -86.7842, 2024),
    ('William R. Snodgrass Tennessee Tower',   137.8,  36.1639,  -86.7850, 1970),
    ('Bridgestone Tower',                      135.2,  36.1589,  -86.7753, 2017),
    ('Fifth Third Center',                     133.0,  36.1639,  -86.7803, 1986),
    ('Amazon Tower Two',                       128.0,  36.1614,  -86.7869, 2023),
    ('The Emory',                              128.0,  36.1600,  -86.7842, 2025),
    ('Alcove',                                 127.8,  36.1617,  -86.7850, 2023),
    ('Symphony Place',                         127.1,  36.1603,  -86.7747, 2010),
    ('The Place at Fifth + Broadway',          126.5,  36.1606,  -86.7800, 2020),
    ('Life & Casualty Tower',                  124.7,  36.1633,  -86.7792, 1957),
    ('The Everett',                            124.7,  36.1597,  -86.7847, 2025),
    ('Conrad Hotel and Residences',            123.0,  36.1544,  -86.7944, 2022),
    ('Nashville City Center',                  122.5,  36.1639,  -86.7817, 1988),
    ('James K. Polk State Office Building',    119.5,  36.1647,  -86.7817, 1981),
    ('JW Marriott Nashville',                  117.6,  36.1564,  -86.7811, 2018),
    ('Renaissance Nashville Hotel',            117.3,  36.1608,  -86.7811, 1987),
    ('1 Hotel and Embassy Suites',             117.0,  36.1575,  -86.7803, 2022),
    ('Viridian Tower',                         115.2,  36.1631,  -86.7794, 2006),
    ('805 Lea',                                112.7,  36.1539,  -86.7800, 2021),
    ('501 Commerce',                           110.0,  36.1614,  -86.7794, 2020),
    ('One22One',                               109.7,  36.1558,  -86.7883, 2023),
    ('One Nashville Place',                    109.4,  36.1628,  -86.7781, 1985),
    ('UBS Tower',                              107.9,  36.1658,  -86.7797, 1974),
    ('Albion Music Row',                       106.7,  36.1550,  -86.7897, 2026),
    ('The Pullman at Gulch Union',             106.0,  36.1547,  -86.7869, 2024),
    ('SoBro',                                  105.2,  36.1594,  -86.7739, 2016),
    ('Amazon Tower One',                       105.0,  36.1608,  -86.7867, 2020),
    ('222 2nd Avenue South',                    99.4,  36.1597,  -86.7733, 2017),
    ('Broadwest Office Tower',                  99.0,  36.1547,  -86.7933, 2022),
    ('Modera McGavock',                         99.0,  36.1556,  -86.7881, 2025),
    ('Olive at Peabody Union',                  99.0,  36.1589,  -86.7694, 2025),
    ('1200 Broadway',                           98.8,  36.1567,  -86.7881, 2019),
    ('Westin Music City',                       98.5,  36.1550,  -86.7808, 2016),
    ('Grand Hyatt Nashville',                   93.0,  36.1581,  -86.7850, 2020),
    ('West End Tower (Vanderbilt)',             93.0,  36.1469,  -86.8072, 2021),
    ('Sheraton Nashville Downtown',             91.4,  36.1633,  -86.7831, 1975),
    ('Tennessee State Capitol',                 63.0,  36.1659,  -86.7844, 1859),
]

FORT_WORTH = [
    ('Burnett Plaza',                          172.9,  32.7503,  -97.3344, 1983),
    ('Bank of America Tower',                  166.7,  32.7561,  -97.3306, 1984),
    ('777 Main Street',                        160.0,  32.7531,  -97.3297, 1983),
    ('The Fort Worth Tower',                   148.7,  32.7533,  -97.3328, 1974),
    ('Wells Fargo Tower',                      145.4,  32.7564,  -97.3319, 1982),
    ('Omni Fort Worth Hotel',                  136.3,  32.7483,  -97.3286, 2009),
    ('Frost Bank Tower',                       112.5,  32.7525,  -97.3333, 2018),
    ('Fort Worth City Hall',                    98.8,  32.7531,  -97.3436, 2004),
    ('Deco 969',                                96.0,  32.7522,  -97.3281, 2024),
    ('714 Main',                                93.6,  32.7528,  -97.3303, 1921),
    ('Bank of America Center',                  91.4,  32.7514,  -97.3336, 1962),
    ('AT&T Building',                           89.9,  32.7500,  -97.3294, 1958),
    ('W. T. Waggoner Building',                 82.3,  32.7517,  -97.3306, 1920),
    ('Blackstone Hotel',                        81.7,  32.7539,  -97.3303, 1929),
    ('Star-Telegram Building',                  79.3,  32.7517,  -97.3317, 1930),
    ('City Place Tower Two',                    78.6,  32.7558,  -97.3347, 1978),
    ('Fritz G. Lanham Federal Building',        76.2,  32.7506,  -97.3317, 1968),
    ('City Place Tower One',                    75.3,  32.7544,  -97.3336, 1976),
    ('River Tower',                             73.2,  32.7497,  -97.3439, 2017),
    ('The Carnegie',                            71.9,  32.7536,  -97.3342, 2008),
    ('Oncor Building',                          71.3,  32.7522,  -97.3303, 1952),
    ('Electric Building',                       69.8,  32.7514,  -97.3328, 1929),
    ('Petroleum Building',                      69.0,  32.7528,  -97.3317, 1927),
    ('Sinclair Building',                       65.5,  32.7539,  -97.3311, 1930),
    ('Pioneer Tower (Will Rogers Memorial)',    65.0,  32.7461,  -97.3664, 1936),
    ('Tarrant County Corrections Center',       61.9,  32.7558,  -97.3367, 1990),
    ('Tarrant County Courthouse',               59.1,  32.7585,  -97.3323, 1895),
]

SUPPLEMENT = {"Austin": AUSTIN, "Nashville": NASHVILLE,
              "Fort Worth": FORT_WORTH}

# The height each article says its own list is complete down to: 300 ft for
# Austin and Nashville, 200 ft for Fort Worth. Above this line the published
# list is authoritative; below it the reference database may still add
# buildings. Landmark rows carried above (the Tennessee State Capitol) can
# sit below this line without lowering it.
LIST_FLOOR = {"Austin": 91.4, "Nashville": 91.4, "Fort Worth": 61.0}


def rows_for(city):
    """Buildings in the same shape the loader produces, tagged as
    hand-entered so that the output can say so."""
    out = []
    for name, h, lat, lon, year in SUPPLEMENT.get(city, []):
        out.append({"name": name, "h": float(h), "lat": lat, "lon": lon,
                    "year": year, "hand": True})
    return out
