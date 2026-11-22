"""Kind `slo`: SLO / error budget / burn-rate / capacity math returned as JSON, graded numerically."""
import json
import math
import random

TOL_REL = 0.005
TOL_ABS = 1e-6
PERIOD_H = 720.0  # 30 days


def _fin(prompt, fields, expected):
    keys = ", ".join(f'"{k}"' for k in fields)
    return (prompt + f"\n\nReturn exactly one JSON object with the keys {keys} and nothing else. Give plain numbers (booleans as true/false), "
            f"no units or strings. Values within {TOL_REL * 100:.1f}% relative error are accepted; integer-valued fields must be exact."), expected


def s_budget(rng):
    slo = rng.choice([99.0, 99.5, 99.9, 99.95, 99.99])
    days = rng.choice([7, 28, 30])
    total = rng.randint(2, 90) * 10 ** rng.choice([6, 7, 8])
    f = 1 - slo / 100
    p = (f"A service has an availability SLO of {slo}% measured over a rolling {days}-day window. It served {total} requests in that window; "
         f"requests are 'bad' when they fail. Compute the error budget.\n"
         f"- error_budget_fraction: allowed fraction of bad requests\n- allowed_downtime_minutes: full-outage minutes the window allows\n- allowed_bad_requests: bad requests allowed in the window (integer, round to nearest)")
    exp = dict(error_budget_fraction=f, allowed_downtime_minutes=days * 1440 * f, allowed_bad_requests=round(total * f))
    return _fin(p, list(exp), exp)


def s_burn(rng):
    slo = rng.choice([99.0, 99.5, 99.9, 99.95])
    e = rng.choice([0.5, 0.8, 1.2, 2.0, 3.5, 6.0]) * (1 - slo / 100) / 0.001 * 0.1
    e = round(e, 4)
    h = rng.choice([1, 2, 6])
    burn = e / 100 / (1 - slo / 100)
    p = (f"SLO: {slo}% availability over 30 days (720 hours). For the last {h} hour(s) the observed error rate is {e}% of requests. Assume the budget was untouched before.\n"
         f"- burn_rate: error rate divided by the allowed error rate\n- hours_to_exhaust_budget: hours until the whole 30-day budget is gone if this error rate continues\n"
         f"- budget_consumed_pct: percent of the 30-day budget consumed during those {h} hour(s)")
    exp = dict(burn_rate=burn, hours_to_exhaust_budget=PERIOD_H / burn, budget_consumed_pct=burn * h / PERIOD_H * 100)
    return _fin(p, list(exp), exp)


def s_burn2(rng):
    slo = rng.choice([99.9, 99.95, 99.5])
    bud = 1 - slo / 100
    for _ in range(100):
        e1 = round(bud * rng.uniform(6, 30) * 100, 3)
        e5 = round(bud * rng.uniform(4, 40) * 100, 3)
        b1, b5 = e1 / 100 / bud, e5 / 100 / bud
        if abs(b1 / 14.4 - 1) > 0.04 and abs(b5 / 14.4 - 1) > 0.04:
            break
    p = (f"SLO {slo}% over 30 days. Multi-window alerting policy: page when BOTH the 1h burn rate and the 5m burn rate are >= 14.4. "
         f"Current observed error rates: {e1}% over the last 1h, {e5}% over the last 5m.\n"
         f"- burn_1h, burn_5m: burn rates\n- page: true if the policy pages\n- hours_to_exhaust_at_5m_rate: hours to exhaust a full 30-day budget at the 5m burn rate")
    exp = dict(burn_1h=b1, burn_5m=b5, page=bool(b1 >= 14.4 and b5 >= 14.4), hours_to_exhaust_at_5m_rate=PERIOD_H / b5)
    return _fin(p, list(exp), exp)


def s_thresholds(rng):
    slo = rng.choice([99.0, 99.5, 99.9, 99.95])
    bud = 1 - slo / 100
    pol = rng.choice([((2, 1), (5, 6)), ((2, 1), (10, 72)), ((5, 6), (10, 72)), ((1, 1), (5, 6))])
    (pf, hf), (ps, hs) = pol
    p = (f"SLO {slo}% availability over 30 days (720h). Design two burn-rate alerts. 'fast': fire when {pf}% of the whole error budget is consumed within {hf} hour(s). "
         f"'slow': fire when {ps}% of the budget is consumed within {hs} hour(s). Each alert uses a short confirmation window equal to 1/12 of its long window.\n"
         f"- fast_burn_threshold / slow_burn_threshold: burn-rate multiple at which the alert fires\n"
         f"- fast_error_rate_pct / slow_error_rate_pct: the equivalent error-rate threshold in percent of requests\n"
         f"- fast_short_window_min / slow_short_window_min: short window length in minutes")
    bf, bs = pf / 100 * PERIOD_H / hf, ps / 100 * PERIOD_H / hs
    exp = dict(fast_burn_threshold=bf, slow_burn_threshold=bs, fast_error_rate_pct=bf * bud * 100, slow_error_rate_pct=bs * bud * 100,
               fast_short_window_min=hf * 60 / 12, slow_short_window_min=hs * 60 / 12)
    return _fin(p, list(exp), exp)


def s_avail(rng):
    names = ["load balancer", "app tier", "database", "message queue"]
    chosen = rng.sample(names, rng.choice([3, 4]))
    desc, A = [], 1.0
    for n in chosen:
        a = rng.choice([0.99, 0.995, 0.999, 0.9995, 0.9999])
        k = 1 if n in ("load balancer", "message queue") else rng.choice([2, 3])
        if k == 1:
            desc.append(f"- {n}: a single instance, availability {a}")
        else:
            desc.append(f"- {n}: {k} independent redundant instances (up if at least one is up), each availability {a}")
        A *= 1 - (1 - a) ** k
    p = ("A request needs every component below to be up (series); redundant instances fail independently.\n" + "\n".join(desc) +
         "\n- composite_availability: availability of the whole system (fraction)\n- downtime_minutes_per_year: expected downtime per 365-day year in minutes\n"
         "- nines: -log10(1 - composite_availability)")
    exp = dict(composite_availability=A, downtime_minutes_per_year=(1 - A) * 525600, nines=-math.log10(1 - A))
    return _fin(p, list(exp), exp)


def s_policy(rng):
    slo = rng.choice([99.9, 99.95, 99.5])
    days = 30
    budget = days * 1440 * (1 - slo / 100)
    inc = [(rng.randint(3, 40), rng.choice([100, 50, 25, 10, 5])) for _ in range(rng.randint(2, 4))]
    thr = rng.choice([10, 20, 25, 30])
    consumed = sum(d * i / 100 for d, i in inc)
    rem = (budget - consumed) / budget * 100
    if abs(rem - thr) < 2:
        inc.append((9, 100))
        consumed = sum(d * i / 100 for d, i in inc)
        rem = (budget - consumed) / budget * 100
    lst = "; ".join(f"{d} min with {i}% of requests failing" for d, i in inc)
    p = (f"SLO {slo}% over a 30-day window. Incidents so far this window: {lst}. An incident's budget cost is duration x failing fraction (full-outage-equivalent minutes). "
         f"Policy: freeze feature deploys when the remaining budget is below {thr}% of the total budget.\n"
         f"- budget_minutes_total: total budget in full-outage-equivalent minutes\n- consumed_minutes: minutes consumed so far\n- remaining_pct: remaining budget as percent of total (negative if overspent)\n"
         f"- freeze_deploys: true if deploys are frozen now\n- extra_outage_minutes_before_freeze: additional full-outage minutes that can still happen before the freeze triggers (0 if already frozen)")
    exp = dict(budget_minutes_total=budget, consumed_minutes=consumed, remaining_pct=rem, freeze_deploys=bool(rem < thr),
               extra_outage_minutes_before_freeze=max(0.0, (budget - consumed) - thr / 100 * budget))
    return _fin(p, list(exp), exp)


def s_capacity(rng):
    for _ in range(200):
        cap = rng.choice([200, 250, 400, 500, 800])
        util = rng.choice([0.5, 0.6, 0.65, 0.7])
        peak = rng.randint(2000, 12000)
        spare = rng.choice([1, 2])
        g = rng.choice([4, 6, 8, 10, 12])
        m = rng.choice([6, 9, 12])
        lat = rng.choice([40, 80, 120, 250])
        x1 = peak / (cap * util)
        x2 = peak * (1 + g / 100) ** m / (cap * util)
        if min(x1 % 1, x2 % 1) > 0.03 and max(x1 % 1, x2 % 1) < 0.97:
            break
    F = math.ceil(x1) + spare + rng.randint(1, 4)
    p = (f"A stateless service peaks at {peak} requests/s. One instance handles {cap} requests/s at 100% utilization, but you size for a target utilization of {int(util * 100)}%. "
         f"Keep {spare} extra instance(s) of N+{spare} redundancy on top of the sized fleet. Traffic grows {g}% per month, compounding. Mean request latency is {lat} ms. The fleet currently has {F} instances in total.\n"
         f"- instances_needed_now: total instances needed now (sized fleet rounded up, plus spares)\n- instances_needed_in_{m}_months: same after {m} months of growth\n"
         f"- months_until_current_fleet_exhausted: months (fractional) until peak traffic needs more than the {F - spare} non-spare instances at target utilization\n"
         f"- inflight_requests_at_peak: mean concurrent in-flight requests at peak (Little's law)")
    exp = {"instances_needed_now": math.ceil(x1) + spare, f"instances_needed_in_{m}_months": math.ceil(x2) + spare,
           "months_until_current_fleet_exhausted": math.log((F - spare) * cap * util / peak) / math.log(1 + g / 100),
           "inflight_requests_at_peak": peak * lat / 1000}
    return _fin(p, list(exp), exp)


def s_hist(rng):
    les = [0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
    for _ in range(500):
        total = rng.randint(50, 900) * 1000
        w = [rng.uniform(0.5, 6) for _ in les] + [rng.uniform(0.01, 0.3)]
        s = sum(w)
        counts = [int(total * x / s) for x in w]
        cum, c = [], 0
        for x in counts:
            c += x
            cum.append(c)
        total = cum[-1]
        thr_i = rng.choice([2, 3])
        target = rng.choice([90.0, 95.0, 99.0])
        good = cum[thr_i] / total
        rank = 0.99 * total
        bi = next(i for i, v in enumerate(cum) if v >= rank)
        if bi < len(les) and abs(good - target / 100) > 0.004:
            break
    lo = les[bi - 1] if bi else 0.0
    prev = cum[bi - 1] if bi else 0
    p99 = lo + (les[bi] - lo) * (rank - prev) / (cum[bi] - prev)
    lines = "\n".join(f'latency_bucket{{le="{le}"}} {v}' for le, v in zip(les, cum)) + f'\nlatency_bucket{{le="+Inf"}} {total}'
    p = (f"A Prometheus-style cumulative histogram of request latency in seconds over the SLO window:\n{lines}\n\n"
         f"SLO: {target}% of requests must complete within {les[thr_i]}s.\n- good_fraction: fraction of requests at or below {les[thr_i]}s (use the bucket boundary)\n"
         f"- meets_slo: true if good_fraction >= {target / 100}\n- p99_seconds: the 99th percentile estimated like Prometheus histogram_quantile (linear interpolation inside the bucket containing rank 0.99*total, lower bound of the first bucket is 0)")
    exp = dict(good_fraction=good, meets_slo=bool(good >= target / 100), p99_seconds=p99)
    return _fin(p, list(exp), exp)


BUILDERS = {"budget": s_budget, "burn": s_burn, "burn2": s_burn2, "thresholds": s_thresholds, "avail": s_avail,
            "policy": s_policy, "capacity": s_capacity, "hist": s_hist}


def make_slo(seed, kind):
    rng = random.Random(seed)
    prompt, exp = BUILDERS[kind](rng)
    exp = {k: (round(v, 8) if isinstance(v, float) else v) for k, v in exp.items()}
    return dict(inputs=dict(prompt="You are an SRE doing reliability math.\n\n" + prompt),
                hidden=dict(expected=exp, tol_rel=TOL_REL, tol_abs=TOL_ABS, subtype=kind),
                reference_answer=json.dumps(exp))
