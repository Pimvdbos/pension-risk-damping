# Methodology and model boundaries

Pim van den Bos, University of Twente, *Management Control for Financial
Institutions*, Assignment D, 3 July 2026. The [report](../reports/Management_Control_Assignment.pdf)
is the research source of truth; Appendix A resolves implementation details where its
narrative is less precise. The supplied findings and reconstructed code are now
accompanied by a [full-data numerical replication and engineering audit](replication_audit.md).
Numerical reproduction is distinguished from validation of the economic assumptions.

## Research question and scope

Which damping mechanisms in the *solidaire premieregeling* (SPR) under the Dutch
*Wet toekomst pensioenen* (Wtp) reduce volatility in pension outcomes, and how much
does each contribute individually and jointly? Within the report's SPR context,
collective investment returns are allocated to participants using predetermined rules.
The simulation isolates four illustrative financial dampers in one participant's account.
It does not implement a complete pension fund or all statutory SPR rules.

DNB generated the economic scenarios. The study reconstructs yield curves from the
provided states and parameters and simulates pension outcomes; it does **not** calibrate
the DNB scenario generator. The exact input is the unshocked CP2022 **P**, **20K**,
**2026Q2** set: 20,000 annual scenarios spanning 100 return years. See
[data acquisition](data_provenance.md) for workbook layout, time indexing and rights.

## Contract and cohort timing

| Choice | Appendix implementation |
| --- | --- |
| Entry / retirement / end age | 25 / 68 / 95 |
| Contributions | Flat nominal 1.0 per accumulation year, added **before** the return |
| Conversion | Capital divided by `sum((1.03)**(-j) for j in range(1,28))` |
| Payout | 27 benefit columns; initial converted benefit followed by 26 updates |
| Cohorts today | 25, 35, 45, 55, 67 |
| Older-cohort history | Since age 25, `(capital + 1) * 1.03` each historical year; only future exposure is stochastic |
| Baseline | 100% equity, full benefit pass-through, no damping |

A.10's `run` starts with **zero** capital at its chosen entry age. A.11's `run_grid`
seeds a current-age cohort with the deterministic capital above. Both are retained.
The default settings give 43 accumulation years for the age-25 entrant.

For current age `a`, `acc = 68-a`; future accumulation uses return columns
`t=0,...,acc-1`. First payout is `capital / annuity_factor` and does not receive an
extra return update. Payout update `k=1,...,26` uses `t=acc+k-1`, and allocation age
`68+k-1`. Benefits are deflated by
`cumprod(1+infl_nl, axis=1)[:, acc+arange(27)-1]`. Thus an age-25 entrant's first
payout uses price index 42 and final payout price index 68. These are the printed
appendix indices, not a newly chosen alternative timing convention.

## Four financial mechanisms

1. **Protection return (*beschermingsrendement*).** Hedge share
   `h = clip((age-45)/(68-45),0,1)`. Liability-duration proxy
   `max(max(95-age,1)/2,1)`, converted to maturity with Python's
   `int(round(duration))` (including ties-to-even). Nominal zero-coupon discount
   factor `P(t,d)=(1+y(t,d))**(-d)`; holding return
   `P(t+1,d-1)/P(t,d)-1`. A zero remaining maturity pays one. The single-bond proxy
   does not match an entire liability cash-flow curve.
2. **Lifecycle (*leeftijdsafhankelijke toedeling van het overrendement*).**
   `w = clip(1-0.8*(age-35)/(95-35),0.2,1)`: full exposure until age 35,
   56% at retirement and 20% at age 95. Residual exposure earns the reconstructed
   one-year **nominal** risk-free rate. Inactive lifecycle sets `w=1`.
3. **Spreading (*spreidingsmechanisme*).** Only during payout, split each raw shock
   into five equal interest-free slices. Write `shock/5` into slot `k % 5` of a
   five-column ring buffer and sum the active slots. The current shock contributes
   **immediately**, remains active for five updates, and is overwritten five updates
   later. Nothing is flushed beyond the fixed payout horizon.
4. **Reserve (*solidariteitsreserve* proxy).** Initially empty participant-level
   buffer, only during payout. Target the previous nominal benefit. Cover shortfall
   up to available funds, then skim 25% of positive surplus with available room
   `max(2*previous_benefit - remaining_reserve,0)`. Funds earn no modeled return.
   The cap limits filling; a lower subsequent target does not forcibly release an
   existing balance. This is a reduced-form own buffer, not a shared reserve of
   several generations. It cannot quantify actual intergenerational transfers.

The combined allocation is

```text
allocated = h*protection + (1-h)*(w*equity + (1-w)*risk_free)
```

Inactive protection sets `h=0`. Each payout update follows a fixed order:
allocation → raw shock `(1+allocated)/(1+projection)-1` → spreading → reserve.
The reserve therefore operates on the remaining movement after spreading.
The benefit is updated multiplicatively by `1+applied_shock`. Contributions,
initial capital and benefits use arbitrary contribution-normalized nominal units.

## Two risk metrics, two questions

Given real benefits `B[scenario, payout_year]`, with NumPy population standard
deviations (`ddof=0`):

```python
level_cov = median(std(B, axis=0) / mean(B, axis=0))
changes = diff(B, axis=1) / B[:, :-1]
yoy_volatility = median(std(changes, axis=1))
```

Level dispersion measures cross-scenario uncertainty in the pension level: compute
a CoV across scenarios **for each payout year**, then the median over years.
YoY volatility measures changes in a scenario's real retirement payments: take the
standard deviation over its 26 relative annual changes, then the median across
scenarios. They measure different risks and use different axes of aggregation.

The appendix's mean, standard deviation and percentile descriptives aggregate the
**entire real-benefit array**. `Std/Mean` need not equal `level_cov`. The supplied
findings describe YoY volatility as broadly similar across cohorts, with minor
variation; the implementation computes it separately and never forces equality.

## Factorial experiments, interactions and attribution

The four switches define all **16 coalitions**, including the undamped baseline and
the full model. For either risk metric `rho`, the value of a coalition is
`v(S)=rho(baseline)-rho(S)`. A mechanism's Shapley value averages its marginal risk
reduction over every possible ordering of coalition additions, using the equivalent
factorial coalition weights. Values sum to the full-model reduction (efficiency).
Percentage shares divide each contribution by that combined reduction.

Shapley removes dependence on the **order of attribution/addition**. It does not
remove dependence on the simulator's fixed **within-year operation order**. The
sequential A.13 table is retained to show a particular addition path. The maintained
package computes each cohort/coalition summary once for both metrics and all tables.

The supplied results show substitution between protection and lifecycle: both reduce
exposure to shocks, so their standalone reductions cannot be added. Spreading smooths
the remaining payout movement, giving it the largest age-45 Shapley share for YoY
stability even though its standalone effect on level dispersion is small. Reported
age-45 level shares are 57.2% protection and 34.2% lifecycle; spreading's YoY share is
37.9%. These are shares of combined reductions, not standalone percentage reductions.
Rounded totals are preserved.

Stability also changes expected benefits. In report Table 1, age-45 mean real benefit
falls from 8.2928 in the all-equity baseline to 2.9729 with standalone protection and
4.0731 with standalone lifecycle; reserve gives 7.5637 and spreading 8.5565. Thus
the reported trade-off concerns specific allocation/buffering choices, not a claim
that every damper uniformly lowers the mean. See the [four transcribed tables](../results/reported/README.md).

## Separate illustrative extensions

A.8 retains projection returns **2.5%, 3%, 4%**, applied to both conversion and
annual benefit updates. This explores level and drift. A.9 retains
`q(age)=clip(0.005*2**((age-65)/9),0,1)`, deterministic cohort survival, a
survival-weighted annuity and per-survivor payout scaling `1/(1-q)`, exactly as
listed. It is an illustrative mortality function, not an AG prognosetafel. Neither
extension participates in the four-player decomposition. No mortality is added to
the main engine.

## Interpretation limits

This academic simulation uses a stylized 100%-equity baseline, illustrative hedge
and lifecycle rules, fixed nominal contributions, survival to a fixed age 95 in the
main model, a single-bond hedge, an own-buffer reserve, one scenario vintage and
a fixed operation order. It cannot measure transfers between generations or establish
a particular fund's policy effects. The report discusses a fuller multi-cohort shared
reserve as future work. This repository adds no such research feature and makes no
production-calculator or official-DNB-implementation claim.
