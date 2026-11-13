# w2-04: Modern, miss and reverse cases (R01-R12)

Table: `data/cases_modern_reverse.csv` (12 rows), built by `python -I build.py <out.csv>`, exit 0. The script lives outside the tree in `%TEMP%\w2-04-scripts\`. Primary texts are saved in `data/raw/w2-04/`. Line and page locators below come from those files.

**How the confirm events were chosen.** Each confirm event was picked before its gap was computed. Where the brief offered alternatives:
- R02 and R03 use Hubble 1929, the observation of expansion, rather than Lemaitre 1927, which was theory.
- R06 and R07 use Perrin's May 1908 Comptes rendus notes, not the 1909 memoir. Ostwald's recantation preface is signed November 1908, so the event that refuted him has to come before it.
- R08 uses Gravity Probe B 2011 rather than the theory (GR 1915).
- R09 uses Hensen 2015 rather than Aspect 1982.

**"verified" column.** It means I, or a verification subagent working on files saved in raw/w2-04, opened the primary passage. Any exceptions are stated per case.

## R01 Poe, Eureka (1848): dark night sky vs Kelvin 1901. PARTIAL

**Text.** Gutenberg 32037, lines 2618-2634. Poe says an endless succession of stars would give the sky a uniform glow. The dark gaps seen in telescopes could then be explained only if the background were so far away that no ray from it has yet reached us. He grants that this may be so, but says there is not "the shadow of a reason" to believe it. He then argues that the Universe of Stars is limited.

**Answer to the brief's question.** Poe raised the finite light-travel option and set it aside. He did not assert it. Two things in the same passage are wrong:
- He treats the gaps as windows onto an empty "Universe of Vacancy" (lines 2639-2645).
- He takes the star system to be bounded.

**Kelvin.** Phil. Mag. ser. 6, 2:161-177 (Aug 1901), secs. 18-19, pp. 175-176. He computes that stellar discs cover only a tiny fraction of the sky. To make discs cover even 4% of the sky, the stars would have to extend so far that their light needs about 3.3 million stellar lifetimes to reach us; he grants each star a 100-million-year life. So the whole sky can never glow at once. This combines a finite light-travel time with finite stellar lifetimes.

**Grade: PARTIAL.** The mechanism Poe named is the right one: light from far enough away has not arrived yet. But it was one option, and he rejected it. He also gives no finite age and no stellar-lifetime budget.
- Counter, towards LOOSE: a claim the author disbelieves fails the "asserted" test outright.
- Counter, towards higher: Harrison (Darkness at Night, 1987) credits Poe with the qualitative idea. That attribution is relayed from wave 1; I have not read the book.

**Causal line.** None. Kelvin cites neither Poe nor Olbers.

**Source caveat.** The Kelvin text in raw/ is a Taylor & Francis download (DOI 10.1080/14786440109462676) and may sit behind a paywall. A free reprint reportedly appears in Kelvin's Baltimore Lectures (1904); I have not opened it.

## R02 Poe's primordial Particle vs Hubble 1929. LOOSE

**Text.** Gutenberg 32037, lines 725-745. God wills one primordial Particle into being. It is irradiated spherically into "previously vacant space" as a finite number of atoms, and gravitation is their tendency to return to Unity. Two further passages bear on his present-day universe:
- Line 1283 frames the hypothesis as matter that was irradiated from a centre "and is now returning to it".
- Lines 3398-3400 say "progressive collapse" is the only state in which we may consider all things.

So Poe's present universe is contracting, which is the opposite of Hubble's recession.

**Confirm event.** Hubble, PNAS 15(3):168-173 (15 Mar 1929); Crossref record checked.

**Grade: LOOSE.** What matches is a single origin and an outward spread. That outward spread is matter moving through existing space, not space expanding, and his present-day sign is wrong.
- Counter: the beginning from one point is specific and could have been wrong.
- My reply: a single origin was also standard creation theology. The preface asks that the work be judged "as a Poem" (line 82).

## R03 Grosseteste, De luce (c. 1225) vs Big Bang. LOOSE

**Text.** Baur, BGPM 9 (1912), pp. 51-59, archive.org ldpd_7395671_000; the OCR was opened by a subagent.
- p. 51 ll. 10-12: a sphere of light, however large, is generated at once from a point of light.
- p. 55 ll. 27-29: nine celestial spheres are completed.
- p. 56: thirteen spheres in all, nine celestial plus four elemental.

**What is wrong in the same text.** Light propagates instantaneously, the cosmos is geocentric and made of nested spheres, and the sphere count is fixed by fiat.

**Grade: LOOSE.** The resemblance is a point-origin and an expansion. Bower et al. (Proc. R. Soc. A 2014, arXiv 1403.0769) only call it "big-bang like" and model it mathematically; they do not claim influence.
- Counter, for PARTIAL: it is a physical causal sequence (light, then expansion, then condensation), and specific enough to model.

**Causal line.** None found.

## R04 Nietzsche's 1881 notes vs Poincare 1890. PARTIAL. Philosopher first by 9 years

**Nietzsche.** eKGWB NF-1881 notebook 11 (M III 1, dated spring-autumn 1881); the whole notebook was fetched from nietzschesource.org.
- **11[202]:** the measure of total force is fixed, "nichts Unendliches". So the number of states is finite, and in infinite time everything has occurred countless times.
- The same argument appears in 11[148], 11[152], 11[245], 11[269] ("sie muß sich wiederholen") and 11[305].
- 11[141] is the "Wiederkunft des Gleichen" plan dated "Anfang August 1881 in Sils-Maria". It is a plan, not the argument.
- 11[311] and 11[313] are objections he raised against the cycle.

I checked 11[202] and 11[269] in the downloaded file myself.

**Poincare.** Acta Math. 13 (1890) 1-270, ch. II §8. Stabilite a la Poisson is defined on p. 68 and Theoreme I is on p. 69, in the free scan of DOI 10.1007/BF02392508.

**Grade: PARTIAL.** The core structure matches: a conserved, bounded quantity plus unbounded time gives return. The hypotheses differ:
- Nietzsche has finite combinatorics and exact, identical recurrence of the whole world.
- Poincare has measure-preserving flow in a bounded region, and return arbitrarily close for almost all states.
- Neither applies to an expanding universe.
- Counter, towards LOOSE: this is a pigeonhole intuition. It was unpublished in his lifetime, and the published version (Gay Science 341) is an ethical test.

**Causal line.** None. The gap is 9 years, but the notes had no public effect.

## R05 Stoic ekpyrosis vs ekpyrotic model 2001. LOOSE

**Stoics.** Diogenes Laertius 7.134-142 in Hicks' translation on Wikisource.
- 7.137: God at stated periods absorbs all substance into himself and creates it again.
- 7.134 and 7.142: resolution into fire, and generation from it.

The Greek on Perseus was not checked, because Perseus refused automated access. The c. 300 BCE date is Zeno's floruit.

**KOST 2001.** Phys. Rev. D 64:123522, arXiv hep-th/0103239; checked in raw/kost2001.txt. On p. 3 the authors say the term is drawn from the Stoic model of cyclic consumption by fire. Their ref. 13 is "K. Volk and J. Katz, private communication", i.e. the name came via classicists. So the causal line is documented, but for the name only.

**Grade: LOOSE.** The shared content is cyclic destruction and renewal by "fire". Everything else differs:
- The Stoics had a divine, providential cycle with exact repetition.
- KOST has brane collision in a fifth dimension.
- The ekpyrotic model is a proposal and is unconfirmed, so the "confirm event" here is a publication, not a confirmation.

## R06 Ostwald's energetics, 1895. MISS (WRONG)

**Claim.** Die Ueberwindung des wissenschaftlichen Materialismus, lecture at Luebeck on 20 Sept 1895; Leipzig: Veit 1895; archive.org dieberwindungde00ostwgoog.
- p. 25: matter is a thought-construct.
- pp. 26-27: reality belongs only to energy, and matter is a spatial grouping of energies.

**Refutation.** Perrin's emulsion counts in Comptes rendus 146:967, May 1908. The date and volume are as cited in Perrin's own 1909 memoir (Soddy translation 1910, archive.org brownianmovement00perr). I did not open the Comptes rendus itself; Gallica is behind Cloudflare.

**Retraction.** The Vorbericht to Grundriss der allgemeinen Chemie, 4th ed. (1909), reprinted in the 5th ed. (1917), goobi.tib.eu 1778037402 image 8. I read via WebFetch the parts citing Thomson's gas-ion counts and the agreement of Brownian motion with the kinetic hypothesis. The November 1908 signature and the mention of Perrin are the subagent's reading of image 9, which I did not see. The 1909 4th edition itself was not found free online.

**Grade: WRONG.** The claim was confident, and Ostwald himself withdrew it.
- Counter: energetics as a research programme was methodological. Even so, "matter is nothing but energies" is an assertion about nature.

**Instrument.** Perrin used an ordinary high-power microscope with a water-immersion objective and a Zeiss counting cell (Soddy translation pp. 61-62), not the slit ultramicroscope. That ultramicroscope (Siedentopf & Zsigmondy, Ann. Phys. 10, issued 30 Dec 1902) was used for other colloid work.

## R07 Mach's anti-atomism, 1883. MISS (WRONG), contested

**Text.** Mechanik 1883, Kap. IV §4 art. 9, pp. 463-464; McCormack translation 1893, p. 492. Atomic theory is a mathematical model for representing facts, comparable to mathematical functions, and is not a description of reality.

**Grade: WRONG** for the claim that atoms are only a device. Mach never retracted it; I found no retraction.
- Strongest counter: this is a methodological stance about what physics should assert, not a forecast that atoms are absent. A page should say "refuted as a stance on atoms' reality", not "Mach predicted no atoms".

**Gap.** 25 years.

## R08 Mach's principle (1883) vs GR / Gravity Probe B 2011. PARTIAL

**Mach.** Mechanik 1883, Kap. II §6 art. 5, pp. 216-217; McCormack 1893, p. 232. Newton's bucket shows only rotation relative to the earth and the other celestial bodies. No one can say what would happen if the bucket's walls grew "several leagues thick".

**Causal line: documented.**
- Einstein, "Ernst Mach", Phys. Z. 17:101-104 (1916). On p. 103 he says Mach was not far from demanding a general theory of relativity, though he lacked the equivalence insight.
- Einstein, Ann. Phys. 55:241-244 (1918). p. 241 states "Machsches Prinzip": the G-field is wholly determined by the masses of bodies.

**Confirm event.** Gravity Probe B, PRL 106:221101 (2011), arXiv 1105.3456. Frame dragging measured at -37.2 ± 7.2 mas/yr.

**Grade: PARTIAL.** Rotating mass does alter local inertial frames. But GR does not fully realise Mach's principle: vacuum solutions with inertia exist, and Einstein later backed away from the principle (from wave 1, not reverified). Mach's statement is also hedged, so it cannot be STRONG.

## R09 EPR 1935, local realism. REVERSE, thesis WRONG

**Text.** Phys. Rev. 47:777-780.
- p. 777: the reality criterion (predict with certainty without disturbing the system, then an element of reality exists).
- p. 779: the locality premise (no real change in the second system).

**Decisive event: Hensen et al., Nature 526:682-686 (2015).** This was the first test to close the locality and detection loopholes together: electron spins 1.3 km apart (arXiv 1508.05949). The alternatives are Aspect 1982, a gap of 47 years, and Freedman-Clauser 1972, a gap of 37 years.

**Grade: WRONG** for local hidden variables.
- Counter: only local causality fails. Bohmian (nonlocal) and superdeterministic escapes survive, and the measurement-independence assumption cannot be closed experimentally. The page must say "local realism".

**Causal line.** Bell's 1964 paper is about the EPR paradox by title.

## R10 Leibniz, identity of indiscernibles vs Bose 1924. REVERSE, PARTIAL (contested)

**Text.** Bennett's earlymoderntexts editions.
- Discourse §9: no two substances are entirely alike.
- 4th paper to Clarke (2 June 1716) §4: the two-leaves story at Herrenhausen.
- §5: the principle named.
- §6: two indiscernibles would be one thing with two names.

**Physics.** Bose, Z. Phys. 26:178-181 (1924), doi 10.1007/BF01327326; bibliographic check only. Permutations of light quanta are not counted as distinct. Pauli, Z. Phys. 31:765-783 (1925), was also confirmed bibliographically.

**Grade: PARTIAL**, meaning the thesis survives only in a weakened form:
- Same-kind particles share all intrinsic and monadic properties, which counts against the strong principle.
- Fermions are weakly discernible by irreflexive relations (Saunders 2003; Muller & Saunders 2008, from wave 1).
- Or the particles are not individuals at all (French & Krause). In that case the principle is not refuted but loses its subject.

**Counter.** "WRONG", since Bose counting is exactly two things with no difference that are still two. SEP "Identity and Individuality in Quantum Theory" treats the question as open. Wave 1's dates have Bose in 1924, before Pauli in 1925.

## R11 Laplace, determinism (1814) vs Heisenberg 1927. MISS (WRONG for the stated form), contested

**Text.** Essai philosophique, 1st ed. (Courcier 1814), pp. 2-3. The p. 2 scan is smeared; the end of the passage is legible at the top of p. 3. The full wording was checked in the 2nd ed. (1816), pp. 3-4, in archive.org's OCR. An intellect that knew, at one instant, all forces and the respective positions of all beings would find nothing uncertain: the future and the past would be present to it.

**Refuting event.** Heisenberg, Z. Phys. 43:172-198 (1927), last paragraph on p. 197. He quotes the causal law in Laplace's form and says the premise is false, not the conclusion: the present cannot in principle be known in every determining respect. He concludes that quantum mechanics establishes the invalidity of the causal law.

**Grade: WRONG** for Laplace's claim as written: positions plus forces as the complete, knowable state. Determinism as such is not settled:
- Bohmian mechanics (1952) and Everett are deterministic.
- Heisenberg's own wording concedes that the conditional stands.

Present it as "the classical form failed; determinism remains interpretation-dependent". **Causal line: documented**, because Heisenberg addresses the thesis explicitly, though without naming Laplace.

## R12 Lemaitre 1931 and Pius XII 1951. REVERSE (physics into theology), LOOSE

**Physics.** Lemaitre, Nature 127:706 (9 May 1931), doi 10.1038/127706b0; bibliographic check only.

**Address.** Pius XII, 22 Nov 1951, "Un'ora", AAS 44 (1952) 31-43; Italian text on vatican.va, opened.
- Section "D) Il principio nel tempo" infers "creation in time, therefore a Creator".
- He casts science as witness to the primordial "Fiat lux".
- He also hedges: the facts are not an argument of absolute proof.

**Lemaitre's reaction.** From the UCLouvain archive exhibit, a secondary source:
- He was disturbed by the confusion between beginning and creation.
- The pope's 7 Sept 1952 address to the IAU dropped the primeval atom.
- At the 1958 Solvay conference Lemaitre said the hypothesis remains outside any metaphysical or religious question; the printed proceedings were not opened.

**Grade: LOOSE.** Equating the physical beginning with creation needs retrofitting; the physicist himself declined it, and the steady-state rival was live until the CMB in 1965.
- Counter: Pius hedged explicitly, so his claim was "consistent with", not "proved".

## Escalations / not done

- **Kelvin's free copy:** not opened; the DOI copy may be paywalled.
- **Diogenes Laertius:** the Greek is unchecked.
- **Not opened directly:**
  - Perrin's 1908 Comptes rendus (cited via Perrin 1909).
  - Ostwald's 1909 4th edition (read in the 1917 reprint).
  - Bose, Pauli and Lemaitre 1931 (bibliographic records only).
