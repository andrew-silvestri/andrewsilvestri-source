# W2-01 Ancient hits (cases A01-A10): evidence notes

CSV: `data/cases_ancient_hits.csv` (10 rows), written by `data/scripts/build_cases_ancient_hits.py` (`python scripts/build_cases_ancient_hits.py`, run from `research/data`, exit 0). A separate check recomputed every gap_years from idea_year and confirm_year, applying the no-year-0 rule only when the span crosses from BCE to CE: 10/10 OK. A06 is BCE to BCE, so it gets no correction.

Downloads are in `data/raw/w2-01/`: Hammond 1902 *Aristotle's Psychology* (djvu text), Heath 1913 *Aristarchus of Samos* (djvu text), Latin Library Lucretius books 1-2, Wikisource D.L. Book X (Hicks), MIT Classics Aristotle (Meteorology, Heavens, Gen. & Corr., Metaphysics), New Advent Hippolytus *Refutation* Book I, Boyle *Continuation* 1669 (EarlyPrint text) and *New Experiments* 1660 (MPIWG), Desaguliers Phil. Trans. 1717 and Bradley Phil. Trans. 1729 (Phil. Trans. OCR archive), Newton General Scholium 1713 Latin PDF, Galileo *Sidereal Messenger* (Gutenberg 46036), Lavoisier *Elements* (Gutenberg 30775), Couprie 2017 PDF, Barnes notes PDF.

Line-number method for Lucretius: the Latin Library text prints a marker every 5 lines. I read the passages against those markers: 2.110/115/120...140 and 2.220...245, and 1.150 and 1.265.

---

## A01. Leucippus/Democritus: matter is atoms and void (HIT, STRONG; Perrin 1909)

- Text: Aristotle, *Metaph.* A.4 (MIT text, opened). Leucippus and Democritus make the full and the empty the elements, and things differ by shape, order and position (the letter analogy A/N, AN/NA). *GC* I.8 (MIT, opened) gives Leucippus's "many", infinite in number and invisible because they are so small, moving in the void. The Bekker numbers (985b4-20; 325a23-b5) and DK 67 A6/A7 come from SEP *Democritus*. The MIT pages print no Bekker numbers.
- **Dalton 1808 or Perrin 1909? Decision: Perrin.** (1) Dalton's atom was a chemical bookkeeping unit. Whether atoms were physically real stayed disputed by chemists and physicists (Ostwald, Mach) until 1908-09. SEP *Atomism from the 17th to the 20th Century* §5.4 says Ostwald and others conceded the case after Perrin's experiments, and §6.1 dates those experiments from 1908. (2) The ancient claim is particles *moving in void*. Perrin measured exactly that: thermal agitation, and the number of molecules, from several independent methods that agreed. Dalton measured combining weights. (3) SEP §4.2 says Dalton broke with the Democritus-to-Newton assumption of one kind of matter, so Dalton is a weaker match to Democritus than Perrin is. The 1909 *Annales* memoir rather than the 1908 *Comptes rendus* note: 1909 is the full concordance argument. Using 1908 changes the gap by one year. Perrin 1909 citation (*Ann. chim. phys.* 8e sér. 18, 5-114): standard reference, not opened. Le Moyne's Soddy-translation excerpt was opened.
- Instrument: Perrin counted grains through a microscope with a water-immersion objective, with a camera lucida and instantaneous photographs. The emulsions were prepared by centrifuging. He used no ultramicroscope (Le Moyne excerpt). instrument_year 1908 is the date of the emulsion technique, not of the microscope.
- Grade STRONG: it was asserted and argued, it contradicted the continuum views, and it could have been wrong. Counter: the argument was a reply to Parmenides, not evidence, and nothing quantitative was at stake. The surviving content is "particulate and moving", while "uncuttable" failed (A02).

## A02. Atoms are indivisible (MISS, WRONG; Thomson 1897)

- Text: in *GC* I.8 (MIT, opened) the Leucippan solids are indivisible plena with the void outside them. SEP *Democritus* calls atoms solid and without void inside. The refuting event is J.J. Thomson, "Cathode Rays", *Phil. Mag.* 44 (1897) 293-316 (citation confirmed via Wikiquote/chemteam; paper not opened). He found corpuscles far lighter than hydrogen and the same from every source. Rutherford 1911 (nucleus) follows.
- Counter: the Greek claim concerned the *ultimate* level. Quarks and leptons have no known parts, so the claim is refuted only for the chemical atom that inherited the name.

## A03. Democritus: Milky Way is many faint stars (HIT, STRONG; Galileo 1610)

- Aristotle *Meteor.* I.8 (MIT, opened) credits Anaxagoras *and* Democritus: stars hidden from the Sun by Earth's shadow show their own light. Aristotle rebuts it: the band does not move with the Sun, and the shadow cone ends well short of the stars. Locator 345a25-31 = DK 59 A80 is from Couprie, *Hyperboreus* 23:2 (2017) 181-207 (opened).
- Aëtius gives Democritus a cleaner, shadow-free version: many small, closely packed stars whose light merges because they are dense (Ps.-Plut. *Plac.* 3.1.6 = DK 68 A91, locator per Couprie). The Greek appears on the nLab *Democritus* page, a secondary source. I did not open an edition of the *Placita*. Couprie also files the Alexander of Aphrodisias commentary under 68 A91.
- Galileo, *Sidereus Nuncius* (Gutenberg Carlos trans., opened): he says the telescope settles the age-old dispute and the Galaxy is nothing else but a mass of innumerable stars. He names no ancient source.
- Grade STRONG on the observable claim. Counter: it is a doxographic report, the shadow version is wrong, and the naked-eye mottling made "stars" a natural guess. Couprie warns against crediting these Greek astronomical guesses. Aristotle's exhalation theory was the rival.

## A04. Epicurus/Lucretius: equal speed of fall in void (HIT, PARTIAL; Desaguliers 1717)

- Texts (opened): *Ep. Hdt.* 61 (Hicks, Wikisource): in void with nothing resisting, heavy and light atoms move at equal speed, "quick as thought". This is about *atoms*. Epicurus says composite bodies do move at different speeds (§62). Lucretius DRN 2.225-242 (Latin Library) is closer to the modern claim. Water and thin air hold back light bodies more than heavy ones, but the void gives way to all. His conclusion, "aeque ponderibus non aequis concita ferri" (2.239), means all must move equally despite unequal weights. He reasons from the medium, as Galileo later did.
- **Who first showed feather and coin falling together in an evacuated vessel?**
  - Boyle did not. In *A Continuation of New Experiments* (Oxford 1669), Experiment 40 (EarlyPrint text, opened), he dropped a cross of four feathers in an exhausted receiver. It fell like a dead weight without turning. But he says he wanted to test heavy against light bodies and his receiver was too short, even with a quarter-second pendulum. The popular "Boyle 1660 guinea and feather" is also anachronistic: the guinea coin was first struck in 1663.
  - Newton, *Principia* 2nd ed. (1713), General Scholium p. 482 (Latin PDF, opened), states as fact that in Boyle's vacuum a thin feather and solid gold fall with equal speed. He gives no date or performer.
  - The earliest dated, described performance I found is J.T. Desaguliers, *Phil. Trans.* 30 (1717) (opened). In 1716, before George I, he dropped a guinea and a feather in a 20-inch exhausted receiver. In Sept. 1717 at Hampton Court, and on 5 Dec 1717 at the Royal Society, he used four stacked receivers (~8 ft) to answer plenists who said 20 inches was too short. At home, before Martin Folkes, a feather lagged in air, but with the air fully pumped out the feathers and papers reached the bottom "at the same instant of time as the Guinea".
  - Someone (Hauksbee is a plausible candidate) may have done it before 1713. **Unverified.**
- **Decision:** confirm_event is Desaguliers 1717, the first documented direct test of the void claim itself, with a quantitative control in air. Galileo 1638 was rejected as the event because it argues and extrapolates from media of decreasing density and could not remove the air. Alternatives for the page: Galileo 1638 gives gap ~1937; Newton's 1713 statement gives ~2012.
- Grade PARTIAL. Same respect: mass-independence once the medium is removed, with the right reasoning. Differences: constant speed rather than acceleration, an absolute down, and in Epicurus a claim about atoms. Counter (upward): the claim was explicit and risky, Aristotle (*Phys.* IV.8) used it as a reductio, and it was correct. Counter (downward): the swerve shows the claim served atomist collisions, not falling bodies.

## A05. Empedocles: light travels and takes time (HIT, STRONG; Rømer 1676)

- Verified. Aristotle *De An.* II.7 says Empedocles held that light travels and arrives between Earth and its envelope without our noticing. Aristotle replies that over the whole span from east to west the claim is too much to assume. Hammond's 1902 translation (archive.org, opened) cross-references "De an. 418b 20" in its *De Sensu* note. The MIT Smith translation (opened) has the same content.
- *De Sensu* 6 (Hammond, opened; Bekker ~446a24-b2): Empedocles says sunlight reaches the intermediate space before the eye or Earth. Aristotle half-concedes that this "seems to be reasonable" for any locomotion, then argues light is a qualitative change instead.
- Heath 1913 pp. 92-93 (opened) calls this Empedocles' one important scientific achievement and quotes both passages. DK 31 A57 for these testimonia: **unverified**, so it is left out of the CSV locator.
- Rømer: *Journal des Sçavans*, 7 Dec 1676; English in *Phil. Trans.* No. 136, 25 June 1677 (chemteam page, opened). He found about 22 minutes for light to cross Earth's orbit, from Io eclipse timings.
- Grade STRONG: the core claim (finite propagation, imperceptibly fast) matches, it was asserted, and it was risky. Aristotle, and later Kepler and Descartes, held light to be instantaneous. Strongest counter: no words of Empedocles survive on this. It comes from a hostile reporter, follows from his effluence theory (one option the theory forced), and gives no magnitude, so PARTIAL is defensible.

## A06. Anaxagoras: Moon's light from the Sun; eclipses (HIT, STRONG; Aristarchus c. 270 BCE)

- Hippolytus *Ref.* I (ANF ch. 7, which is standard 1.8; New Advent, opened). The Moon has no light of its own but from the Sun. It is eclipsed when Earth is interposed, and sometimes by bodies beneath the Moon. The Sun is eclipsed when the Moon is interposed at new moon. "He was the first to frame definitions regarding eclipses and illuminations." Couprie cites A42(6) for Moon light and A42(10) for the Milky Way, which fixes DK 59 A42 = Ref. 1.8.
- Transmission: Heath ch. X (opened) quotes Plato *Crat.* 409a ("which Anaxagoras recently asserted") and Plutarch *Nicias* 23. Heath rejects Parmenides' priority as resting on a possibly interpolated line. Aristarchus, *Sizes and Distances*, hypothesis 1: "That the moon receives its light from the sun" (Heath p. 353 by the page header that follows, opened).
- Grade STRONG on the claim. Caveat for the page: the gap is about 180 years and the confirmation is within ancient astronomy, so this is a fast *acceptance* more than a long-range anticipation. Counter: phases and the shape of Earth's shadow make the inference easy, the extra invisible eclipsing bodies are an ad hoc patch, and Couprie argues the Milky Way shadow theory conflicts with the lunar-eclipse shadow theory.

## A07. Anaximander: Earth hangs unsupported (HIT, PARTIAL; Newton 1687)

- Hippolytus *Ref.* I (ANF ch. 5, which is standard 1.6; opened): the Earth is poised aloft, held by nothing, and stays because it is equally distant from all things. It is shaped like a stone column drum. Aristotle *De Caelo* II.13 (MIT, opened) names Anaximander among those who say the Earth stays because of "indifference", calls the view clever but not true, and gives his hair-under-even-tension and starving-man analogies.
- Locators: 295b10-16 is confirmed by secondary sources (Kočandrle; philopedia). **Caveat:** Barnes's notes put Eudemus fr. 145 W (via Theon of Smyrna) under DK 12 A26, and that report oddly has Anaximander's Earth *moving*. So A26 is not purely the Aristotle passage.
- Grade PARTIAL. The geometric insight (no absolute down, no support needed) is right and was argued. The mechanism is symmetry, not force, and Newton's Earth is not at rest. Counter: an unsupported Earth was routine by Aristotle's time, so "anticipating Newton" overstates it. The better framing is the first break with the idea that Earth needs a floor.

## A08. Philolaus/Pythagoreans: Earth moves (HIT, PARTIAL; Bradley 1729)

- D.L. 8.85 (Thayer/Hicks, opened): Philolaus was first to say the Earth moves in a circle, though some credit Hicetas. Aristotle *De Caelo* II.13 (MIT, opened): the "Pythagoreans" put fire at the centre and make Earth one of the stars, producing night and day by moving round the centre, plus a counter-earth. Aristotle says they force observations to fit their theories. He does not name Philolaus.
- DK 44 A16-A21 as a range: **unverified** (SEP *Philolaus* cites only A20). The Aëtius 3.13 passage is the one Copernicus quotes via Plutarch in his dedication: Philolaus moved Earth round the fire in an oblique circle (Fordham sourcebook, via search summary). That gives a documented causal line, though as rhetorical authority rather than evidence.
- **Bradley 1729 or Bessel 1838? Decision: Bradley.** It is the first observed effect produced by Earth's orbital motion (Phil. Trans. 35, 637-661, opened). Bradley himself concedes that with no measurable parallax, anti-Copernicans could still deny Earth's motion, but only by also denying the progressive motion of light. Rømer had already shown that motion. Bessel 1838 closed the parallax objection 109 years later and is the more *geometric* proof. With Bessel the gap would be 2257.
- Mismatch: Philolaus' motion is a *daily* circuit around an invisible fire, kinematically close to rotation. Bradley proves the *annual* orbit. The best kinematic match would be Foucault's pendulum (1851, Earth's rotation).
- Grade PARTIAL; LOOSE is defensible. Only "Earth moves, not the centre" survives, and the centre, counter-earth and motive were wrong.

## A09. "Nothing comes from nothing" vs Lavoisier 1789 (HIT, PARTIAL)

- *Ep. Hdt.* 38-39 (Hicks, opened): nothing comes from the non-existent, or anything could arise from anything without seeds. Nothing perishes into non-being. The sum of things always was and will be as now. Lucretius DRN 1.149-266 (Latin Library, opened): 1.150 states the principle, and 1.265-266 sums it up: things cannot be created from nothing nor return to nothing.
- Lavoisier, *Traité* Part I ch. XIII (Kerr trans., Gutenberg, opened): in all operations of art and nature nothing is created, and matter and elements are equal before and after. He calls it an "incontestible axiom" and names no ancient.
- Grade PARTIAL. Counter (upward): Lavoisier also asserted it as an axiom, and his elements-conserved version is *closer* to the atomists than to modern physics. Counter (downward): the ancient claim conserves uncuttable atoms and is about kinds, not weighed quantities. Rest mass alone is not conserved (E=mc^2). The 1774 sealed-vessel weighings that turned the axiom into evidence were not opened in this session, so instrument_year 1774 is unverified.

## A10. Lucretius: motes in a sunbeam vs Perrin 1908 (HIT, LOOSE)

- DRN 2.112-141 (Latin Library, opened). Specks in a sunbeam through a dark room fight and part endlessly, a likeness and image of the first-beginnings' motion. From 2.125 on, he says their tumbling shows hidden motions of matter: blind blows, passed up from atoms to small clusters to the visible specks.
- Perrin (Soddy trans. 1910, Le Moyne excerpt, opened) explicitly sets aside the comparison with dust in sunlight: air currents carry neighbouring dust in the same direction, while Brownian grains move independently. The 1908 *Comptes rendus* note is cited there as May 1908. I did not open vol. 146 pp. 967-970.
- Grade LOOSE: right form of inference, wrong phenomenon, no quantitative content, no causal line. Counter: the stated cause (unseen molecular blows on small particles) is the correct physics of Brownian motion. He was wrong only about which effect dominates for visible motes.

---

## Flags (outside the CSV, for the editor)
- Unverified in session: DK 31 A57; DK 44 A16-A20; Perrin 1909 page range; Thomson paper text; Lavoisier 1774 experiments; who first did a vacuum drop before 1713.
- Confirm_event choices that change gaps: A01 (Dalton gives 2237); A04 (Galileo 1638 gives 1937); A08 (Bessel gives 2257).
