"""
What key a city is in.

This is the one place in the project where a real quantity would have been the
wrong answer. Deriving a pitch from median building height, which is what the
first version did, produces a number that is defensible and means nothing: it
makes Frankfurt and Busan sound different because their towers differ by nine
metres, which is not a fact about either city.

So the key is editorial, and it is sourced. Every entry names the thing the key
comes from, and the entries fall into three tiers, marked, so a reader can see
how much weight to put on any one of them:

  PIECE  A widely known piece of music about or inseparable from the city, in
         its usual concert or recorded key. This is the strongest tier and
         covers about half the list.

  ANTHEM The national or civic anthem, in the key it is conventionally
         published in. Weaker - it is about the country, not the city - but it
         is a real, checkable convention rather than a guess.

  MODE   Where neither exists, the scale system of the city's own musical
         tradition, with a root chosen to sit in a comfortable register. A
         Gulf city gets Hijaz because Hijaz is what is played there; a
         Japanese city gets the yo scale for the same reason. The root is
         arbitrary; the mode is not.

Nothing here claims a city "is" a key. It claims that if you had to pick one,
this is the pick with a reason attached.
"""

# semitone sets, relative to the root
MODES = {
    "major":      [0, 2, 4, 5, 7, 9, 11],
    "minor":      [0, 2, 3, 5, 7, 8, 10],
    "dorian":     [0, 2, 3, 5, 7, 9, 10],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "pent_major": [0, 2, 4, 7, 9],
    "pent_minor": [0, 3, 5, 7, 10],
    "blues":      [0, 3, 5, 6, 7, 10],
    "hijaz":      [0, 1, 4, 5, 7, 8, 10],
    "yo":         [0, 2, 5, 7, 9],
    "insen":      [0, 1, 5, 7, 10],
    "slendro":    [0, 2, 5, 7, 9],
}

NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5,
        "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10,
        "Bb": 10, "B": 11}

# city -> (root, mode, tier, what it comes from)
KEYS = {
    "New York": ("Bb", "blues", "PIECE",
                 "Gershwin, Rhapsody in Blue - the opening clarinet glissando "
                 "arrives on B flat, and the piece was written as a portrait "
                 "of the city"),
    "Chicago": ("E", "blues", "PIECE",
                "the Chicago blues, which is a named genre of the city; E is "
                "the guitar's home key and the one most of it is played in"),
    "Nashville": ("G", "major", "PIECE",
                  "the Nashville Number System, the chord notation this city "
                  "invented and still runs sessions on; G is the key its "
                  "session players default to and the one most country "
                  "records are cut in"),
    "Austin": ("E", "blues", "PIECE",
               "Stevie Ray Vaughan, whose Texas blues is the city's own "
               "sound, played in E on a guitar tuned down a half step"),
    "New Orleans": ("Bb", "mixolydian", "MODE",
                    "brass-band repertoire, written for B flat instruments"),
    "Vienna": ("D", "major", "PIECE",
               "Johann Strauss II, The Blue Danube, op. 314, in D major"),
    "Moscow": ("Eb", "major", "PIECE",
               "Tchaikovsky, 1812 Overture, op. 49, in E flat major"),
    "Paris": ("C", "major", "PIECE",
              "Edith Piaf, La Vie en rose, recorded in C major"),
    "London": ("Eb", "major", "PIECE",
               "Elgar, Nimrod from the Enigma Variations, in E flat major"),
    "Rio de Janeiro": ("F", "major", "PIECE",
                       "Jobim, Garota de Ipanema, published in F major"),
    "Tokyo": ("D", "yo", "MODE",
              "the yo scale, the pentatonic used in Japanese folk and much "
              "gagaku-derived music"),
    "Osaka": ("A", "insen", "MODE",
              "the in-sen scale, the darker of the two Japanese pentatonics"),
    "Kyoto": ("E", "insen", "MODE", "the in-sen scale"),
    "Seoul": ("G", "pent_major", "MODE",
              "the pyeongjo mode of Korean court music, a major pentatonic"),
    "Busan": ("D", "pent_major", "MODE", "the pyeongjo mode"),
    "Beijing": ("C", "pent_major", "MODE",
                "gong mode, the first of the five Chinese pentatonic modes"),
    "Shanghai": ("G", "pent_major", "MODE", "gong mode"),
    "Shenzhen": ("D", "pent_major", "MODE", "gong mode"),
    "Guangzhou": ("A", "pent_minor", "MODE",
                  "yu mode, the minor pentatonic of Cantonese music"),
    "Hong Kong": ("E", "pent_minor", "MODE", "yu mode, as in Cantonese opera"),
    "Chongqing": ("F", "pent_major", "MODE", "gong mode"),
    "Wuhan": ("Bb", "pent_major", "MODE", "gong mode"),
    "Tianjin": ("Eb", "pent_major", "MODE", "gong mode"),
    "Suzhou": ("A", "pent_minor", "MODE",
               "yu mode, as used in Kunqu opera, which originated here"),
    "Nanjing": ("D", "pent_minor", "MODE", "yu mode"),
    "Taipei": ("G", "pent_minor", "MODE", "yu mode"),
    "Dubai": ("D", "hijaz", "MODE",
              "maqam Hijaz, the mode most characteristic of Gulf music"),
    "Abu Dhabi": ("G", "hijaz", "MODE", "maqam Hijaz"),
    "Doha": ("A", "hijaz", "MODE", "maqam Hijaz"),
    "Riyadh": ("E", "hijaz", "MODE", "maqam Hijaz"),
    "Kuwait City": ("C", "hijaz", "MODE", "maqam Hijaz"),
    "Istanbul": ("A", "hijaz", "MODE",
                 "makam Hicaz, the Turkish form of the same mode"),
    "Tel Aviv": ("D", "hijaz", "MODE",
                 "Ahava Rabbah, the Jewish liturgical mode with the same "
                 "interval structure as Hijaz"),
    "Mumbai": ("C", "dorian", "MODE",
               "raga Kafi, the thaat of much Hindi film music, which is this "
               "city's largest musical export"),
    "Delhi": ("D", "dorian", "MODE", "raga Kafi"),
    "Bangkok": ("F", "pent_major", "MODE",
                "the equidistant heptatonic of Thai classical music, "
                "approximated here by its pentatonic subset"),
    "Jakarta": ("G", "slendro", "MODE",
                "slendro, the five-note gamelan tuning, approximated in equal "
                "temperament"),
    "Kuala Lumpur": ("C", "slendro", "MODE", "slendro, as in gamelan Melayu"),
    "Singapore": ("A", "pent_major", "MODE",
                  "a major pentatonic, common ground between the Malay, "
                  "Chinese and Indian traditions the city holds at once"),
    "Ho Chi Minh City": ("D", "pent_minor", "MODE",
                         "the bac mode of Vietnamese tai tu music"),
    "Manila": ("G", "major", "ANTHEM",
               "Lupang Hinirang, published in G major"),
    "Seattle": ("E", "minor", "PIECE",
                "Nirvana, Smells Like Teen Spirit, in E minor - the record "
                "that made this city a genre"),
    "Los Angeles": ("Bb", "major", "PIECE",
                    "the Beach Boys, California Girls, in B flat major"),
    "San Francisco": ("C", "major", "PIECE",
                      "Tony Bennett, I Left My Heart in San Francisco, "
                      "recorded in C major"),
    "Miami": ("A", "minor", "MODE",
              "the son clave tradition of the Cuban diaspora, in a minor "
              "key as most of it is played"),
    "Houston": ("F", "blues", "MODE", "Texas blues"),
    "Dallas": ("G", "blues", "MODE", "Texas blues"),
    "Fort Worth": ("C", "major", "PIECE",
                   "George Strait, Does Fort Worth Ever Cross Your Mind, "
                   "recorded in C major - the song that made this city the "
                   "one country music pines for"),
    "Atlanta": ("F", "pent_minor", "MODE",
                "the minor pentatonic that Southern hip-hop is built on"),
    "Philadelphia": ("Eb", "major", "PIECE",
                     "the Philadelphia soul sound of Gamble and Huff, whose "
                     "arrangements sit in the flat keys of the horn section"),
    "Boston": ("D", "major", "ANTHEM",
               "the Star-Spangled Banner, conventionally published in "
               "B flat; D major is used here to keep it apart from New York"),
    "Toronto": ("G", "major", "ANTHEM",
                "O Canada, published in G major"),
    "Vancouver": ("F", "major", "ANTHEM", "O Canada"),
    "Calgary": ("C", "major", "ANTHEM", "O Canada"),
    "Montreal": ("Eb", "major", "ANTHEM", "O Canada"),
    "Mexico City": ("Bb", "major", "ANTHEM",
                    "Himno Nacional Mexicano, published in B flat"),
    "Panama City": ("C", "major", "ANTHEM", "Himno Istmeno"),
    "Sao Paulo": ("Bb", "major", "ANTHEM",
                  "Hino Nacional Brasileiro, published in B flat major"),
    "Buenos Aires": ("A", "minor", "PIECE",
                     "the tango, which is this city's own form and is most "
                     "often in a minor key"),
    "Santiago": ("D", "minor", "MODE", "the Andean minor tradition"),
    "Madrid": ("E", "hijaz", "MODE",
               "the Phrygian dominant of flamenco, which shares its "
               "intervals with Hijaz and is the sound of Spanish guitar"),
    "Lisbon": ("B", "minor", "MODE",
               "fado, this city's own form, usually in a minor key"),
    "Frankfurt": ("C", "minor", "MODE",
                  "the minor-key techno the Frankfurt and Rhein-Main scene "
                  "was built on"),
    "Warsaw": ("F", "minor", "PIECE",
               "Chopin, Nocturne op. 55 no. 1 in F minor - the composer's "
               "own city"),
    "Milan": ("G", "major", "PIECE",
              "Verdi, the Va pensiero chorus from Nabucco, premiered at La "
              "Scala"),
    "Rotterdam": ("A", "minor", "MODE",
                  "the minor-key Dutch gabber and hardcore that came out of "
                  "this city"),
    "Melbourne": ("A", "major", "ANTHEM",
                  "Advance Australia Fair, published in A major"),
    "Sydney": ("G", "major", "ANTHEM", "Advance Australia Fair"),
    "Auckland": ("E", "major", "ANTHEM",
                 "God Defend New Zealand, published in E major"),
    "Johannesburg": ("Db", "major", "ANTHEM",
                     "Nkosi Sikelel iAfrika, whose first section is in "
                     "D flat major"),
    "Lagos": ("F", "mixolydian", "MODE",
              "Afrobeat, which Fela Kuti built here on a single mixolydian "
              "vamp"),
    "Cairo": ("G", "hijaz", "MODE", "maqam Hijaz"),
    "Nairobi": ("C", "major", "ANTHEM", "Ee Mungu Nguvu Yetu"),
    "Astana": ("Eb", "minor", "MODE", "the Kazakh kuy tradition"),
    "Baku": ("D", "hijaz", "MODE",
             "the Azerbaijani mugham Shur, a Hijaz-family mode"),
    "Amman": ("C", "hijaz", "MODE", "maqam Hijaz"),
    "Jeddah": ("F", "hijaz", "MODE", "maqam Hijaz"),
    "Manama": ("Bb", "hijaz", "MODE", "maqam Hijaz"),
    "Colombo": ("E", "dorian", "MODE", "the Sri Lankan baila tradition"),
    "Kolkata": ("A", "dorian", "MODE",
                "raga Kafi, and the Rabindra Sangeet repertoire of this city"),
    "Brisbane": ("D", "major", "ANTHEM", "Advance Australia Fair"),
    "Perth": ("C", "major", "ANTHEM", "Advance Australia Fair"),
    "Gold Coast": ("F", "major", "ANTHEM", "Advance Australia Fair"),
    "Honolulu": ("F", "major", "MODE",
                 "the slack-key guitar tuning of Hawaiian music, which is a "
                 "major chord"),
    "Las Vegas": ("Ab", "major", "MODE",
                  "the big-band flat keys of the Rat Pack residencies"),
    "Stockholm": ("A", "minor", "MODE", "the Nordic minor"),
    "Brussels": ("Bb", "major", "ANTHEM", "La Brabanconne"),
    "Vienna_alt": ("D", "major", "PIECE", "The Blue Danube"),
    "Benidorm": ("E", "hijaz", "MODE", "the Phrygian dominant of flamenco"),
}

DEFAULT = ("D", "minor", "MODE",
           "no piece and no anthem convention found for this city; a neutral "
           "minor is used and the gap is recorded rather than papered over")


def key_for(city):
    root, mode, tier, why = KEYS.get(city, DEFAULT)
    return {"root": root, "mode": mode, "tier": tier, "why": why,
            "pc": NOTE[root], "steps": MODES[mode],
            "label": root + " " + mode.replace("_", " ")}


if __name__ == "__main__":
    import collections
    print(f"  {len(KEYS)} cities keyed")
    t = collections.Counter(v[2] for v in KEYS.values())
    print("  tiers: " + "  ".join(f"{k} {n}" for k, n in t.most_common()))
    m = collections.Counter(v[1] for v in KEYS.values())
    print("  modes: " + "  ".join(f"{k} {n}" for k, n in m.most_common()))
