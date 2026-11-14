# opinions_book5.csv notes (Placita Book V, Gutenberg #78851 lines 6459-7135)

Source: armchair/data/placita_dowel.txt, file lines 2738-3414, read in full (no sampling).
Generator: C:\Users\dasil\AppData\Local\Temp\b5_extract\b5_extract.py (`python -I`, exit 0). It refuses to write if any question has more than 12 words, any opinion has more than 30, a line number falls outside 6459-7135, or a chapter is missing. The length check fired on three rows during drafting, which were then trimmed.
Check: each row's line_start/line_end falls between its own CHAPTER heading and the next one; 30/30 chapter headings were found in the source; ids are unique (exit 0).

## Totals
106 rows, 30 chapters (I-XXX). Every chapter has at least one attributed opinion, so none needed the "-" placeholder.

Rows per chapter:
1:4 2:3 3:6 4:3 5:4 6:1 7:8 8:3 9:3 10:4 11:3 12:3 13:3 14:2 15:5 16:3 17:6 18:6 19:5 20:5 21:2 22:1 23:4 24:1 25:4 26:5 27:1 28:1 29:2 30:5

## Lines not parsed / textual problems
- Ch XXVIII (7073-7075): the text breaks off mid-sentence ("As to the motions of dangers ... &c...."). Only the complete first sentence is used.
- Ch XVIII has a blank line inside the chapter (6824). The Aristotle/Hippocrates opinion continues after it, so it was treated as the same chapter.
- Ch XI, 6670-6672 ("Women have a concurrent emission of seed..."): this sentence has no holder of its own. It follows the Stoic opinion directly, so it was folded into the Stoics' row B5.11.3. That attribution is an inference.
- Ch XXIX: the chapter title asks whether fever is "annexed to a primary passion"; Erasistratus's endorsement of that idea (7094-7095) is included in his row.
- Euripides verse lines (6867-6868) are a quotation supporting the Epicurean row B5.19.2, not a separate opinion.
- The chapter title spellings "PROGENTITORS" (XI) and "HOW IF COMES" (XIV) are source typos; the modernised questions ignore them.

## Splitting choices
- Hippo, ch V: two rows (B5.5.3 on women's seed; B5.5.4 "the same also asserts" bones from the man, flesh from the woman). The text marks the second as a separate assertion.
- Hippo, ch VII: two rows (B5.7.3 thick vs thin seed; B5.7.8 seminal power vs nourishing material). The text states them in separate places, and they give different mechanisms.
- Polybus, ch XVIII: one row jointly with Diocles and the Empirics (B5.18.3), plus one row alone (B5.18.5, the 182.5-day reckoning).
- Empedocles, ch XIX: two rows (four stages of generation; sorting of animals to habitat by temperament). Ch XXVI: three rows (plants are animals, held jointly with Plato; trees as first living things and growth by earth's heat; fruits, leaves and juices).
- Empedocles and Diocles, ch XIV: one row. Diocles is said to "concur" and adds dissection evidence.
- Ch XVII "Some think the great toe ... others affirm the navel": two unnamed rows.

## Holder spelling choices
- Groups named by profession are kept as holders, not "unnamed": "physicians" (ch XIII, XVII), "physicians (most)" (ch XII "the greatest part of physicians"), "physicians (some)" (ch VIII), "the astrologers", "the Empirics". Reclassify them as unnamed if the merge needs that.
- "unnamed" is used for ch XVII's great toe and navel answers and for ch XIX "those philosophers who entertain the opinion that the world had an original".
- "the Epicureans" for "the followers of Epicurus" (XIX) and "Epicureans" (XXVI).
- "Zeno" (ch IV) is left unqualified because the text does not say which Zeno.
- "Diogenes" (ch XV, XX, XXIII) is left unqualified because the text never says "of Apollonia".
- "Timaeus" (ch XVIII) is left as written; the text does not say whether this means the Locrian or the historian.
- Other names: Dicaearchus, Strato, Herophilus, Alcmaeon (Dowel "Alcmaeon"), Hippo, Cleophanes, Diocles, Erasistratus, Asclepiades, Polybus, Hippocrates, Euripides, as spelt in the source.
- Multiple holders are joined with "; " in the order the text gives them.
