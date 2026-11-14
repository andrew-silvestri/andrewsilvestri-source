# opinions_book4.csv - notes

Source: armchair/data/placita_dowel.txt, Gutenberg lines 5873-6458 (Book IV, chapters I-XXIII). The whole range was read; it ends at line 6458, just before "BOOK V." at 6459.
Built by: `python -I %TEMP%\b4_extract.py` (exit 0). It reported 85 rows, 23 chapters, no chapter missing, no paraphrase over 30 words (max 30), no question over 12 words (max 11). The written CSV was read back with csv.DictReader: 85 rows, 85 unique ids.

## Rows per chapter
| ch | rows | ch | rows | ch | rows |
|---|---|---|---|---|---|
| 1 Nile | 7 | 9 | 3 | 17 | 2 |
| 2 | 6 | 10 | 3 | 18 | 2 |
| 3 | 6 | 11 | 1 | 19 | 5 |
| 4 | 4 | 12 | 1 | 20 | 2 |
| 5 | 13 | 13 | 4 | 21 | 1 |
| 6 | 2 | 14 | 3 | 22 | 3 |
| 7 | 4 | 15 | 2 | 23 | 3 |
| 8 | 4 | 16 | 4 | | |

Total 85. Every chapter has at least one attributed opinion, so no "(no attributed opinion)" placeholder rows were needed.

## Judgement calls and lines that did not parse cleanly
- B4.3.1 (5940-5943): the text says "All those that have been named by me" hold that the soul is incorporeal. It names no one, and the predicates (self-moving, intelligent substance, actuality of an organic body) echo Thales, Pythagoras, Plato and Aristotle in ch. II, so those four are listed. Dicaearchus and Asclepiades, also named in ch. II, are left out. This is an inference.
- B4.1.7: the opinion is the Egyptian priests' as reported by Eudoxus. Both are listed as holders.
- B4.5.12: "Certain of the Neoterics" (some recent thinkers) is coded as "unnamed".
- B4.7.1 and B4.7.4: Plato and Pythagoras appear twice in ch. VII (whole soul immortal and returns to the world-soul; then only the rational part eternal, the irrational part dies). The text gives these as two separate statements, so there are two rows.
- B4.4.3 and B4.4.4: Democritus appears in a joint two-part division with Epicurus and then alone (all things, even corpses, share in soul). These are different answers, so there are two rows.
- B4.9.2 (6069-6074): Epicurus' sentence is garbled in Dowel (sense "gives a false representation" only of objects of understanding; the fancy gives a "double error"). The paraphrase keeps the clear part: all impressions are true, opinions are mixed, and imagination can mislead about sensible and intellectual things. It does not settle the garbled clause.
- B4.11.1, B4.12.1, B4.21.1, B4.22.3: these long single-holder passages (Stoics, Chrysippus, Stoics, Herophilus) are each kept as one compound row. The Orestes and Electra verses and the Theoclymenus remark (6160-6174) count as illustration inside Chrysippus' row.
- Skipped as compiler framing, not opinion: 5876-5877 (book preface); 6317-6318 (the objection "How can some fragments of air fill a theatre...", which is unattributed and is a rejoinder, not an answer); the definitions at 6042-6046 are folded into the Stoic row.
- B4.20.2: the pyramid echo remark (6350-6351) is read as part of the Stoic passage.

## Spelling choices
- Euthymenes "the Massilian" is written "Euthymenes of Massalia".
- "Diogenes" (5.7, 16.3, 18.2) is left unqualified. The text does not say "of Apollonia", although the doctrines fit him.
- "Strato" (5.2, 23.3) is Strato as spelt in the text (Strato of Lampsacus is probable but not stated).
- "Heraclides" (9.3) is left unqualified (probably Heraclides of Pontus; not stated).
- "Lybia" is written Libya; "Epikranis" is paraphrased as the membrane around the brain.
- Group holders: "the Stoics", "the Pythagoreans" (Dowel's "followers of Pythagoras"), "the followers of Anaxagoras", "Plato and his followers". Each is kept as the text groups them.
- Other holders as spelt: Thales, Anaxagoras, Democritus, Herodotus, Ephorus, Eudoxus, Pythagoras, Plato, Aristotle, Dicaearchus, Asclepiades, Epicurus, Heraclitus, Erasistratus, Herophilus, Parmenides, Empedocles, Leucippus, Chrysippus, Hipparchus, Alcmaeon.
