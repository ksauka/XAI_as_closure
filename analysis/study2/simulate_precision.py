"""Seeded six-profile GLMM planning; simulated data only, never study results.

Marginal logistic random-intercept likelihood, Gauss-Hermite quadrature.
Nuisance assumptions and directional effects are explicit in scenarios.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import time
from pathlib import Path

import numpy as np
import scipy
from numpy.polynomial.hermite import hermgauss
from scipy.optimize import minimize
from scipy.special import expit, logsumexp
from scipy.stats import norm

NAMES = [
    "intercept",
    "explanation",
    "delivery",
    "forcing",
    "explanation_delivery",
    "order",
] + [f"profile_{i}" for i in range(2, 7)]


def simulate(n, scenario, rng):
    if n % 8:
        raise ValueError("Planning N must be divisible by eight.")
    assignment = np.tile(np.arange(8), n // 8)
    rng.shuffle(assignment)
    e = ((assignment // 4) % 2) - 0.5
    a = ((assignment // 2) % 2) - 0.5
    f = assignment % 2 - 0.5
    order = np.array([rng.permutation(6) for _ in range(n)])
    x = np.zeros((n, 6, len(NAMES)))
    x[:, :, 0] = 1
    for col, value in [(1, e), (2, a), (3, f), (4, e * a)]:
        x[:, :, col] = value[:, None]
    x[:, :, 5] = np.arange(6)[None, :] - 2.5
    for profile in range(1, 6):
        x[:, :, 5 + profile] = order == profile
    random_intercept = rng.normal(0, scenario["random_intercept_sd"], n)
    if "profile_disagreement_probabilities" in scenario:
        profile_q = np.asarray(scenario["profile_disagreement_probabilities"], dtype=float)
        if profile_q.shape != (6,) or not np.isfinite(profile_q).all() or np.any((profile_q < 0) | (profile_q > 1)):
            raise ValueError("Provide six finite profile opportunity probabilities between zero and one.")
        q = profile_q[order]
    else:
        q = np.where(
            order < 4,
            scenario["correct_ai_disagreement_probability"],
            scenario["incorrect_ai_disagreement_probability"],
        )
    # Optional informative opportunity sensitivity, not an assumption that
    # between-subject randomisation makes later opportunities pre-treatment.
    selection = scenario.get("opportunity_random_intercept_slope", 0)
    with np.errstate(divide="ignore"):
        q = expit(np.log(q / (1 - q)) + selection * random_intercept[:, None])
    mask = rng.uniform(size=(n, 6)) < q
    beta = np.zeros(len(NAMES))
    beta[0] = np.log(
        scenario["baseline_appropriate_probability"]
        / (1 - scenario["baseline_appropriate_probability"])
    )
    beta[1] = np.log(scenario["explanation_or"])
    beta[2] = np.log(scenario["delivery_or"])
    beta[3] = np.log(scenario["forcing_or"])
    beta[4] = np.log(scenario["interaction_or"])
    beta[5] = scenario.get("order_log_odds", 0)
    beta[6:] = scenario["profile_log_odds_offsets"][1:]
    eta = x @ beta + random_intercept[:, None]
    y = rng.binomial(1, expit(eta))
    counts = {
        "diagnostic_trials": int(mask.sum()),
        "ai_reliance_opportunities": int((mask & (order < 4)).sum()),
        "self_reliance_opportunities": int((mask & (order >= 4)).sum()),
        "participants_without_opportunities": int((~mask.any(axis=1)).sum()),
    }
    return x, y, mask, beta, counts


def fit_glmm(x, y, mask, nodes=20):
    keep = mask.any(axis=1)
    x, y, mask = x[keep], y[keep], mask[keep]
    original_p = x.shape[-1]
    columns = list(range(original_p))
    missing_profiles = []
    reference_profile = 1
    if original_p == len(NAMES) and mask.any():
        # Keep all treatment/order terms. Recode only profile contrasts when a
        # profile has no observed opportunity, as dropping unused factor levels
        # does in a GLMM fit. This is the same fixed-effect predictor space.
        profile = np.where(x[:, :, 6:].sum(axis=2) == 0, 0, 1 + x[:, :, 6:].argmax(axis=2))
        observed = sorted(set(profile[mask].tolist()))
        reference_profile = 1 + min(observed)
        missing_profiles = [i + 1 for i in range(6) if i not in observed]
        columns = list(range(6)) + [5 + i for i in observed if i != reference_profile - 1]
        x = x[:, :, columns]
    flat = x[mask]
    p = x.shape[-1]
    if len(flat) <= p or np.linalg.matrix_rank(flat) < p or len(np.unique(y[mask])) < 2:
        return {"status": "rank_or_outcome_failure"}
    z, weights = hermgauss(nodes)
    z = z * np.sqrt(2)
    logw = np.log(weights) - 0.5 * np.log(np.pi)

    def objective(theta):
        sigma = np.exp(theta[-1])
        eta = (x @ theta[:-1])[:, :, None] + sigma * z[None, None, :]
        ll = ((y[:, :, None] * eta - np.logaddexp(0, eta)) * mask[:, :, None]).sum(
            axis=1
        )
        log_joint = ll + logw[None, :]
        log_integral = logsumexp(log_joint, axis=1)
        posterior = np.exp(log_joint - log_integral[:, None])
        residual = (y[:, :, None] - expit(eta)) * mask[:, :, None]
        beta_gradient = np.einsum(
            "ntk,ntp,nk->p", residual, x, posterior, optimize=True
        )
        sigma_gradient = np.sum(posterior * residual.sum(axis=1) * (sigma * z[None, :]))
        return -log_integral.sum(), -np.r_[beta_gradient, sigma_gradient]

    initial = np.zeros(p + 1)
    mean_y = np.clip(y[mask].mean(), 0.01, 0.99)
    initial[0] = np.log(mean_y / (1 - mean_y))
    initial[-1] = np.log(0.7)
    bounds = [(None, None)] * p + [(-7, np.log(3))]
    result = None
    for iterations in [200, 800]:
        result = minimize(
            objective,
            initial,
            jac=True,
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": iterations, "ftol": 1e-10, "gtol": 1e-5},
        )
        if result.success:
            break
        initial = result.x
    if not result.success:
        return {"status": "optimizer_failure", "message": str(result.message)}
    theta = result.x
    step = 1e-4
    hessian = np.column_stack(
        [
            (
                objective(theta + np.eye(p + 1)[j] * step)[1]
                - objective(theta - np.eye(p + 1)[j] * step)[1]
            )
            / (2 * step)
            for j in range(p + 1)
        ]
    )
    hessian = (hessian + hessian.T) / 2
    at_lower = theta[-1] < -6.95
    at_upper = theta[-1] > np.log(3) - 0.01
    if at_upper:
        return {"status": "upper_variance_boundary"}
    # At zero-variance boundary use fixed-variance curvature, report boundary.
    information = hessian[:-1, :-1] if at_lower else hessian
    if np.linalg.eigvalsh(information).min() <= 1e-7:
        return {"status": "information_failure"}
    covariance = np.linalg.inv(information)[:p, :p]
    se = np.sqrt(np.diag(covariance))
    beta_full = [None] * original_p
    se_full = [None] * original_p
    for column, estimate, error in zip(columns, theta[:-1], se):
        beta_full[column] = float(estimate)
        se_full[column] = float(error)
    return {
        "status": "ok",
        "beta": beta_full,
        "se": se_full,
        "profile_reference": reference_profile,
        "unobserved_profiles": missing_profiles,
        "active_columns": columns,
        "sigma": float(np.exp(theta[-1])),
        "zero_variance_boundary": bool(at_lower),
        "nll": float(result.fun),
    }


def holm_rejections(p1, p3):
    if min(p1, p3) > 0.025:
        return False, False
    return p1 <= (0.025 if p1 <= p3 else 0.05), p3 <= (0.025 if p3 < p1 else 0.05)


def run(config, repetitions, nodes, seed):
    summaries, records = [], []
    children = np.random.SeedSequence(seed).spawn(
        len(config["scenarios"]) * len(config["sample_sizes"]) * repetitions
    )
    cursor = 0
    for scenario in config["scenarios"]:
        for n in config["sample_sizes"]:
            group = []
            for repetition in range(repetitions):
                rng = np.random.default_rng(children[cursor])
                cursor += 1
                x, y, mask, truth, counts = simulate(n, scenario, rng)
                fitted = fit_glmm(x, y, mask, nodes)
                row = {
                    "scenario": scenario["name"],
                    "n": n,
                    "repetition": repetition,
                    **counts,
                    **fitted,
                }
                if fitted["status"] == "ok":
                    b, se = np.array(fitted["beta"], dtype=float), np.array(fitted["se"], dtype=float)
                    ps = 2 * norm.sf(np.abs(b[[1, 3]] / se[[1, 3]]))
                    r1, r3 = holm_rejections(*ps)
                    row.update(
                        {
                            "h1_reject": bool(r1),
                            "h3_reject": bool(r3),
                            "h2_covered": bool(abs(b[4] - truth[4]) <= 1.96 * se[4]),
                            "h2_log_ci_width": float(3.92 * se[4]),
                            "h2_bias": float(b[4] - truth[4]),
                        }
                    )
                group.append(row)
                records.append(row)
            ok = [r for r in group if r["status"] == "ok"]
            summary = {
                "scenario": scenario["name"],
                "n": n,
                "attempted": repetitions,
                "successful": len(ok),
                "failure_counts": {
                    status: sum(r["status"] == status for r in group)
                    for status in sorted(
                        {r["status"] for r in group if r["status"] != "ok"}
                    )
                },
            }
            for key in [
                "diagnostic_trials",
                "ai_reliance_opportunities",
                "self_reliance_opportunities",
                "participants_without_opportunities",
            ]:
                summary["mean_" + key] = float(np.mean([r[key] for r in group]))
            if ok:
                for label in ["h1", "h3"]:
                    # Failed fits count as non-rejections: unconditional power.
                    rate = sum(r[label + "_reject"] for r in ok) / repetitions
                    summary[label + "_holm_rejection_rate"] = rate
                    summary[label + "_mc_se"] = math.sqrt(
                        rate * (1 - rate) / repetitions
                    )
                widths = np.array([r["h2_log_ci_width"] for r in ok])
                summary.update(
                    {
                        "h2_median_log_ci_width": float(np.median(widths)),
                        "h2_log_ci_width_q10_q90": np.quantile(
                            widths, [0.1, 0.9]
                        ).tolist(),
                        "h2_median_ci_multiplicative_half_span": float(
                            np.exp(np.median(widths) / 2)
                        ),
                        "h2_mean_bias": float(np.mean([r["h2_bias"] for r in ok])),
                        "h2_coverage_successful_fits": float(
                            np.mean([r["h2_covered"] for r in ok])
                        ),
                        "zero_variance_boundaries": sum(
                            r["zero_variance_boundary"] for r in ok
                        ),
                    }
                )
            summaries.append(summary)
            print(json.dumps(summary), flush=True)
    return summaries, records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=Path(__file__).with_name("scenarios.json")
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=200)
    parser.add_argument("--nodes", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20261022)
    args = parser.parse_args()
    if args.repetitions < 1 or args.nodes < 5:
        parser.error("Positive repetitions and at least five quadrature nodes required")
    config = json.loads(args.config.read_text())
    start = time.time()
    summaries, records = run(config, args.repetitions, args.nodes, args.seed)
    output = {
        "kind": "simulation_not_observed_data",
        "seed": args.seed,
        "repetitions": args.repetitions,
        "quadrature_nodes": args.nodes,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "config": config,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "seconds": round(time.time() - start, 2),
        "summaries": summaries,
        "replicates": records,
        "limitations": [
            "Nuisance assumptions are scenarios, not estimates from Study 2.",
            "No H2 significance-based power claim is made.",
            "Precision target and pilot estimates remain to be fixed before recruitment.",
            "Non-adaptive quadrature approximation: compare higher-node run before final registration.",
            "Informative opportunity selection can change the conditional estimand; scenario comparisons do not identify a mediation mechanism.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n")


if __name__ == "__main__":
    main()
