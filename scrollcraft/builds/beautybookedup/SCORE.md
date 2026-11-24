# Beauty Booked Up · grammar, gate and score

## Grammar: rhythmic cutlist

Twelve short cuts, each under 1.4vh, no pinning, no dwell above 0.1, hard cuts
between per-section grounds. The visitor feels a pulse rather than following one
long argument. That is the only grammar that fits "a lot of videos (pretty
short)" without pretending the page is a film.

Why the other seven lost:

- **Filmic one-shot** needs long pinned carries and hides its cuts. It would turn
  seven clips into a single fragile film and make the short clips long.
- **Chaptered editorial** forbids full-bleed media over type and wants fewer,
  longer, printed chapters. Wrong tempo and wrong media role.
- **Live surface** wants a real running product surface. MannyChat is a later
  build, and a painted fake dashboard is banned by that grammar.
- **Continuous world** is the most expensive and fragile option and requires one
  unbroken flight. The brief asks for separate short videos, not one geography.
- **Typographic poster** would throw away all the generated footage.
- **Gallery / catalog** would make the page a portfolio of clips rather than a
  pitch to beauticians, and its neutral labels would flatten the offer.
- **Split stage** wants one sustained before/after argument and forbids full-bleed
  openings. Six services cannot live in two columns without one becoming a
  caption for the other.

## Nav, hero and close follow from the grammar

- **Nav:** loud full-width bar, wordmark in type, one CTA label ("Book a free
  call") at the same weight as the wordmark. No logo yet.
- **Hero:** one short scrub cut, copy in a bottom band so a centre crop survives
  on a phone, headline legible within the first third of the act. Depth is built
  inside the frame by occlusion and scale, not by parallax, which this grammar
  bans.
- **Close:** abrupt full-bleed booking cut. Diary rail resolves in the fixed
  chrome. Instagram-style square frames sit around the CTA. No spotlight, no
  magnet, no drift-down, no fade to footer.

## Signature move: the diary fills as you scroll

A fixed strip at the bottom edge shows six real service slots. Each service cut
stamps one slot with its real service name. It is clickable: selecting a filled
slot jumps to that service's cut. From act 14 it holds, complete, in front of the
close. `data-sc-verify-state` on the strip publishes the rendered slot state so
the harness grades the bespoke chrome instead of skipping it.

## Fingerprint gate (workspace registry, one existing row)

The only existing row is **Aurum Listening Bar**: chaptered editorial, margin
folio chrome, typographic title-page hero, flow-only short chapters (~7.8vh),
colophon close, scroll-velocity equalizer + groove trace.

| Dimension | This build vs Aurum |
|---|---|
| Grammar | Rhythmic cutlist vs chaptered editorial (different) |
| Nav treatment | Loud full-width bar with equal-weight CTA vs margin folio (different) |
| Hero device | One short scrub cut with bottom-band copy vs typographic title page (different) |
| Act-sequence shape | 16 cuts, one scrub, ~13vh, no pins vs 11 long flow chapters, ~7.8vh (different) |
| Close pattern | Abrupt full-bleed CTA with resolved diary rail vs quiet colophon (different) |
| Signature move | Diary filling rail vs velocity equalizer + groove trace (different) |

**Result: 6 of 6 dimensions differ.** Gate passes.

## Score (device per beat)

Four device families, no family twice in a row, one scrub only, no pins.

| Beat | Act | Device | Why this one |
|---|---|---|---|
| Recognition | 1 | `scrub` (1.2vh, dwell 0.05) | The one clip the visitor scrubs with the wheel; opens the page |
| Interruption | 2 | `flow` + `in` | A hard cut lands faster than any dissolve |
| Fatigue | 3 | `flow` + `in` on ink | The ground itself changes state, no wipe needed |
| Change | 4 | `flow` + `reveal` (iris) | One iris on the page, the diary appears |
| Substance | 5 | `flow` + `in` | Six real services, plain labels |
| Clarity | 6 | `flow` + `in` | Four promises, no decoration |
| Calm | 7 | `flow` + `reveal` (left) | Macro nails, one wipe, soft light |
| Confidence | 8 | `flow` + `reveal` (up) | One still, one claim, no motion competing |
| Appetite | 9 | `flow` + `in`, one `kinetic` heading | Words arrive at speed once, then cut on |
| Inclusion | 10 | `flow` + `reveal` (up) | A change of state earned by the subject |
| Relief | 11 | `flow` + `reveal` (left) | The inbox cut, quiet and plain |
| Weight | 12 | `flow` + `in` | Plans as real lists, no cards |
| Reassurance | 13 | `flow` + `in` | FAQs as an operable accordion |
| Intent | 14 | `flow` + `in` | A real form with a real mailto action |
| Stillness | 15 | `flow` (authored silence) | Three still frames, no stamp, no kinetic |
| Resolve | 16 | `flow` + `in`, full-bleed CTA | The page stops cutting and asks for the call |

Four device families: `scrub`, `flow` + `in`, `reveal`, `kinetic`. No `pin`,
no `pan`, no `spotlight`, no `magnet`, no `parallax`, no `count`.

Grounds are painted per section, not drifted: several short acts are part-way
through at once, so a single drifting ground would arrive a section late. No
statistics, so no `count` device. Pointer devices are excluded by the grammar.

## Theme tokens

High-key editorial, ink on warm white, one raspberry accent that owns the CTA
and the filled diary slots. No cream-and-brass, no violet gradient.

```
--sc-canvas #F8F5F1   --sc-surface #EFEAE4
--sc-ink #1A1417      --sc-ink-soft #5D5256
--sc-accent #C4325B   --sc-accent-ink #FFFFFF
--sc-font-display Archivo   --sc-font-text Geist
```

Type over media uses ink, not white. Scrims wash toward the canvas (density up,
not down) because the ground is light.
