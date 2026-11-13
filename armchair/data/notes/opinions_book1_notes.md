# Book I extraction notes

Source: `armchair/data/placita_dowel.txt`, Gutenberg lines 3731-4770, all 1040 lines read (758 non-blank).
Output: `opinions_book1.csv`. It was built by a Python script (csv module) that checks each opinion is at most 30 words, that each line range falls inside 3731-4770, and that ids are unique. It was then read back: 119 rows, 119 unique ids, longest opinion 30 words.

## Totals

- 119 rows.
- Chapters I-XXX: all 30 are present (30 `CHAPTER` headings counted in the range). There is also chapter 0 for the untitled preface (see below).

Rows per chapter: 0:2, 1:1, 2:2, 3:14, 4:1, 5:4, 6:2, 7:15, 8:2, 9:5, 10:3, 11:3, 12:4, 13:2, 14:1, 15:5, 16:3, 17:4, 18:5, 19:2, 20:1, 21:3, 22:4, 23:6, 24:3, 25:3, 26:4, 27:3, 28:6, 29:4, 30:2.

## Judgement calls

- **Preface (3734-3765)** has no chapter number, but it gives two attributed opinions: the Stoics' three-part division of philosophy, and the Aristotle/Theophrastus/Peripatetic split into theory and practice. I coded them as chapter 0 (`B1.0.1`, `B1.0.2`). Drop chapter 0 if downstream expects 1-30 only.
- **Ch. IV** (atomist cosmogony) names no one, so the holder is "unnamed".
- **Ch. VI**: both rows are attributed to the Stoics. The passage opens with "The Stoics thus define..." and the account of transmission and the seven kinds of gods (4157-4205) continues it without naming anyone new.
- **Ch. VII**: the long argument at 4264-4297 is the compiler's own polemic. It says a blessed, immortal being would not trouble with the world and cites Agamemnon and Hercules. I skipped it as framing, along with the compiler's attack after the Callimachus verse at 4250-4252 that God cannot do everything. The Callimachus verse itself (4245-4248) is kept as an attributed view. Plato appears twice (4252-4253 world in God's image; 4260-4263 God ordered disordered bodies) because the text gives two separate claims.
- **Ch. II**: the compiler's remarks that Thales is "peccant" were dropped. So were the criticisms of Anaximander and Anaximenes (Ch. III) and the rebuttal of Plato (Ch. V, 4093-4100). Only the opinions were kept.
- **Ch. III** atomists: one shared row (Epicurus; Democritus, since the text says their views are the same) plus separate rows for Democritus (atoms have size and shape only) and Epicurus (adds weight), because the text sets these against each other. Pythagoras's soul-as-tetrad passage (3930-3953) is folded into his single principles row.
- **Ch. IX, XVI, XVII, XXII, XXIV**: "they that say...", "Others", "the ancient philosophers" and "most philosophers" are coded "unnamed", with a parenthetical where the text identifies the group.
- **Ch. XV**: the Pythagoreans get two rows, one for what colour is and one for its four kinds, because the text states them separately.
- **Ch. XXVIII**: Chrysippus gets two rows, because the text separates his second definition with "Again, in his book styled the Definitions".
- **Ch. XVIII** line 4558: "Aristotle,[42]" carries a translator footnote marker. The footnote text lies outside the range and was not consulted. The opinion is attributed as printed.

## Spelling choices

- "Zeno son of Mnaseas, of Citium" (Ch. III) and "Zeno the Stoic" (Ch. XV) are written as Zeno of Citium. In Ch. X, "Stoics of the school of Zeno" is written as "the Stoics (school of Zeno of Citium)".
- In Ch. XXIV, Zeno is written as Zeno of Elea. The text says only "Zeno", but it pairs him with Parmenides and Melissus and gives the denial of motion, so Elea is inferred from context.
- Euemerus is spelt Euhemerus. Diagoras the Melian is spelt Diagoras of Melos. Theodorus the Cyrenean is spelt Theodorus of Cyrene. Hippasus of Metapontum is shortened to Hippasus.
- "Followers/disciples of X" is kept as a holder ("the followers of Thales"), and "Pythagoras' disciples" is written as "the Pythagoreans".
- Euripides (Ch. VII) is the holder for the Sisyphus speech. The paraphrase says it is voiced through the character.

## Unparsed lines

None. The verse quotations and the compiler's framing were read and deliberately skipped, as noted above.
