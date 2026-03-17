#!/usr/bin/env python3
"""
Run report experiments and generate plots.

Two sweeps:
1) rounds sweep: iters_per_param=1000, rounds=1..5
2) iterations sweep: rounds=5, iters_per_param=500..5000 step 500

Logs results (append + resume) and writes plots under report/images/.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = REPO_ROOT / "report"
RESULTS_DIR = REPORT_DIR / "results"
IMAGES_DIR = REPORT_DIR / "images"

CSV_PATH = RESULTS_DIR / "experiments.csv"
JSONL_PATH = RESULTS_DIR / "experiments.jsonl"


@dataclass(frozen=True)
class ExperimentSpec:
    sweep: str  # "rounds_sweep" | "iters_sweep"
    rounds: int
    iterations_per_param: int
    random_restarts: int = 1
    init_strategy: str = "random"
    use_multi_metric: bool = True


@dataclass
class ExperimentResult:
    sweep: str
    rounds: int
    iterations_per_param: int
    random_restarts: int
    init_strategy: str
    use_multi_metric: bool
    best_error: float
    match_percent: float
    matches: int
    total_params: int
    elapsed_s: float
    timestamp: float


def _ensure_dirs() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def _load_completed_keys(csv_path: Path) -> set[Tuple[str, int, int, bool]]:
    if not csv_path.exists():
        return set()
    completed: set[Tuple[str, int, int, bool]] = set()
    with csv_path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                completed.add(
                    (
                        row["sweep"],
                        int(row["rounds"]),
                        int(row["iterations_per_param"]),
                        row["use_multi_metric"].lower() == "true",
                    )
                )
            except Exception:
                # If a row is malformed, skip it rather than blocking.
                continue
    return completed


def _append_csv(csv_path: Path, result: ExperimentResult) -> None:
    write_header = not csv_path.exists()
    with csv_path.open("a", newline="") as f:
        fieldnames = list(asdict(result).keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(asdict(result))


def _append_jsonl(jsonl_path: Path, result: ExperimentResult) -> None:
    with jsonl_path.open("a") as f:
        f.write(json.dumps(asdict(result)) + "\n")


def _run_single(spec: ExperimentSpec) -> ExperimentResult:
    """
    Executes one autotuning run and returns a lightweight summary for plotting.
    """
    # Import lazily so plotting-only mode doesn't require package imports.
    import sys

    src_dir = REPO_ROOT / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    from autotuner.sequential_tuner import run_sequential_autotuning

    t0 = time.time()
    if spec.sweep == "iters_sweep":
        # For iterations sweep, make iterations_per_param meaningful by sampling
        # more as the budget increases.
        selection_strategy = "epsilon_greedy"
        exploration_rate = 0.3
    else:
        # For restarts sweep, keep deterministic inner loop and vary restarts.
        selection_strategy = "deterministic_sweep"
        exploration_rate = 0.1

    best_config, best_error, error_history, actual_params, tuning_info = run_sequential_autotuning(
        iterations_per_param=spec.iterations_per_param,
        num_rounds=spec.rounds,
        use_multi_metric=spec.use_multi_metric,
        selection_strategy=selection_strategy,
        exploration_rate=exploration_rate,
        random_restarts=spec.random_restarts,
        init_strategy=spec.init_strategy,
        rng_seed=1337,
    )
    elapsed = time.time() - t0

    # tuning_info is expected to contain these keys in this repo.
    matches = int(tuning_info.get("final_matches", 0))
    match_percent = float(tuning_info.get("final_match_percent", 0.0))
    total_params = len(actual_params) if isinstance(actual_params, dict) else 0

    return ExperimentResult(
        sweep=spec.sweep,
        rounds=spec.rounds,
        iterations_per_param=spec.iterations_per_param,
        random_restarts=spec.random_restarts,
        init_strategy=spec.init_strategy,
        use_multi_metric=spec.use_multi_metric,
        best_error=float(best_error),
        match_percent=match_percent,
        matches=matches,
        total_params=total_params,
        elapsed_s=float(elapsed),
        timestamp=time.time(),
    )


def _specs(rounds_min: int, rounds_max: int) -> List[ExperimentSpec]:
    specs: List[ExperimentSpec] = []

    # 1) rounds sweep: iters fixed at 1000, rounds 1..5
    for r in range(rounds_min, rounds_max + 1):
        # Use "rounds" as the restart budget so increasing rounds means more exploration.
        # Keep num_rounds=1 for each restart to isolate restart effect.
        specs.append(ExperimentSpec(sweep="rounds_sweep", rounds=1, iterations_per_param=1000, random_restarts=r))

    # 2) iterations sweep: rounds fixed at 5, iters 500..5000 step 500
    for iters in range(500, 5000 + 1, 500):
        # Keep a fixed restart budget for stability; vary iterations_per_param.
        specs.append(ExperimentSpec(sweep="iters_sweep", rounds=5, iterations_per_param=iters, random_restarts=5))

    return specs


def _read_results(csv_path: Path) -> List[Dict[str, str]]:
    if not csv_path.exists():
        return []
    with csv_path.open("r", newline="") as f:
        return list(csv.DictReader(f))


def _plot(csv_path: Path) -> None:
    import matplotlib.pyplot as plt

    rows = _read_results(csv_path)
    if not rows:
        print(f"No results found at {csv_path}. Nothing to plot.")
        return

    def frows(sweep: str) -> List[Dict[str, str]]:
        out = [r for r in rows if r.get("sweep") == sweep]
        # Deduplicate by keeping the last row for each key if rerun.
        keyed: Dict[Tuple[int, int, int], Dict[str, str]] = {}
        for r in out:
            keyed[
                (int(r["rounds"]), int(r["iterations_per_param"]), int(r.get("random_restarts", "1")))
            ] = r
        return list(keyed.values())

    # Plot 1: rounds sweep (x=rounds)
    rs = frows("rounds_sweep")
    rs.sort(key=lambda r: int(r["random_restarts"]))
    x_rounds = [int(r["random_restarts"]) for r in rs]
    y_match = [float(r["match_percent"]) for r in rs]
    y_err = [float(r["best_error"]) for r in rs]

    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    ax1.plot(x_rounds, y_match, marker="o", label="Match %")
    ax1.set_xlabel("Random restarts")
    ax1.set_ylabel("Match %")
    ax1.grid(True, alpha=0.25)
    ax2 = ax1.twinx()
    ax2.plot(x_rounds, y_err, marker="s", color="tab:red", label="Best error")
    ax2.set_ylabel("Best error (lower is better)")
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="best")
    ax1.set_title("Random restarts sweep (iterations_per_param=1000, rounds=1 per restart)")
    fig.tight_layout()
    out1 = IMAGES_DIR / "rounds_sweep.png"
    fig.savefig(out1, dpi=200)
    plt.close(fig)

    # Plot 2: iterations sweep (x=iters)
    its = frows("iters_sweep")
    its.sort(key=lambda r: int(r["iterations_per_param"]))
    x_iters = [int(r["iterations_per_param"]) for r in its]
    y_match2 = [float(r["match_percent"]) for r in its]
    y_err2 = [float(r["best_error"]) for r in its]

    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    ax1.plot(x_iters, y_match2, marker="o", label="Match %")
    ax1.set_xlabel("Iterations per parameter")
    ax1.set_ylabel("Match %")
    ax1.grid(True, alpha=0.25)
    ax2 = ax1.twinx()
    ax2.plot(x_iters, y_err2, marker="s", color="tab:red", label="Best error")
    ax2.set_ylabel("Best error (lower is better)")
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="best")
    ax1.set_title("Iterations sweep (rounds=5, random_restarts=5)")
    fig.tight_layout()
    out2 = IMAGES_DIR / "iters_sweep.png"
    fig.savefig(out2, dpi=200)
    plt.close(fig)

    print(f"Wrote {out1}")
    print(f"Wrote {out2}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run autotuning sweeps for report graphs.")
    parser.add_argument("--rounds-min", type=int, default=1)
    parser.add_argument("--rounds-max", type=int, default=5)
    parser.add_argument("--no-run", action="store_true", help="Skip running; just plot from existing logs.")
    parser.add_argument("--plot-only", action="store_true", help="Alias for --no-run.")
    args = parser.parse_args()

    _ensure_dirs()

    if args.plot_only:
        args.no_run = True

    if not args.no_run:
        completed = _load_completed_keys(CSV_PATH)
        specs = _specs(args.rounds_min, args.rounds_max)
        to_run = [s for s in specs if (s.sweep, s.rounds, s.iterations_per_param, s.use_multi_metric) not in completed]

        print(f"Planned runs: {len(specs)} | already completed: {len(completed)} | remaining: {len(to_run)}")
        for i, spec in enumerate(to_run, start=1):
            print(f"[{i}/{len(to_run)}] sweep={spec.sweep} rounds={spec.rounds} iters={spec.iterations_per_param}")
            res = _run_single(spec)
            _append_csv(CSV_PATH, res)
            _append_jsonl(JSONL_PATH, res)
            print(
                f"  match={res.match_percent:.2f}% best_error={res.best_error:.6f} elapsed={res.elapsed_s:.1f}s"
            )

    _plot(CSV_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

