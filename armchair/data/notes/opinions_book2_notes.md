# opinions_book2.csv - notes

Source: `armchair/data/placita_dowel.txt`, Gutenberg lines 4771-5420 (Book II, Dowel tr.), read in full.
Generator: `C:\Users\dasil\AppData\Local\Temp\b2_extract\b2_extract.py` (`python -I`, exit 0).

## Counts

Total rows: 144. Chapters: 32 (I-XXXII; headings found by script at 4782 ... 5401, all 32 present).

Rows per chapter:
1:6 2:4 3:3 4:4 5:3 6:5 7:6 8:2 9:5 10:2 11:3 12:1 13:9 14:4 15:6 16:5
17:4 18:2 19:3 20:9 21:4 22:4 23:6 24:8 25:7 26:2 27:4 28:4 29:6 30:3 31:3 32:7

## Checks the script runs before writing (any failure exits 1, writes nothing)

- every line_start/line_end lies inside its chapter's span and points at a non-blank line;
- opinion <= 30 words, question <= 12 words;
- no 6-word run in any opinion appears in Book II's source text (no-quotation check). First run
  failed on 13 rows (e.g. "the sun is eclipsed when the"); those were reworded and the run re-done.
  So the check has been seen to fire, not only to pass.

## Skipped as non-opinions (not rows)

- 4774-4777: compiler's preface to Book II.
- 4787-4788 (ch. 1): Pythagoras first called the world "kosmos" - naming/etymology, not an answer.
- 5010-5012 (ch. 12): priority dispute, Pythagoras vs Oenopides of Chios, over discovering the
  zodiac's obliquity - history of discovery, not a division of heaven.
- 5145-5147 (ch. 19): Aratus verse kept inside the Eudoxus; Aratus row's span, not a separate row.

## Judgement calls

- ch. 2, 32: "others ... others" / "some ... some ... others" with different answers -> one "unnamed"
  row per distinct answer.
- ch. 3 "All the other philosophers", ch. 6 "The natural philosophers", ch. 29 "Some of the later
  philosophers": holder "unnamed", with the text's label in brackets at the start of the opinion.
- ch. 6: final sentence "In all these Plato hath the same sentiments with Pythagoras" -> Plato added
  as holder on the five-solids row.
- ch. 13: Diogenes' pumice/breathing stars and his falling invisible stones kept as one compound row;
  Empedocles appears twice (origin of stars; fixed stars on the crystal, planets loose) because the
  text gives two different answers.
- ch. 13: "this opinion is current among the followers of Orpheus" -> "followers of Orpheus" added
  to the Heraclides; the Pythagoreans row.
- ch. 15: "Plato and some of the mathematicians conspire in the same opinion" -> holders
  "Plato; some mathematicians" on Plato's planetary order.
- ch. 24: Xenophanes has three rows (sun quenched and renewed; many suns, one straying into an
  uninhabited region; apparent circular motion due to distance). His reported month-long and total
  eclipses are folded into the first row.
- ch. 32: the unattributed planetary periods (Saturn 30 yrs etc.) are one "unnamed" row.

## Text oddities, recorded as printed (not corrected)

- ch. 4, 4844: "[and Plato]" is an editorial bracket in the source; Plato kept as holder.
- ch. 9, 4956: "the infinite world" in the Stoic sentence; paraphrased neutrally as "the world".
- ch. 15, 5070: "The other Stoics" follows Xenocrates (not a Stoic); holder written "the Stoics".
- ch. 20 vs 21: Anaximander's sun-ring is 28x the earth in ch. 20 and 27x in ch. 21; both kept.
- ch. 23, 5226: Anaximenes' sentence says "the stars", not the sun; paraphrase says "heavenly bodies".
- ch. 24, 5262: "the earth [the moon?]" is an editorial query in the source; kept as "earth
  (editor queries 'moon')".
- ch. 29, 5345: lunar eclipse by the blocked wheel-mouth is printed under Anaximenes (the wheel
  model is elsewhere given to Anaximander); holder kept as printed, "Anaximenes".

## Spelling choices

- Diogenes: never qualified in Book II, so "Diogenes" (not "of Apollonia") throughout.
- Metrodorus: "Metrodorus" except ch. 15, where the text says "Metrodorus of Chios".
- Heraclides: as printed (no "Ponticus" in the text). Zeno does not occur in Book II.
- Pythagoreans: "Pythagoras; the Pythagoreans" for "Pythagoras and his followers"; "some
  Pythagoreans" in ch. 29. "Thales and his followers" -> "Thales; followers of Thales".
- "those philosophers who introduced atoms and a vacuum" -> "the atomists".
- Place/name forms: Aegospotami, Peloponnese, Phaethon (Dowel: Phaëton), Antichthon; "furlongs"
  given as stades (780,000).
- Unparsed lines: none.
