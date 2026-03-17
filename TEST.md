High‑level goal
The framework’s job is to infer your CPU’s hidden microarchitecture parameters (ROB size, cache sizes/latencies, issue width, etc.) by:
Generating diverse synthetic workloads,
Getting ground‑truth performance metrics for those workloads via MacSim (or a timing fallback),
Building a parametric performance model that predicts metrics as a function of microarch parameters,
Running a search algorithm (sequential tuner or MAB bandit) over the discrete parameter space to find the configuration whose predicted metrics best match the measured metrics.
Below is how that actually works, step by step, in terms of concrete modules and data.
1. Workload definitions (what is being measured)
Module: workload_registry.py
Core object: WORKLOADS – a big dict mapping workload IDs like w1_matrix_mult, w6_branch_intensive, w28_neural_network, etc., to:
code: an inline Python program that:
Allocates data (matrices, arrays, graphs, trees…),
Runs some algorithm (matrix mult, FFT, Monte Carlo, BFS, N‑body, etc.),
Prints Execution time: X.XXXXXX seconds.
description: what behavior it stresses (branching, cache, SIMD, memory, HPC).
collection_types: legacy “VTune style” tags, kept mostly for documentation.
Effect: you get ~30 synthetic workloads, each stressing different CPU subsystems so the error surface in parameter space is informative, not degenerate.
Helpers:
get_all_workloads() → list of all workload IDs.
get_workload_code(id) → the Python source for that workload.
These are used by the runner and MacSim integration.
2. Running workloads and collecting “ground truth”
2.1 BenchmarkRunner: how workloads are actually executed
Module: benchmark_runner.py
Class: BenchmarkRunner
On init:
Creates data/benchmarks/ as a directory for temporary workload scripts.
Key steps when it runs a workload:
get_workload_command(workload_id)
Calls get_workload_code(workload_id) from the registry.
Writes that string to data/benchmarks/{workload_id}_temp.py.
Returns a command like [sys.executable, "…/w1_matrix_mult_temp.py"].
If the registry doesn’t know the workload, there’s a smaller hard‑coded fallback dict of few basic workloads, and finally an .exe or echo fallback.
run_benchmark(workload_id, use_macsim=True, fallback_on_error=True, cpu_params=None)
Primary path: call into MacSimProfiler.profile_workload(...):
Input:
command: the workload command list from above.
workload_id: used for file naming.
cpu_params: optional microarch parameter assignment to simulate.
Output: a dict of metrics:
Always at least: execution_time, elapsed_time, cpu_time, and _source.
When MacSim stats are available: cpi, ipc, cache hits/misses and hit rates, etc.
Validation: if execution_time is inf or ≤ 0, it treats this as invalid and raises.
Fallback (if fallback_on_error=True):
Just runs the Python command directly with subprocess.run,
Times it with time.time(), then (optionally) parses Execution time: … from stdout,
Returns only timing metrics and _source='direct_timing'.
2.2 MacSimProfiler: how MacSim is wired in
Module: macsim_profiler.py
Class: MacSimProfiler
Low‑level behavior:
MacSim binary resolution
On init, _find_macsim() tries several hard‑coded locations (e.g. …/macsim/bin/macsim, which macsim, plus a system‑specific path).
Sets self.macsim_path and a macsim_results/ folder in your project root where it writes params/, compiled_workloads/ and per‑workload result dirs.
Parameter file generation (_create_params_file)
Builds a *.in parameter file for MacSim in macsim_results/params/.
Starts from a dictionary of default sim parameters (core types, max_insts, fetch width, default caches).
If cpu_params is provided (our high‑level parameters: rob_size, issue_width, l1_cache_size, etc.), it maps them to MacSim’s config keys:
issue_width → large_width
rob_size → rob_large_size
l1_cache_size → l1_large_num_set (approximate mapping of size→sets)
l1_latency → l1_large_latency
l2_cache_size → l2_large_num_set
l2_latency → l2_large_latency
l3_cache_size → llc_num_set
branch_predictor_size → bp_hist_length
etc.
Writes them out in MacSim’s textual format (key–value lines grouped by sections).
Python → C++ conversion and compilation
_python_to_cpp(workload_id, python_code):
Pattern‑matches on workload name / code to select one of many pre‑templated C++ kernels:
Matrix mult, bubble sort, DFT/FFT‑like, memory‑intensive strided loops, compute‑intensive loops, branch‑intensive, cache‑friendly, graph BFS, N‑body, Ray tracing, etc.
These are hand‑written C++ equivalents approximating the Python workload behavior, not a generic translator.
Writes a full C++ program with main() that:
Initializes random data,
Runs the kernel,
Times it with <chrono>,
Prints Execution time: ....
_compile_workload(...):
Saves that C++ into macsim_results/compiled_workloads/{workload_id}.cpp,
Compiles with g++ -O2 -std=c++11 -o {binary} (always uses simple DFT, no FFTW),
On success returns the compiled binary path.
profile_workload end‑to‑end
Creates a per‑workload result dir: macsim_results/{workload_id}/.
Writes params file via _create_params_file(...).
Tries to compile the workload (_compile_workload).
If it has a binary:
Runs the binary with subprocess.run inside the result dir, capturing stdout.
Extracts an execution time:
Initially via end_time - start_time,
Then refined by parsing Execution time: from stdout if present.
Calls _estimate_metrics_from_params(execution_time, cpu_params) to “fake” secondary metrics (CPI, cache hit rates, etc.) from the CPU params:
Uses rough analytic rules: bigger caches → higher hit rate, wider issue / more ROB → smaller CPI, etc.
Optionally tries to run actual MacSim with:
macsim_path -param {params_file},
A toy trace_file_list written into the result dir.
If general.stat.out, memory.stat.out, etc. appear, _extract_metrics parses them and overlays these more faithful metrics on top of the estimates.
Marks _source='macsim' and sets execution_time / elapsed_time / cpu_time.
If compilation or MacSim pathing fails:
Falls back to direct timing of the Python command, returning only timing metrics.
So “ground truth” is either:
Direct MacSim stats, or
A hybrid of real binary timing + approximate metrics inferred from CPU params, or
Pure wall‑clock timing of the Python workload (if MacSim isn’t usable).
2.3 Collecting ground truth across all workloads
BenchmarkRunner.collect_ground_truth(...)
If workload_ids is None, it pulls them from get_all_workloads().
For each workload:
Calls run_benchmark(... use_macsim=True ...).
Stores the returned metric dict under that workload ID.
Appends a _metadata block describing:
Source, metric names, list of workloads.
Writes JSON to data/results/ground_truth.json.
Returns the full dict.
mab_autotuner.load_ground_truth()
Reads that JSON, strips _metadata, normalizes old formats to the new dict‑per‑workload format.
If the file doesn’t exist, it calls BenchmarkRunner.collect_ground_truth to build it.
3. SystemProfiler: what the “true” parameters are
Module: system_profiler.py
Class: SystemProfiler
Implementation details:
On init, it caches some platform info (system, processor, machine).
extract_cpu_parameters():
Branches on OS.
Linux path:
Reads /proc/cpuinfo.
Uses regexes to find L1d cache: XXX KB, L2 cache: YYY KB.
Heuristically sets issue_width if it sees SIMD extensions (sse, avx).
Windows path: uses wmic and tries to parse cache info lines.
This returns a very raw dict, e.g. {l1_cache_size: 64, l2_cache_size: 256, issue_width: 4, …} (where “…” might be empty).
_map_to_parameter_space(params)
Imports TUNABLE_PARAMETERS from mab_autotuner.
For each tunable parameter (rob size, caches, latencies, bandwidth, etc.), it:
Either takes the discovered value or a reasonable default,
Rounds it to the nearest allowed discrete option using min(options, key=lambda |x−value|).
Also fills in parameters the OS doesn’t expose (latencies, ROB size, predictor size, etc.) with plausible defaults.
get_actual_parameters()
Wraps the above and falls back to a hard‑coded modern CPU config if anything fails.
This produces actual_params, a dict in the exact discrete parameter space the tuner searches over, which is used only for validation / accuracy scoring (except in some “maximized” paths where it was historically used to shrink the search space, but that’s explicitly commented out now).
4. Performance model: how you “simulate” different CPUs without hardware
Because you cannot truly change microarchitecture of your real CPU, the framework needs a model that says:
> “If I change from config A to config B, how would metrics change?”
4.1 Base model (PerformanceModel)
Module: performance_model.py
Class: PerformanceModel
Core ideas:
Maintains a base_execution_time (set from average ground‑truth).
Has impact coefficients:
rob_impact, width_impact, l1_size_impact, l1_latency_impact, l2_size_impact, l2_latency_impact.
estimate_execution_time(ap):
Starts from base_execution_time.
Applies multiplicative adjustments:
ROB:
rob_factor = rob_baseline / ap['rob_size']
time *= (1 + rob_impact * (rob_factor - 1))
→ bigger rob_size → rob_factor < 1 → time decreases.
Issue width, L1 size/latency, L2 size/latency similarly.
Clamps to a minimum positive time.
estimate_all_metrics(ap, base_metrics):
Calls estimate_execution_time.
Estimates CPI, IPC, cache hit/miss rates, branch misprediction rates based on:
Ratios of ap vs baseline values.
Modest analytic relationships (bigger caches → better hit rates; bigger ROB and width → smaller CPI).
Copies through some base metrics if present.
4.2 Enhanced model (EnhancedPerformanceModel)
Module: enhanced_performance_model.py
Class: EnhancedPerformanceModel(PerformanceModel)
Differences vs base:
Larger impact factors (e.g. rob_impact=0.8, l1_size_impact=0.85, etc.) to make parameter differences show more strongly in error.
Workload‑aware scaling:
For workloads whose ID suggests matrix/memory/cache, it scales up cache impacts.
For branch_*, it scales up ROB impact.
For compute/vector workloads, it scales width impact.
Adds effects of many more parameters:
l3_cache_size, l3_latency, memory_latency, memory_bandwidth,
branch_predictor_size, tlb_size, execution_units, simd_width,
prefetcher_lines, smt_threads (with behavior depending on workload type).
estimate_all_metrics(...) is similarly richer (L3 hit rates, TLB hit rates, memory bandwidth predictions, etc.).
calibrate_from_ground_truth(ground_truth):
Computes mean and variance of real execution times.
Sets base_execution_time to the average.
If coefficient of variation is high, it boosts impact factors further.
If cache metrics are present, further increases cache‑related impact.
In the sequential tuner and maximized autotuning, this enhanced model is what is used.
5. Error metric: how a configuration’s quality is scored
Function: calculate_aggregate_error in mab_autotuner.py.
Inputs:
ap: a parameter assignment (one candidate CPU).
ground_truth: mapping workload_id → {metric_name → value}.
performance_model: either PerformanceModel or EnhancedPerformanceModel.
Flags: use_multi_metric, optional metric_weights.
Steps:
If no custom weights, builds a default metric_weights dict giving:
Highest weights to timing metrics (execution_time, elapsed_time, cpu_time),
Medium to CPI/IPC, cache hit rates, etc.,
Small default weight for any unknown metrics.
Gathers all metric names across all workloads (excluding _source, _metadata).
For each workload wi:
Calls estimate_all_metrics(workload_id, ap, performance_model, ground_truth)
→ this internally sets the model’s base time from that workload’s execution time and predicts metrics under this ap.
If use_multi_metric=True:
For each metric present in both ground truth and estimate:
Computes normalized error: |C(m) − S(m)| / |C(m)| (if C(m) ≠ 0).
Squares it, multiplies by the metric’s weight, and accumulates into workload_error_squared.
If there were no overlapping metrics, it falls back to plain squared error on execution_time.
If use_multi_metric=False, uses plain squared error on execution_time.
Collects all workloads’ workload_error_squared into an array and finally computes:
$E_\mathrm{Agg} = \sqrt{\sum_\text{workloads} E_{wi}^2}$
This scalar aggregate error is what every search algorithm tries to minimize.
6. Search algorithms: how the framework explores parameter space
You have two main tuners:
6.1 Sequential tuner (used by run_full_autotuning.py)
Module: sequential_tuner.py
Function: run_sequential_autotuning(iterations_per_param, num_rounds, use_multi_metric, metric_weights, param_order)
Control flow when run_full_autotuning.py calls it:
Load ground truth: ground_truth = load_ground_truth().
Initialize enhanced model:
Extracts all execution_times, computes avg_ground_truth,
Sets performance_model.base_execution_time = avg_ground_truth,
Calls performance_model.calibrate_from_ground_truth(ground_truth).
Decide parameter order:
If param_order is None, uses list(TUNABLE_PARAMETERS.keys()).
Initial configuration:
For each param, picks the middle value from its discrete list → current_config.
Outer loop over rounds (1…num_rounds):
For each param in param_order:
Logs current value and the list of all values.
param_best_value = current value, param_best_error = +∞.
For iteration in 0…iterations_per_param-1:
If iteration < len(values), just try each possible value once (pure exploration).
Else, use a very simple epsilon‑greedy:
10% of the time: random value from the list,
90%: reuse param_best_value (exploit).
Build test_config = current_config with this param set to test_value.
Call calculate_aggregate_error(test_config, ground_truth, performance_model, use_multi_metric, metric_weights).
Append error to per‑param and global error_history.
If this error beats param_best_error, update param_best_value, maybe print a message.
If this error beats global best_error, update best_config and print “NEW GLOBAL BEST”.
After iterations_per_param iterations, set current_config[param_name] = param_best_value.
Record round summary in round_results.
After all rounds:
Calls SystemProfiler().get_actual_parameters() to obtain actual_params.
Counts how many parameters in best_config exactly equal the actual value (just to report match percentage).
Builds a detailed tuning_info dict (per‑param histories, per‑round results, match stats, number of workloads).
Returns (best_config, best_error, error_history, actual_params, tuning_info).
So for each parameter, it does an inner local search holding others fixed, iteratively improving per‑param choices while tracking a global best across the full vector.
6.2 MAB tuner (UCB1 bandit)
Module: mab_autotuner.py
There are two layers here:
Low‑level bandits:
UCB1Bandit: pre‑generates all combinations of tunable_params (Cartesian product), shuffles them, and uses the classic UCB1 formula:
Reward = -error,
For each arm k: Q_k + sqrt(2 * ln(t) / N_k),
Always pulls arms with infinite UCB first (unpulled),
Keeps counts and values arrays.
LazyUCB1Bandit (in lazy_bandit.py): for huge spaces, it:
Doesn’t pre‑generate all configs,
Generates random configs as needed, hash‑indexes them in dictionaries,
Applies UCB1 over just the already‑encountered arms, with some probability of random exploration to bring in new configs.
High‑level loops:
run_autotuning(max_iterations, tunable_params=None):
Loads ground truth, initializes base PerformanceModel, calibrates base time.
Picks UCB1Bandit or (intended) a lazy bandit (the use_lazy_generation variable is referenced but not defined where you read; in other paths it is defined).
For each iteration:
config_ap, arm_index = bandit.select_arm().
error = calculate_aggregate_error(config_ap, ground_truth, performance_model, use_multi_metric=True).
bandit.update(arm_index, error).
Track global best config and error; log progress.
run_maximized_autotuning:
Similar, but always uses EnhancedPerformanceModel, optionally LazyUCB1Bandit, and emphasizes multi‑metric error.
After the search, it calls SystemProfiler to get actual_params and prints/returns match stats and coverage statistics (how many unique configs tested, fraction of search space explored).
In both, the core difference from sequential tuning is that the entire parameter vector is treated as a single “arm” instead of tuning one parameter at a time.
7. Orchestration: what run_full_autotuning.py actually does
The script you have open is basically a full pipeline driver:
Ensure ground truth exists:
Builds a BenchmarkRunner() and all_workloads = get_all_workloads().
If data/results/ground_truth.json is missing:
Calls benchmark_runner.collect_ground_truth(workload_ids=None, output_file=ground_truth_file).
Else, just reports how many workloads are in the existing file.
Extract actual CPU parameters:
system_profiler = SystemProfiler().
actual_params = system_profiler.get_actual_parameters().
Prints each param and value.
Run sequential autotuning:
Prints that it’s doing 5 rounds × 5000 iterations/param.
Calls:
     best_config, best_error, error_history, predicted_actual_params, tuning_info = \         run_sequential_autotuning(             iterations_per_param=5000,             num_rounds=5,             use_multi_metric=True         )
Note: predicted_actual_params is actually the actual_params returned by the tuner (from SystemProfiler inside sequential_tuner), and best_config is the predicted config.
Compare predicted vs actual:
Prints “Predicted Parameters” from best_config.
Prints “Actual Parameters” from the earlier actual_params.
Builds a joint set of parameter names and prints a row for each with predicted, actual, and a ✓/✗ match flag.
Computes overall match ratio and prints best_error.
Save final summary:
Writes full_autotuning_results.json containing:
predicted_parameters (best_config),
actual_parameters,
matches, total_parameters, match_percent,
best_error,
tuning_info (per‑param and per‑round details),
workloads_used.
So the core loop you run from this script is:
Ground truth via BenchmarkRunner + MacSimProfiler → ground_truth.json,
Actual CPU params via SystemProfiler,
Search over TUNABLE_PARAMETERS using EnhancedPerformanceModel + multi‑metric error via run_sequential_autotuning,
Compare and save.
