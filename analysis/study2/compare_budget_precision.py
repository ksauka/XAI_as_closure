"""Paired N=160/192/200 sensitivity planning with the existing six-case GLMM."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import time

import numpy as np
import scipy
from scipy.stats import beta, norm

ROOT = Path(__file__).resolve().parents[2]
PLANNER_PATH = Path(__file__).with_name('simulate_precision.py')
spec = importlib.util.spec_from_file_location('six_case_planner', PLANNER_PATH)
planner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(planner)


def profile_indices(x):
    return np.where(x[:, :, 6:].sum(axis=2) == 0, 0, 1 + x[:, :, 6:].argmax(axis=2))


def balanced_subset(x, n):
    if n % 8 or n > len(x):
        raise ValueError('Requested subset must be balanced and fit within the panel.')
    cell = ((x[:, 0, 1] + .5) * 4 + (x[:, 0, 2] + .5) * 2 + x[:, 0, 3] + .5).astype(int)
    selected = np.concatenate([np.flatnonzero(cell == k)[:n // 8] for k in range(8)])
    if len(selected) != n:
        raise ValueError('Panel has insufficient participants in a cell.')
    return np.sort(selected)


def count_opportunities(x, mask):
    profile = profile_indices(x)
    cell = ((x[:, 0, 1] + .5) * 4 + (x[:, 0, 2] + .5) * 2 + x[:, 0, 3] + .5).astype(int)
    table = [[int((mask[cell == k] & (profile[cell == k] == p)).sum()) for p in range(6)] for k in range(8)]
    return {
        'diagnostic_trials': int(mask.sum()),
        'ai_reliance_opportunities': int((mask & (profile < 4)).sum()),
        'self_reliance_opportunities': int((mask & (profile >= 4)).sum()),
        'participants_without_opportunities': int((~mask.any(axis=1)).sum()),
        'profile_opportunities': [int((mask & (profile == p)).sum()) for p in range(6)],
        'cell_profile_opportunities': table,
        'cells_without_ai_opportunities': sum(sum(row[:4]) == 0 for row in table),
        'cells_without_self_opportunities': sum(sum(row[4:]) == 0 for row in table),
    }


def rate_interval(k, total):
    return [0. if k == 0 else float(beta.ppf(.025, k, total-k+1)),
            1. if k == total else float(beta.ppf(.975, k+1, total-k))]


def summarise(rows):
    ok = [r for r in rows if r['status'] == 'ok']
    out = {'scenario': rows[0]['scenario'], 'n': rows[0]['n'],
           'attempted': len(rows), 'successful': len(ok),
           'failure_counts': {s: sum(r['status'] == s for r in rows)
                              for s in sorted({r['status'] for r in rows if r['status'] != 'ok'})}}
    for key in ('diagnostic_trials', 'ai_reliance_opportunities', 'self_reliance_opportunities',
                'participants_without_opportunities', 'cells_without_ai_opportunities', 'cells_without_self_opportunities'):
        out['mean_' + key] = float(np.mean([r[key] for r in rows]))
    out['mean_profile_opportunities'] = np.mean([r['profile_opportunities'] for r in rows], axis=0).tolist()
    out['mean_cell_profile_opportunities'] = np.mean([r['cell_profile_opportunities'] for r in rows], axis=0).tolist()
    out['panels_missing_at_least_one_profile'] = sum(any(c == 0 for c in r['profile_opportunities']) for r in rows)
    for label in ('h1', 'h3'):
        for suffix in ('reject', 'positive_reject'):
            k = sum(r.get(label + '_' + suffix, False) for r in rows)
            p = k / len(rows)
            prefix = label + ('_holm' if suffix == 'reject' else '_positive_holm')
            out[prefix + '_rejection_rate'] = p
            out[prefix + '_mc_se'] = math.sqrt(p * (1-p) / len(rows))
            out[prefix + '_mc_interval95'] = rate_interval(k, len(rows))
    familywise = sum(r.get('h1_reject', False) or r.get('h3_reject', False) for r in rows)
    out['either_h1_h3_rejection_rate'] = familywise / len(rows)
    out['either_h1_h3_mc_interval95'] = rate_interval(familywise, len(rows))
    if ok:
        widths = np.array([r['h2_log_ci_width'] for r in ok])
        out.update({
            'h2_median_log_ci_width': float(np.median(widths)),
            'h2_log_ci_width_q10_q90': np.quantile(widths, [.1, .9]).tolist(),
            'h2_median_ci_multiplicative_half_span': float(np.exp(np.median(widths) / 2)),
            'h2_median_or_interval_endpoints': [float(np.median([r['h2_or_lower'] for r in ok])), float(np.median([r['h2_or_upper'] for r in ok]))],
            'h2_coverage_successful_fits': float(np.mean([r['h2_covered'] for r in ok])),
            'h2_coverage_mc_interval95': rate_interval(sum(r['h2_covered'] for r in ok), len(ok)),
            'h2_mean_bias': float(np.mean([r['h2_bias'] for r in ok])),
            'zero_variance_boundaries': sum(r['zero_variance_boundary'] for r in ok),
            'profile_reference_counts': {str(p): sum(r['profile_reference'] == p for r in ok) for p in range(1, 7)},
        })
    return out


def paired_comparisons(records, sample_sizes):
    comparisons = []
    for low, high in zip(sample_sizes[:-1], sample_sizes[1:]):
        left = {r['repetition']: r for r in records if r['n'] == low}
        right = {r['repetition']: r for r in records if r['n'] == high}
        item = {'scenario': records[0]['scenario'], 'low_n': low, 'high_n': high}
        for label in ('h1', 'h3'):
            differences = np.array([int(right[i].get(label + '_positive_reject', False)) - int(left[i].get(label + '_positive_reject', False)) for i in left])
            mean = float(differences.mean())
            error = float(differences.std(ddof=1) / np.sqrt(len(differences)))
            item[label + '_positive_power_gain'] = mean
            item[label + '_paired_mc_interval95'] = [mean - 1.96 * error, mean + 1.96 * error]
        comparable = [(left[i], right[i]) for i in left if left[i]['status'] == right[i]['status'] == 'ok']
        item['paired_successful'] = len(comparable)
        if comparable:
            item['median_h2_width_ratio_low_over_high'] = float(np.median([a['h2_log_ci_width'] / b['h2_log_ci_width'] for a,b in comparable]))
        comparisons.append(item)
    return comparisons


def run_scenario(job):
    index, scenario, config, output = job
    records = []
    repeats = config['repetitions']
    for repetition in range(repeats):
        rng = np.random.default_rng(np.random.SeedSequence([config['seed'], index, repetition]))
        x, y, mask, truth, _ = planner.simulate(max(config['sample_sizes']), scenario, rng)
        for n in config['sample_sizes']:
            selected = balanced_subset(x, n)
            xx, yy, mm = x[selected], y[selected], mask[selected]
            fitted = planner.fit_glmm(xx, yy, mm, config['quadrature_nodes'])
            row = {'scenario': scenario['name'], 'n': n, 'repetition': repetition,
                   **count_opportunities(xx, mm), **fitted}
            if row['status'] == 'ok':
                estimates = np.array(row['beta'], dtype=float)
                errors = np.array(row['se'], dtype=float)
                ps = 2 * norm.sf(np.abs(estimates[[1,3]] / errors[[1,3]]))
                reject1, reject3 = planner.holm_rejections(*ps)
                row.update(h1_reject=bool(reject1), h3_reject=bool(reject3),
                    h1_positive_reject=bool(reject1 and estimates[1] > 0),
                    h3_positive_reject=bool(reject3 and estimates[3] > 0),
                    h2_covered=bool(abs(estimates[4] - truth[4]) <= 1.96 * errors[4]),
                    h2_log_ci_width=float(3.92 * errors[4]), h2_bias=float(estimates[4] - truth[4]),
                    h2_or_lower=float(np.exp(estimates[4] - 1.96*errors[4])),
                    h2_or_upper=float(np.exp(estimates[4] + 1.96*errors[4])))
            records.append(row)
        if (repetition + 1) % 100 == 0:
            print(json.dumps({'scenario': scenario['name'], 'panels_completed': repetition+1, 'panels_total': repeats}), flush=True)
    summaries = [summarise([r for r in records if r['n'] == n]) for n in config['sample_sizes']]
    artifact = Path(output) / 'replicates' / (scenario['name'] + '.json')
    artifact.parent.mkdir(exist_ok=True)
    artifact.write_text(json.dumps({'kind': 'simulation_not_observed_data', 'scenario': scenario, 'replicates': records}, allow_nan=False) + '\n')
    return {'summaries': summaries, 'paired_comparisons': paired_comparisons(records, config['sample_sizes']),
            'artifact': str(artifact.relative_to(Path(output))), 'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--repetitions', type=int)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if args.repetitions:
        config['repetitions'] = args.repetitions
    if config['repetitions'] < 2:
        raise ValueError('At least two panels required for Monte Carlo uncertainty.')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    jobs = [(i, scenario, config, str(args.output_dir)) for i,scenario in enumerate(config['scenarios'])]
    start = time.time()
    finished = []
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(run_scenario, job) for job in jobs]
        for future in as_completed(futures):
            result = future.result()
            finished.append(result)
            (args.output_dir / 'progress.json').write_text(json.dumps({'completed_scenarios': len(finished), 'total_scenarios': len(jobs), 'elapsed_seconds': round(time.time()-start,1)}))
            print(json.dumps({'scenario_finished': result['summaries'][0]['scenario'], 'completed_scenarios': len(finished)}), flush=True)
    order = {s['name']: i for i,s in enumerate(config['scenarios'])}
    finished.sort(key=lambda r: order[r['summaries'][0]['scenario']])
    metadata = {'kind': 'simulation_not_observed_data', 'config': config,
        'source_hashes': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (PLANNER_PATH, Path(__file__))},
        'input_config_sha256': hashlib.sha256(args.config.read_bytes()).hexdigest(),
        'git_commit': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT).decode().strip(),
        'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__,
        'blas_threads': os.environ.get('OPENBLAS_NUM_THREADS'), 'workers': args.workers,
        'seconds': round(time.time()-start,2),
        'summaries': [s for result in finished for s in result['summaries']],
        'paired_comparisons': [s for result in finished for s in result['paired_comparisons']],
        'replicate_artifacts': [{'path': r['artifact'], 'sha256': r['sha256']} for r in finished],
        'limitations': ['All effect and opportunity rates are assumptions, not Study 2 estimates.',
            'Historical expert data and material version are not interchangeable with revised Study 2.',
            'H2 is evaluated by precision and coverage, not rejection power.',
            'No recruitment target or acceptable-precision threshold is selected.',
            'Main-effect rejection rates count failed fits as non-rejections; coverage is conditional on successful fits.',
            'Unobserved profiles trigger an explicitly recorded contrast-reference change, not removal of treatment terms.',
            'Informative opportunity selection is a conditional-estimand sensitivity, not just a sampling-precision scenario.']}
    (args.output_dir / 'results.json').write_text(json.dumps(metadata, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'completed': True, 'configurations': len(metadata['summaries']), 'fits_attempted': len(jobs)*config['repetitions']*len(config['sample_sizes']), 'seconds': metadata['seconds']}), flush=True)


if __name__ == '__main__':
    main()
