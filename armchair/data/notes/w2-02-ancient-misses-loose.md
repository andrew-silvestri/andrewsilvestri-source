# w2-02: ancient misses and loose/hyped hits (cases M01-M15)

Brief: W2_CASES_BRIEF.md, rubric W1_BRIEF_COMMON.md. CSV: `data/cases_ancient_misses_loose.csv` (15 rows, built by a Python csv script; gap computed as confirm_year - idea_year, minus 1 when crossing BCE to CE). Downloads in `data/raw/w2-02/` (MIT Classics HTML stripped to .txt, Gutenberg Confessions and Lavoisier, Latin Library Conf. XI, Censorinus at LacusCurtius, Burnet on Wikisource). Search method for each "verified" claim: `grep -n` on those files; the matching lines are cited per case.

## What "verified = Y" means here (read before using)

- Y = I opened a public translation of the philosopher's passage and its content and chapter (book/part) match the locator. MIT Classics (Oxford tr.) and Jowett do NOT print Bekker/Stephanus line numbers, so the line ranges (e.g. 216a11-21) are the standard numbering, not checked line by line. Confidence on chapter: high; on line numbers: medium.
- Two MIT pages were truncated at ~100 KB (De Caelo I ends mid-I.12; Physics IV ends in IV.13). The passages used lie inside the downloaded part; for M09 I also opened De Caelo II.1, which restates the conclusion.
- Not opened (secondary or from memory, so medium confidence): the confirming texts of Galileo 1638, Torricelli 1644, Tycho 1573, Cavendish 1784, Ibn al-Haytham, Redi 1668, Cauchy 1821, Helmholtz 1847, Born 1926, Hawking-Penrose 1970, Penzias-Wilson 1965 (ADS blocked automated fetch, "Human Verification"). Exception: Lavoisier 1789 (Kerr tr., Gutenberg 30775) opened: preface and the Table of Simple Substances, 33 entries counted.
- DK numbers: Empedocles B6 and B84, Heraclitus B30/B31, and the Burnet-fr.-22 = DK B90 concordance were not checked against Diels-Kranz itself (Burnet numbers his own fragments). Plutarch 730E for Anaximander was not opened; Censorinus 4.7 was.

## Decisions the task asked me to make

- M04 four elements: Lavoisier 1789, not Boyle 1661. Boyle's Sceptical Chymist argued doubt and offered no replacement list; Lavoisier published a list of simple substances that leaves out water, air, earth, and his preface names the four-element doctrine as a Greek prejudice. Irony for the page: the same table still lists light and caloric (the latter glossed as "fire") and five "earths" later shown to be compounds.
- M08 spontaneous generation: Redi 1668, not Pasteur 1862. Aristotle's examples are insects, testaceans, some fish; he says nothing of microbes. Redi tested the class Aristotle named. Pasteur refuted a later, microbial version Aristotle never stated. Caveat: Redi himself still allowed spontaneous origin of gall insects and intestinal worms.
- M09 eternal universe: CMB 1965, not Hubble 1929. Expansion alone was compatible with an eternal steady-state universe (Bondi, Gold, Hoyle 1948); the relic radiation is what discriminated against it.
- M15 Augustine: Hawking-Penrose 1970, not Lemaitre 1931. Lemaitre 1931 proposed a beginning; the 1970 theorem is the result that a GR universe meeting stated conditions is past-incomplete. Neither is an observation. Gap to Lemaitre would be 1533.
- M07: event year 1021, the end of the common 1011-1021 composition window (Wikipedia, "Book of Optics"); the Institute of Ismaili Studies gives c. 1027, the task said c. 1028. With 1027 the gap is 1386 instead of 1380. I found no source for exactly 1028.
- M01: Galileo 1638 as the brief names him. Stevin and de Groot's Delft drop (1586) is earlier and documented; the Pisa tower story is not.
- IDs: I numbered all 15 cases M01-M15 (misses M01-M09, loose/hyped hits M10-M15), since the task gave the prefix "M01..".

## Misses (side = MISS, grade WRONG)

### M01 Aristotle, heavier falls faster. Gap 1972 (c. -335 to 1638)
- Evidence: Physics IV.8 (MIT tr., Part 8): bodies with greater impulse of weight, alike otherwise, move faster over an equal space, in the ratio of their magnitudes. De Caelo I.6 (MIT Part 6): times inversely proportional to weights; "if one weight is twice another, it will take half as long".
- Same passage, and it matters: Aristotle derives that in a void all bodies would move at equal speed, and rejects the void BECAUSE that is impossible. He stated the correct result and used it as a reductio.
- Rationale: an asserted, quantitative, testable law; refuted.
- Strongest counter: Rovelli (J. Am. Phil. Assoc. 1, 2015) argues Aristotle's physics is right for bodies at terminal velocity in a fluid, where steady speed does rise with weight. Reply: Aristotle stated the ratio generally, including for the time over a given distance, and Galileo's argument targets exactly that; WRONG stands, with Rovelli as a note. Confidence: high.

### M02 Aristotle, no void. Gap 1977 (to Torricelli 1643)
- Evidence: Physics IV.8 opens with the aim of showing there is no separate void (grep "no void existing separately").
- Rationale: a confident claim; Torricelli's tube produced and sustained an air-free space and assigned the column to air pressure. Pascal/Perier's Puy de Dome ascent (19 Sept 1648) showed the column falls with altitude, which ruled out horror vacui as the explanation; it is the stronger "decisive" test, but the brief says decide before computing, and the void first existed in 1643.
- Counter: a Torricelli space contains mercury vapour, and the modern vacuum is a field state, not nothing. Aristotle's argument concerned a void as a place with no body, and the tube shows such a place (to an excellent approximation). Confidence: high on the claim, medium on the 1644 letter date (not opened).

### M03 Aristotle, unchanging aether heavens. Gap 1907 (to 1573)
- Evidence: De Caelo I.3 (MIT Part 3): the first body is ungenerated, indestructible, unalterable; Aristotle cites the evidence that in all records no change appears in the outermost heaven; derives the name aither from "runs always".
- Rationale: he based this on an empirical claim (no recorded change), so it was falsifiable, and the 1572 nova falsified it. Comet of 1577 adds to it.
- Counter: novae are rare and Aristotle had no record of one beyond the Moon; his inference was reasonable on his data. That defends his reasoning, not his conclusion. Confidence: high.

### M04 Empedocles/Aristotle, four elements. Gap 2238 (c. -450 to 1789)
- Evidence: Aristotle, Metaph. I.3 (MIT) reports Empedocles' four, with earth added to the three earlier principles. Lavoisier preface: he calls the four-element notion a prejudice from the Greek philosophers; table counted (5 + 3 + 3 + 17 + 5 = 33).
- Counter: "a few kinds of stuff combine in proportion to make all substances" is the structure of modern chemistry (Empedocles B96 gives a bone recipe in proportions). That is a PARTIAL match for a different, weaker claim; the claim graded here, that these four are the elements, is WRONG. Confidence: high.

### M05 Thales, water. Gap 2368 (c. -585 to 1784)
- Evidence: Metaph. I.3 (MIT): Thales says the principle is water and so the earth rests on water; Aristotle supplies a guessed reason ("getting the notion perhaps from").
- Caveats: Thales wrote nothing extant; we have Aristotle's report about 250 years later, in Aristotle's own vocabulary of "principle". The event chosen is Cavendish 1784 (water synthesised from two gases); Lavoisier's 1783 announcement is the rival choice (gap 2367). Volume/pages 74 (1784) 119-153 from memory, medium.
- Counter: Thales is credited with seeking one natural, non-mythic principle, which is the part that survived. That is a method, not the claim. Confidence: medium (attribution is second-hand).

### M06 Plato, regular-solid elements. Gap 2148 (c. -360 to 1789)
- Evidence: Timaeus (Jowett, MIT): cube to earth, pyramid to fire, then air and water; built from two right triangles; earth cannot pass into the others. Plato frames it as the "probable" account.
- Counter (strong): Plato labels it a likely story, so it is less "confident" than the Aristotle claims; and Heisenberg praised the idea that symmetry/mathematical form underlies matter. Reply: the specific assignments are asserted and wrong; the "mathematical form" reading is a LOOSE hit elsewhere, not a defence of this claim. The refuting event shares Lavoisier 1789 with M04 because the claim's objects are the same four. Confidence: high on text, medium on event choice (Dalton 1808 is an alternative).

### M07 Plato/Empedocles, extramission. Gap 1380 (c. -360 to 1021)
- Evidence: Timaeus (MIT, grep "stream of vision"): pure fire within flows through the eyes, coalesces with daylight, and carries motions back to the soul.
- Note: Plato's account is a hybrid (daylight is needed too). Ibn al-Haytham's target was mainly the mathematicians' visual ray (Euclid, Ptolemy), so causal_line is none-found for Plato himself.
- Counter: Euclid and Ptolemy may have used the ray as a geometrical device; but Plato's is plainly a physical claim. Confidence: high on text, medium on date.

### M08 Aristotle, spontaneous generation. Gap 2002 (to Redi 1668)
- Evidence: HA V.1 (MIT, grep "putrefying"): some animals arise spontaneously, not from kindred stock, some from putrefying earth or vegetable matter, as with many insects.
- Counter: Aristotle was a careful observer and Redi's result covered only flies; eels (which Aristotle says arise from mud) were not settled until the 20th century. Still WRONG for the class he named. Confidence: high.

### M09 Aristotle, eternal uncreated universe. Gap 2299 (to 1965)
- Evidence: De Caelo I.10-12 (MIT): argues the ungenerated is eternal and that generated and destructible coincide; II.1 opens with the conclusion that the heaven as a whole neither came into being nor can be destroyed.
- Counter (serious): whether the universe as a whole had an absolute beginning is open (eternal inflation, bounce models). Reply: Aristotle claimed an eternal cosmos in the same order, with no beginning of its duration; the hot-big-bang evidence refutes a changeless eternal cosmos even if a pre-big-bang phase exists. Page wording: "refuted as an unchanging eternal cosmos; whether time had a beginning is still open". Confidence: medium-high.

## Loose / hyped hits (side = HIT)

### M10 Zeno vs limits. LOOSE. Gap 2280 (c. -460 to 1821)
- Evidence: Physics VI.9 (MIT, grep "half-way", "Achilles").
- Rationale: Zeno posed a problem and concluded motion is impossible; he did not propose a finite sum of infinitely many terms. Posing the problem is not anticipating the answer. Arguably not an anticipation at all; I keep LOOSE because the series 1/2 + 1/4 + ... is implicit in the dichotomy.
- Counter: the paradox defined the object (an infinite series) the calculus later had to handle, and supertask debates (Thomson 1954, Benacerraf 1962) show the mathematics does not settle everything. Confidence: high on text.

### M11 Heraclitus fire-exchange vs energy conservation. LOOSE. Gap 2346 (c. -500 to 1847)
- Evidence: Burnet fr. 22 (Wikisource): all things an exchange for fire, as wares for gold. Burnet himself (sect. 72) reads the "measures" as keeping each form's aggregate constant.
- Rationale: an exchange analogy with a standard of value; the standard is a substance (fire), no quantity is defined or measured, nothing about heat-work equivalence. Event: Helmholtz 1847 as the general statement; Mayer 1842 and Joule's measurements (1845-50) are the alternatives.
- Counter (upward to PARTIAL): B90 plus B31's "same measure" says one quantity is common to all change and is preserved in exchange, which is the shape of the first law. Reply: shape only; no causal line (Kuhn 1959 traces Naturphilosophie, not Heraclitus). Confidence: medium.

### M12 Lucretius swerve vs quantum indeterminacy. LOOSE. Gap 1980 (c. -55 to 1926)
- Evidence: DRN 2 (Leonard tr., MIT): atoms decline a little at scarcely determined times and places; without it, no collisions; later lines tie the swerve to free will.
- Rationale: one-bit match (some uncaused micro-event). The swerve has no law; Born's probabilities follow a rule over outcomes. The motive is ethical. Deterministic interpretations of QM (Bohm) exist.
- Counter: very few ancient doctrines posit objective indeterminism in matter and argue it is physically required. Confidence: high on text.

### M13 Anaximander, humans from fish-like creatures. LOOSE. Gap 2408 (c. -550 to 1859)
- Evidence: Censorinus 4.7 (Latin, LacusCurtius): from heated water and earth came fish or fish-like animals; humans formed in them, were kept inside until puberty, then emerged able to feed themselves. The "infant cannot survive alone" argument is in Ps.-Plutarch (DK 12 A10), not opened. Plutarch 730E not opened.
- Rationale: a one-off birth story, not descent with modification; resemblance is in "humans came from fish".
- Counter: the conclusion (aquatic origin) is true and was argued from viability, not myth. Reply: lineage across generations is the whole content of Darwin's claim. Confidence: medium (late doxography).

### M14 Empedocles random combinations vs Darwin. LOOSE. Gap 2308 (c. -450 to 1859)
- Evidence: Physics II.8 (MIT, grep "perished"): things that by chance were organised fittingly survived; others perished and still perish, as Empedocles says of the man-faced ox-progeny. Burnet fr. 57, 61 (Wikisource) give the heads without necks and ox-men. The survival sentence is Aristotle's paraphrase, put forward to be rejected.
- Causal: Darwin's Aristotle footnote ("shadowed forth") was added in the 4th edition, 1866 (Swallow, Aristotelica 2023; consistent with wave-1's Gutenberg 6th-ed. check). It names Aristotle, not Empedocles, and came after the theory. So "documented" means a citation, not an influence.
- Counter (upward to PARTIAL): the filter of survival by fit is the core of selection; Burnet (1920) already called it survival of the fittest. Reply: no heritable variation, no populations, no time depth; the filter acts once on monsters. Confidence: high on text.

### M15 Augustine, time created with the world. PARTIAL. Gap 1572 (c. 398 to 1970)
- Evidence: Confessions XI (Pusey, Gutenberg; numbering from the Latin Library): 11.13.15 (God made that very time; no "then" when there was no time), 11.14.17 begins "ipsum tempus tu feceras" then asks what time is.
- Rationale: the structural claim (time is part of the world, no before) matches the classical-GR statement of a past boundary, was argued against a rival (an eternal world), and could have been wrong.
- Why not STRONG: the argument is theological; Plato (Timaeus 37d-38b) had time come to be with the heavens first; and the "confirmation" is a classical theorem at a point where GR is expected to fail, so whether time began is still open (Hartle-Hawking 1983, bounce models; BGV 2003 shows past-incompleteness, not a first moment).
- Counter (down to LOOSE): matching needs reading "time made with creation" as "spacetime has a past boundary", which is a retrofit; and the confirming event is not an observation. I keep PARTIAL but flag it as the most contestable grade in this file. No causal line: Lemaitre kept his physics apart from theology (wave-1 w1-04, unverified there). Confidence: medium.

## Instrument notes (all medium unless stated)
inclined plane with water clock: Galileo's experiments from c. 1604 (letter to Sarpi 1604); mercury tube 1643 (high); Tycho's sextant 1572; pneumatic trough: Hales, Vegetable Staticks 1727; Ibn al-Haytham's dark-chamber experiments are in the Optics itself; Redi's gauze cover 1668; Holmdel horn antenna built 1959; Joule paddle wheel 1845. Rows M10, M12-M15 have no instrument: the result was mathematical, theoretical, or from field observation.

## Pattern worth stating on the page
All nine misses were refuted by an observation or an instrument (balance, tube, sextant, gauze, antenna). Of the six "hits", five are LOOSE and the only PARTIAL (Augustine) is matched by a theorem, not a measurement. Gaps cluster at 1,900-2,400 years for both groups, so gap length does not distinguish hits from misses.

## Sources opened this session
- http://classics.mit.edu/Aristotle/physics.4.iv.html ; physics.2.ii.html ; physics.6.vi.html ; heavens.1.i.html ; heavens.2.ii.html ; metaphysics.1.i.html ; history_anim.5.v.html
- http://classics.mit.edu/Plato/timaeus.html ; http://classics.mit.edu/Carus/nature_things.2.ii.html
- https://www.gutenberg.org/cache/epub/3296/pg3296.txt (Confessions, Pusey) ; https://www.thelatinlibrary.com/augustine/conf11.shtml
- https://www.gutenberg.org/cache/epub/30775/pg30775.txt (Lavoisier, Kerr tr.)
- https://penelope.uchicago.edu/Thayer/L/Roman/Texts/Censorinus/text*.html
- https://en.wikisource.org/wiki/Early_Greek_Philosophy/Herakleitos_of_Ephesos ; .../Empedokles_of_Akragas
- Search snippets only (not opened): https://aristotelica.cnr.it/ojs/index.php/A/article/view/794 (Darwin footnote 1866); https://en.wikipedia.org/wiki/Book_of_Optics and https://iis.ac.uk/ar/encyclopaedia-articles/ibn-al-haytham-or-alhazen (dating).
