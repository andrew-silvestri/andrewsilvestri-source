# opinions_book3.csv notes

Source: armchair/data/placita_dowel.txt, Gutenberg lines 5421-5872 (Book III, read in full: 452 lines).
Verification: re-read with csv.DictReader gives 85 rows, 18 chapters, 85 unique ids (exit 0).

## Counts
Total rows: 85. Chapters: 18 (I-XVIII), all present.

| ch | rows | ch | rows | ch | rows |
|---|---|---|---|---|---|
| 1 Milky Way | 9 | 7 winds | 4 | 13 earth's motion | 4 |
| 2 comets | 12 | 8 winter/summer | 1 | 14 zones | 1 |
| 3 thunder etc. | 5 | 9 earth's nature | 5 | 15 earthquakes | 11 |
| 4 clouds/rain | 3 | 10 earth's shape | 5 | 16 sea | 6 |
| 5 rainbow | 6 | 11 earth's position | 4 | 17 tides | 5 |
| 6 rods | 1 (placeholder) | 12 earth's inclination | 2 | 18 halo | 1 (placeholder) |

## Judgement calls
- Ch VI (5616-5620) and ch XVIII (5862-5868): only unattributed explanation in the compiler's voice; one "-" / "(no attributed opinion)" row each.
- Ch V: the long unattributed rainbow explanation (5553-5557, 5568-5596: reflection from small drops, red/purple/green) is the compiler's own account and was skipped as framing. Kept as rows: Plato's Thaumas etymology (5559-5560), Homer's verse (5560-5563), and the unnamed bull's-head fable (5565-5566), since each is an attributed or "others" statement about the rainbow. Drop B3.5.1-B3.5.3 if only causal accounts are wanted.
- Ch I opening definition (5440-5442), the Book III preface (5424-5430) and the Meteors/terrestrial transition (5656-5657): framing, skipped.
- Ch II: Heraclides' entry plus "this way go all the Peripatetics" (5478-5484) merged into one row, holders "Heraclides of Pontus; the Peripatetics". Anaxagoras appears twice (comet with Democritus; shooting stars alone) as two different answers. Metrodorus (5489-5490) has no explicit subject; read as about the shooting fires just mentioned.
- Ch VII: the Etesian-wind sentence (5637-5640) has no named subject; attributed to Metrodorus by continuation and kept as its own row (B3.7.4). Flag if a grader needs a stated holder.
- Ch XV: Anaximenes gives two separate answers (dryness/rarity at 5769-5772; earth borne on air at 5787-5788), so two rows. Several entries from 5780 onward (Metrodorus, Parmenides; Democritus, Anaximenes, Plato) answer why the earth stays put rather than why it quakes; kept under ch XV as the text places them.
- Democritus appears twice in ch XV (with Thales; with Parmenides) because the text gives two different answers.

## Unparsed lines
None. Footnote marker [43] at 5563 ignored.

## Spelling choices
Phaethon (text: Phaëton); Boethus (Boëthus); Pytheas of Massalia (text: "the Massilian"); Seleucus the mathematician (as text); Hicetes the Pythagorean; Heraclides of Pontus where the text says "native of Pontus" (ch II, XIII); plain "Heraclides" in ch XVII where the text gives no city; Timaeus left unqualified (text gives no city); Philolaus without "the Pythagorean" in holders; "Thales and his followers" for "Thales and his followers" / "disciples of Thales"; "the school of Plato" for "The schools of Plato"; "some Pythagoreans" for "Some of the Pythagoreans"; "unnamed" for "others" / "most of the philosophers". No Zeno or Diogenes disambiguation needed except ch II "Diogenes", left unqualified (text gives none).
