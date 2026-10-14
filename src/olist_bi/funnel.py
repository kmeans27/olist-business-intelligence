#!/usr/bin/env python3
"""Marketing-funnel metrics: segment conversion, uplift vs baseline, Wilson CI.

The memo question: which lead segments should marketing spend target?
Statistical choices (justified in the memo):
- Wilson score interval at 95% for conversion rates (robust near 0/1 and small n,
  unlike the normal-approximation interval).
- Uplift = segment rate - overall baseline rate (majority-class baseline).
- Minimum detectable effect (MDE) sizing: n needed per segment to detect an
  80%-power relative uplift at alpha=0.05, two-sided.
"""

import math

from pandas import DataFrame


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z / denom * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, centre - half), min(1.0, centre + half))


def n_needed_for_mde(
    p_base: float, rel_uplift: float, alpha: float = 0.05, power: float = 0.8
) -> int:
    """Sample size to detect a relative uplift over p_base with two-sided z-tests.

    Standard normal-power formula: n = ((z_a + z_b)^2 * p(1-p)) / delta^2 with
    p under the alternative; conservative using p_base.
    """
    za = 1.96  # alpha/2 = 0.025
    zb = 0.84  # beta = 0.20
    delta = p_base * rel_uplift
    return math.ceil((za + zb) ** 2 * p_base * (1 - p_base) / delta**2)


def segment_table(leads: DataFrame, deals: DataFrame, key: str) -> DataFrame:
    """Conversion rate per segment value, with baseline, uplift, Wilson CI, MDE sizing."""
    converted = set(deals["mql_id"])
    seg = leads[key].astype(str).str.strip().str.upper().replace("", "UNKNOWN")
    ids = leads["mql_id"]
    grp = seg.to_frame().assign(converted=[i in converted for i in ids])
    g = grp.groupby(seg.name, observed=True)
    rows = []
    for name, sub in g:
        n = len(sub)
        k = int(sub["converted"].sum())
        lo, hi = wilson(k, n)
        rows.append(
            {"segment": name, "n": n, "converted": k, "rate": k / n, "ci_low": lo, "ci_high": hi}
        )
    out = DataFrame(rows).sort_values("n", ascending=False)
    total_n, total_k = len(leads), int(out["converted"].sum())
    baseline = total_k / total_n
    out["uplift_pp"] = out["rate"] - baseline
    out["mde_n"] = n_needed_for_mde(baseline, 0.2)
    out["baseline"] = baseline
    return out
