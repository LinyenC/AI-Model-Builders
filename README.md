# AI-Model-Builders

AI-Model-Builders is the code accompanying a hydrologic model-structure search experiment. It uses a large language model as a candidate generator for process-level HBV structural changes, then compiles, validates, calibrates, and evaluates each candidate outside the LLM.

## What Is Included

- `src/llm_hydro_structure_v032/`: core HydroAgent package.
- `run_hydroagent.py`: single-basin and batch LLM structure-search runner.
- `run_hbv_baseline.py`: baseline HBV calibration runner.
- `tests/`: unit tests for candidate validation, calibration, and experiment control logic.
- `environment.yml`: Conda environment specification.
- `requirements.txt`: pip dependency list.
- `pyproject.toml`: lightweight packaging/test configuration.

## Workflow

1. Load CAMELS-US forcing, streamflow, and basin attributes.
2. Calibrate the baseline HBV model on the calibration split.
3. Build basin diagnostics using calibration/development data only.
4. Ask the LLM to propose HBV module-DSL structural changes.
5. Compile each `module_dsl` into executable HBV code.
6. Reject unsafe or invalid candidates using static and runtime checks.
7. Calibrate valid candidates independently.
8. Select the best model using the development split.
9. Report final-test metrics only after selection.

The final-test split is not used for candidate generation, calibration, diagnosis, or model selection.

## Data

The code expects the CAMELS-US dataset in a local directory. Data are not included in this repository.

Set the dataset path with either:

```bash
export HYDROAGENT_CAMELS_ROOT=/path/to/CAMELS_US
```

or pass it explicitly:

```bash
python run_hydroagent.py --camels-root /path/to/CAMELS_US
```

On Windows PowerShell:

```powershell
$env:HYDROAGENT_CAMELS_ROOT = "D:\data\CAMELS_US"
```

## Installation

Using Conda:

```bash
conda env create -f environment.yml
conda activate hydroagent
```

Using pip in an existing Python 3.11 environment:

```bash
pip install -r requirements.txt
pip install -e .
```

## LLM Configuration

For OpenAI or an OpenAI-compatible endpoint:

```bash
export OPENAI_API_KEY=your_api_key
```

Optional settings:

```bash
export OPENAI_BASE_URL=https://api.openai.com/v1
export OPENAI_API_MODE=responses
export OPENAI_TIMEOUT_SECONDS=300
export OPENAI_MAX_RETRIES=8
export OPENAI_MAX_OUTPUT_TOKENS=30000
```

For OpenAI-compatible chat-completions providers that do not support strict JSON schema:

```bash
export OPENAI_API_MODE=chat_completions
export OPENAI_RESPONSE_FORMAT=json_object
```

## Run A Single Basin

Offline smoke test:

```bash
python run_hydroagent.py \
  --agent offline \
  --data-mode camels_us \
  --camels-root /path/to/CAMELS_US \
  --basin-id 12025000 \
  --output-dir outputs/smoke_12025000 \
  --max-search-evaluations 120
```

LLM structure-search run:

```bash
python run_hydroagent.py \
  --agent openai \
  --llm-model gpt-5.4-mini \
  --llm-call-mode single_stage \
  --data-mode camels_us \
  --camels-root /path/to/CAMELS_US \
  --basin-id 12025000 \
  --output-dir outputs/llm_12025000 \
  --max-llm-iterations 5 \
  --candidate-workers 3 \
  --max-search-evaluations 2000
```

Two-stage diagnosis mode:

```bash
python run_hydroagent.py \
  --agent openai \
  --llm-model gpt-5.4-mini \
  --llm-call-mode two_stage_diagnosis \
  --data-mode camels_us \
  --camels-root /path/to/CAMELS_US \
  --basin-id 12025000 \
  --output-dir outputs/two_stage_12025000
```

## Batch Runs

Create a text file with one basin ID per line, then run:

```bash
python run_hydroagent.py \
  --agent openai \
  --llm-model gpt-5.4-mini \
  --data-mode camels_us \
  --camels-root /path/to/CAMELS_US \
  --basin-file basin_ids.txt \
  --output-dir outputs/batch_run \
  --basin-workers 10 \
  --candidate-workers 3 \
  --max-llm-iterations 5
```

For batch LLM runs, the code uses a lock file by default so that multiple basins/candidates can be calibrated in parallel while only one LLM request is active at a time.

## Baseline Calibration

```bash
python run_hbv_baseline.py \
  --camels-root /path/to/CAMELS_US \
  --basin-file basin_ids.txt \
  --output-dir outputs/HBVbaseline \
  --max-workers 12
```

You can reuse a baseline candidate in a later LLM run:

```bash
python run_hydroagent.py \
  --agent openai \
  --data-mode camels_us \
  --camels-root /path/to/CAMELS_US \
  --basin-id 12025000 \
  --reuse-baseline-candidate-result outputs/HBVbaseline/basins/12025000/candidate_artifacts/baseline_standard_hbv_fine_process_dsl/candidate_result.json
```

## Outputs

Each experiment directory contains:

- `results.json`: complete experiment summary.
- `metrics_summary.csv`: all valid candidates by split.
- `selected_metrics.csv`: baseline and selected model metrics.
- `report.md`: human-readable run report.
- `memory/`: search history passed to later LLM rounds.
- `candidates/`: compiled candidate models and calibration records.

Generated outputs are ignored by git.

## Tests

```bash
python -m unittest discover -s tests
```

## Reproducibility Notes

- Calibration uses the calibration split only.
- Model selection uses the development split only.
- Final-test metrics are computed after selection.
- Candidate code is checked for restricted imports, file/network access, dynamic execution, required function signatures, and hydrologic stability tests.
- Candidate generation follows an iteration policy: early rounds enforce simple one-module changes, and later rounds require a mix of one-, two-, and three-or-more-module candidates.
