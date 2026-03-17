# Project Report Assets

This folder contains scripts + outputs used to generate report figures.

## Folder layout

- `report/results/`: CSV/JSON logs from experiment sweeps (append/resumable)
- `report/images/`: generated figures (PNG)

## Experiments requested

1) **Rounds sweep (iterations fixed)**  
   - iterations per parameter: **1000**
   - rounds: **1 → 5**

2) **Iterations sweep (rounds fixed)**  
   - rounds: **5**
   - iterations per parameter: **500 → 5000** (step **500**)

## Run

From repo root:

```bash
python3 report/run_experiments.py
```

To only plot from existing results:

```bash
python3 report/run_experiments.py --plot-only
```

Outputs:
- Logs: `report/results/experiments.csv` and `report/results/experiments.jsonl`
- Figures: `report/images/rounds_sweep.png`, `report/images/iters_sweep.png`

