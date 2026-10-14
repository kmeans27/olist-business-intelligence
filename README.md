# Olist Business Intelligence

**A reproducible business-analysis study over the public Olist Brazilian
e-commerce dataset: SQL case study, persona-first operations dashboard, and a
marketing-funnel decision memo with confidence-interval inference.**

Language: Python 3.14, managed with [uv](https://github.com/astral-sh/uv). No notebooks; every artifact is produced by a committed script and checked by tests.

---

## 1. Abstract

We study three decision-relevant questions over Olist's public marketplace
data — (i) where revenue and delivery risk concentrate (SQL case study, five
non-trivial queries), (ii) what a regional operations manager should act on
(persona-first Streamlit dashboard), and (iii) which marketing-funnel sources
should be grown or pruned (decision memo using Wilson score intervals and
minimum-detectable-effect sizing). All headline numbers are regenerated on
open; the test suite recomputes every SQL result in pandas and asserts the
published CSVs match, so the reports are CI-guarded rather than hand-copied.

## 2. Data and provenance

| Item | Value |
|---|---|
| Primary datasets | *Brazilian E-Commerce Public Dataset by Olist* (99,441 orders) and *Marketing Funnel by Olist* (8,000 leads, 1,000 closed deals) |
| Source used | Public GitHub mirrors: `MarthaMueni/Marketing-Funnel-Olist` (10 files), `Kaushal00Vaid/OLIST-Brazilian-Ecommerce-Analysis` (reviews) — no Kaggle API key required |
| Validation | Row counts match the official Kaggle release for every file |
| Period | Orders 2016-09-29 → 2018-09-29 (harvest date) |
| Excluded | Geolocation file (≈1M rows): not required by any analysis in this repo |

## 3. Definitions and measurement basis

These choices are the study's *operational definitions*; all are encoded in
`src/olist_bi/` and re-checked by `tests/test_golden.py`.

- **Revenue basis.** Revenue is summed over `order_items` (`price +
  freight_value`) restricted to orders with a non-empty
  `order_delivered_customer_date`. We deliberately do **not** filter on the
  `order_status` string: the mirror re-encodes `completed` as `delivered`, so
  the delivery-date predicate is the robust one.
- **Person identity.** `customer_id` is an alias per order, not a person. All
  person-level analysis joins through `customer_unique_id`. This is asserted
  in the test suite (`test_q5_repeat_rate_uses_real_person_ids`).
- **Cohort repeat rate.** A *cohort* is a person's first delivered order month;
  a person *repeats* if they have a second delivered order later. Rates are
  reported per cohort month, never as a single average.
- **Delivery risk.** Per state, the p90 of delivered-days
  (`julianday(delivered) − julianday(purchase)`), defined as the
  ⌈0.9·n⌉-th order statistic (no interpolation); `n` is always shown so
  small-sample states are visible.
- **Conversion inference.** For funnel segments we use the **Wilson score
  interval** (p̂ ± z·√(p̂(1−p̂)/n + z²/4n²)/(1 + z²/n), z = 1.96) rather than
  the normal approximation: it is well-defined near 0/1 and at small n. A
  segment is *significantly above/below baseline* iff its interval excludes
  the overall baseline rate. **Uplift** = segment rate − baseline.
  **MDE sizing** (80% power, α = 0.05) reports the n required to detect a
  +5pp lift; segments below that n are described as *not detectable*, not as
  *no effect*.

## 4. Data cleaning (every lossy decision documented)

| Decision | Rationale | Effect |
|---|---|---|
| Drop rows with empty `order_status` | unclassifiable records | 2 rows |
| Normalise both Olist date formats to sortable ISO | mixed `2016-09-05 21:01:15` and `...T...Z` forms ship side-by-side | none (formatting only) |
| Keep NULL `product_category` as `(not mapped)` | dropping would silently erase ≈3% of revenue from category mix | visible residual row |
| Mirror column renames (`customer_unique_id`, `mql_id`, `price`) | schemas verified against file headers before coding (`head -1` of each CSV) | — |

## 5. Results (regenerated on open; full tables in `reports/`)

**SQL case study**

1. **Category revenue.** Top category `health_beauty` R$1.41M (9.2% of all
   revenue), then `watches_gifts` (8.2%), `bed_bath_table` (7.9%),
   `sports_leisure` (7.3%), `computers_accessories` (6.7%); top-5 ≈ 39%.
2. **Seller league.** 2,970 sellers produced delivered revenue; **551 (18.6%)
   account for 80% of it**; the single largest carries 1.6%. Revenue is
   broadly distributed across the marketplace — no single-vendor story.
3. **Delivery risk by state.** Worst p90s: `RR` 53 days (n=41), `AL` 40
   (n=397), `AM`/`PA` 39; best: `SP` 15 days (n=40,495). Low-n states rank
   high on rate; `n` is published in the table (see §6).
4. **Monthly revenue growth.** Steady +30–100% MoM through 2017; **2016-12 is
   a data artifact** (R$19.62 ≈ 2 orders — the month is essentially absent) and
   2018-08 (−4.1%) is the **harvest-truncation edge**. Both are flagged in an
   output column, not smoothed away.
5. **Cohort repeat rate** (person-level): early cohorts show 4.5–5.3% of
   first-time buyers returning within the window; the rate decays for later
   cohorts because the observation window shrinks — an honest measurement
   artifact, reported per cohort rather than averaged.

**Marketing-funnel decision memo** (Wilson 95%; overall baseline 10.53%)

| Source | n | rate | CI (95%) | verdict |
|---|---|---|---|---|
| PAID_SEARCH | 1,586 | 12.30% | 10.8–14.0 | +1.8pp; lower bound just clears baseline — directionally supported, small |
| ORGANIC_SEARCH | 2,296 | 11.80% | 10.5–13.2 | indistinguishable from baseline |
| UNKNOWN | 1,159 | 16.65% | 14.6–18.9 | highest, but unattributed — not an actionable lever |
| SOCIAL | 1,350 | 5.56% | 4.5–6.9 | **significantly below baseline** |
| EMAIL | 493 | 3.04% | 1.9–5.0 | **significantly below baseline** |
| OTHER | 150 | 2.67% | 1.0–6.7 | below baseline; n < MDE (1,667) — not detectable |

**Decision:** no actionable source clears a +5pp uplift target (MDE n ≈ 1,667
per segment); the well-supported action is **pruning EMAIL/SOCIAL/DISPLAY/OTHER
sources**, not "improving the funnel overall". Won-deal composition
(`home_decor` 105, `health_beauty` 93, `car_accessories` 77 top the list)
aligns conversion targets with the top revenue categories of (1).

**Operations dashboard** (`dashboard/app.py`): persona-first — the operator
selects their destination state; KPI strip (delivered orders, revenue, exact
p90) → monthly revenue trend → risk league across all states with an explicit
AT RISK verdict column → category mix. One accent color; risk is conveyed by
ordering + verdict, not a rainbow.

## 6. Limitations (threats to validity)

- **Harvest artifacts:** the 2016-12 gap and 2018-08 truncation are properties
  of the public file, not of the marketplace; they are flagged, not hidden.
- **Small-n percentiles:** states with n < 100 (e.g. `RR`, `AP`) have unstable
  p90s; `n` is published with every figure and the dashboard keeps it visible.
- **Funnel join:** 842 of 1,000 closed deals match the 8,000-lead sample
  (the public files are samples of the same population); rates are computed on
  matched leads only.
- **Date precision:** day-level `julianday` differences (no intra-day term).
- **Observation-window decay:** cohort repeat rates and MoM growth are
  window-length dependent; all are reported per cohort/edge with the caveat.

## 7. Reproduction

```bash
uv run scripts/fetch_data.py          # 10 CSVs -> data/raw -> data/raw_clean
uv run scripts/build_db.py            # cleaned CSVs -> SQLite (data/olist.sqlite)
uv run scripts/run_queries.py         # sql/*.sql -> reports/sql_results/*.csv
uv run scripts/make_decision_memo.py  # segment tables -> reports/decision_memo_data/
uv run pytest                         # 6 golden checks (SQL outputs vs independent pandas recomputation)
uv run ruff check src tests scripts dashboard && uv run ruff format --check src tests scripts dashboard
uv run streamlit run dashboard/app.py # persona dashboard
```

Status at publication: `pytest` 6/6 passed; `ruff check` and `ruff format --check` clean; dashboard smoke-runs with exit 0.

## 8. Repository layout

```
sql/                      five queries (joins, window functions, percentiles, cohorts)
reports/sql_results/      CSV outputs of the queries (regenerated, not hand-edited)
reports/decision_memo_data/  segment tables with Wilson intervals + MDE
dashboard/app.py          Streamlit persona dashboard (Altair, single accent)
src/olist_bi/             library: fetch+clean, SQLite schema, Wilson/uplift/MDE math
tests/test_golden.py      golden checks: pandas recomputation must match SQL outputs
scripts/                  pipeline runners
data/                     raw + cleaned CSVs and the SQLite DB (gitignored)
```

## 9. References

- Olist. *Brazilian E-Commerce Public Dataset by Olist* (Kaggle, 2018) — 99,441 orders, 2016-09 → 2018-09.
- Olist. *Marketing Funnel by Olist* (Kaggle, 2019) — 8,000 leads, 1,000 closed deals.
- Wilson score interval: Wilson, E.B. (1919). *Probable Proportions and a Method of Determining Probable Confidence of a Given Trial Outcome from a Known Sample Population*. With corrections for continuity.
- Method: Wilson score interval (z = 1.96) chosen over the normal approximation for robustness near p̂ ∈ {0,1} and small n.

## License

Analysis code: this repository. Data: Olist's public dataset, released under its Kaggle terms.
