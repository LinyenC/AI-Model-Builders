from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from llm_hydro_structure_v032 import CalibrationBudget, run_batch_experiment, run_experiment  # noqa: E402
from llm_hydro_structure_v032.paths import DEFAULT_CAMELS_ROOT  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the hydro-DSL HBV LLM structure-search v0.3.2 POC.")
    parser.add_argument("--seed", type=int, default=9)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "experiment_001")
    parser.add_argument("--data-mode", choices=["camels_us", "synthetic"], default="camels_us")
    parser.add_argument("--camels-root", type=Path, default=DEFAULT_CAMELS_ROOT)
    parser.add_argument("--basin-id", default="12025000")
    parser.add_argument(
        "--basin-ids",
        default=None,
        help="Comma-separated basin IDs for batch CAMELS-US runs. Overrides --basin-id when provided.",
    )
    parser.add_argument(
        "--basin-file",
        type=Path,
        default=None,
        help="Text file with one CAMELS-US basin ID per line for batch runs.",
    )
    parser.add_argument("--forcing-product", choices=["daymet", "maurer", "nldas"], default="daymet")
    parser.add_argument("--warmup-start", default="1980-10-01")
    parser.add_argument("--calibration-start", default="1981-10-01")
    parser.add_argument("--calibration-end", default="1989-09-30")
    parser.add_argument("--development-start", default="1989-10-01")
    parser.add_argument("--development-end", default="1994-09-30")
    parser.add_argument("--final-test-start", default="1994-10-01")
    parser.add_argument("--final-test-end", default="1999-09-30")
    parser.add_argument(
        "--agent",
        choices=["offline", "openai", "openai_no_diagnosis"],
        default="offline",
        help="Use the deterministic offline surrogate or a real OpenAI-backed module-DSL agent.",
    )
    parser.add_argument("--llm-model", default="gpt-5.4-mini")
    parser.add_argument(
        "--llm-call-mode",
        choices=["single_stage", "two_stage_diagnosis"],
        default="single_stage",
        help=(
            "single_stage keeps the original one-call candidate generation. "
            "two_stage_diagnosis first asks the LLM for diagnosis/directions, then passes that "
            "diagnosis into the normal candidate-generation call."
        ),
    )
    parser.add_argument(
        "--llm-api-mode",
        choices=["responses", "chat_completions"],
        default=None,
        help=(
            "OpenAI-compatible API surface for structured LLM calls. Defaults to OPENAI_API_MODE "
            "or responses. Use chat_completions for OpenAI-compatible endpoints that return empty "
            "Responses API output_text."
        ),
    )
    parser.add_argument(
        "--llm-response-format",
        choices=["json_schema", "json_object"],
        default=None,
        help=(
            "Structured-output response_format. Defaults to OPENAI_RESPONSE_FORMAT or json_schema. "
            "Use json_object for DeepSeek-style OpenAI-compatible chat endpoints that do not support "
            "json_schema."
        ),
    )
    parser.add_argument(
        "--llm-timeout-seconds",
        type=float,
        default=None,
        help="Per-request LLM timeout in seconds. Defaults to 300 for real LLM agents.",
    )
    parser.add_argument(
        "--llm-max-retries",
        type=int,
        default=None,
        help="Maximum attempts for each LLM request. Defaults to 8 for real LLM agents.",
    )
    parser.add_argument(
        "--llm-retry-initial-seconds",
        type=float,
        default=None,
        help="Initial backoff before retrying a failed LLM request. Defaults to 30 seconds.",
    )
    parser.add_argument(
        "--llm-retry-max-seconds",
        type=float,
        default=None,
        help="Maximum backoff between LLM retries. Defaults to 300 seconds.",
    )
    parser.add_argument(
        "--llm-json-repair-attempts",
        type=int,
        default=None,
        help=(
            "Additional LLM calls allowed when a response is not valid JSON. Defaults to "
            "OPENAI_JSON_REPAIR_ATTEMPTS or 2."
        ),
    )
    parser.add_argument(
        "--llm-request-lock-path",
        type=Path,
        default=None,
        help=(
            "Optional cross-process lock file. In batch OpenAI runs, defaults to "
            "<output-dir>/_llm_request.lock so only one LLM request runs at a time."
        ),
    )
    parser.add_argument(
        "--llm-request-lock-stale-seconds",
        type=float,
        default=None,
        help="Seconds after which an abandoned LLM lock file is considered stale. Defaults to 7200.",
    )
    parser.add_argument("--max-llm-iterations", type=int, default=5)
    parser.add_argument("--min-llm-iterations", type=int, default=3)
    parser.add_argument("--min-evaluated-candidates-before-stop", type=int, default=6)
    parser.add_argument("--min-candidates-per-iteration", type=int, default=2)
    parser.add_argument("--target-candidates-per-iteration", type=int, default=3)
    parser.add_argument("--max-candidates-per-iteration", type=int, default=3)
    parser.add_argument(
        "--candidate-workers",
        type=int,
        default=None,
        help=(
            "Number of worker processes for candidate calibration inside each LLM iteration. "
            "Defaults to serial unless HYDROAGENT_CANDIDATE_WORKERS or HYDROAGENT_MAX_WORKERS is set."
        ),
    )
    parser.add_argument(
        "--basin-workers",
        type=int,
        default=None,
        help=(
            "Number of worker processes for batch basin experiments. Defaults to serial unless "
            "HYDROAGENT_EXPERIMENT_BASIN_WORKERS or HYDROAGENT_MAX_WORKERS is set."
        ),
    )
    parser.add_argument("--kg-points", type=int, default=24)
    parser.add_argument("--power-points", type=int, default=18)
    parser.add_argument("--control-points", type=int, default=10)
    parser.add_argument("--max-calibrated-parameters", type=int, default=16)
    parser.add_argument("--max-search-evaluations", type=int, default=2000)
    parser.add_argument(
        "--reuse-baseline-candidate-result",
        type=Path,
        default=None,
        help=(
            "Path to an existing baseline candidate_result.json or its directory. "
            "Useful when the baseline was already calibrated in HBVbaseline outputs."
        ),
    )
    parser.add_argument(
        "--resume-existing",
        action="store_true",
        help=(
            "Resume from existing output-dir candidates and memory.json. This is now the default "
            "workflow; the flag is kept for explicitness."
        ),
    )
    parser.add_argument(
        "--fresh-run",
        action="store_true",
        help="Disable resume-first behavior and start from scratch in the chosen output directory.",
    )
    parser.add_argument(
        "--followup-instruction",
        default=None,
        help=(
            "Optional basin-specific instruction injected into the LLM run context. Use this for "
            "targeted follow-up searches after diagnosing previous rounds."
        ),
    )
    parser.add_argument(
        "--followup-instruction-file",
        type=Path,
        default=None,
        help="Optional UTF-8 text file containing a basin-specific follow-up instruction.",
    )
    args = parser.parse_args()
    followup_instruction = args.followup_instruction
    if args.followup_instruction_file is not None:
        file_instruction = args.followup_instruction_file.read_text(encoding="utf-8").strip()
        followup_instruction = (
            f"{followup_instruction}\n\n{file_instruction}"
            if followup_instruction
            else file_instruction
        )

    budget = CalibrationBudget(
        kg_points=args.kg_points,
        power_points=args.power_points,
        control_points=args.control_points,
        max_calibrated_parameters=args.max_calibrated_parameters,
        max_search_evaluations=args.max_search_evaluations,
    )
    periods = {
        "warmup_start": args.warmup_start,
        "calibration_start": args.calibration_start,
        "calibration_end": args.calibration_end,
        "development_start": args.development_start,
        "development_end": args.development_end,
        "final_test_start": args.final_test_start,
        "final_test_end": args.final_test_end,
    }
    resume_existing = args.resume_existing or not args.fresh_run
    basin_ids = _resolve_basin_ids(args.basin_id, args.basin_ids, args.basin_file)
    if len(basin_ids) > 1:
        batch_summary = run_batch_experiment(
            args.output_dir,
            basin_ids=basin_ids,
            seed=args.seed,
            budget=budget,
            agent_mode=args.agent,
            llm_model=args.llm_model,
            llm_call_mode=args.llm_call_mode,
            llm_api_mode=args.llm_api_mode,
            llm_response_format=args.llm_response_format,
            max_llm_iterations=args.max_llm_iterations,
            min_llm_iterations=args.min_llm_iterations,
            min_evaluated_candidates_before_stop=args.min_evaluated_candidates_before_stop,
            min_candidates_per_iteration=args.min_candidates_per_iteration,
            target_candidates_per_iteration=args.target_candidates_per_iteration,
            max_candidates_per_iteration=args.max_candidates_per_iteration,
            candidate_workers=args.candidate_workers,
            basin_workers=args.basin_workers,
            data_mode=args.data_mode,
            camels_root=args.camels_root,
            forcing_product=args.forcing_product,
            periods=periods,
            reuse_baseline_candidate_result=args.reuse_baseline_candidate_result,
            resume_existing=resume_existing,
            followup_instruction=followup_instruction,
            llm_timeout_seconds=args.llm_timeout_seconds,
            llm_max_retries=args.llm_max_retries,
            llm_retry_initial_seconds=args.llm_retry_initial_seconds,
            llm_retry_max_seconds=args.llm_retry_max_seconds,
            llm_json_repair_attempts=args.llm_json_repair_attempts,
            llm_request_lock_path=args.llm_request_lock_path,
            llm_request_lock_stale_seconds=args.llm_request_lock_stale_seconds,
        )
        print("Hydro DSL HBV v0.3.2 batch complete")
        print(f"Output root: {args.output_dir}")
        print(f"Basin count: {batch_summary['basin_count']}")
        print(f"Successful basins: {batch_summary.get('successful_basin_count', batch_summary['basin_count'])}")
        print(f"Failed basins: {batch_summary.get('failed_basin_count', 0)}")
        print(f"Basin workers: {batch_summary['parallel']['basin_workers']}")
        print(f"LLM request lock: {batch_summary['parallel'].get('llm_request_lock_path', '')}")
        for row in batch_summary["basins"]:
            if row.get("status") == "failed":
                print(
                    "{basin_id}: FAILED {error_type}: {error}".format(
                        **row
                    )
                )
            else:
                print(
                    "{basin_id}: baseline_dev={baseline_development_score:.6f}, "
                    "best_dev={best_development_score:.6f}, baseline_final={baseline_final_test_score:.6f}, "
                    "best_final={best_final_test_score:.6f}, best={best_candidate_id}, accepted={accepted}".format(
                        **row
                    )
                )
        print(f"Batch metrics CSV: {args.output_dir / 'batch_metrics_summary.csv'}")
        return

    summary = run_experiment(
        args.output_dir,
        seed=args.seed,
        budget=budget,
        agent_mode=args.agent,
        llm_model=args.llm_model,
        llm_call_mode=args.llm_call_mode,
        llm_api_mode=args.llm_api_mode,
        llm_response_format=args.llm_response_format,
        max_llm_iterations=args.max_llm_iterations,
        min_llm_iterations=args.min_llm_iterations,
        min_evaluated_candidates_before_stop=args.min_evaluated_candidates_before_stop,
        min_candidates_per_iteration=args.min_candidates_per_iteration,
        target_candidates_per_iteration=args.target_candidates_per_iteration,
        max_candidates_per_iteration=args.max_candidates_per_iteration,
        candidate_workers=args.candidate_workers,
        data_mode=args.data_mode,
        camels_root=args.camels_root,
        basin_id=basin_ids[0],
        forcing_product=args.forcing_product,
        periods=periods,
        reuse_baseline_candidate_result=args.reuse_baseline_candidate_result,
        resume_existing=resume_existing,
        followup_instruction=followup_instruction,
        llm_timeout_seconds=args.llm_timeout_seconds,
        llm_max_retries=args.llm_max_retries,
        llm_retry_initial_seconds=args.llm_retry_initial_seconds,
        llm_retry_max_seconds=args.llm_retry_max_seconds,
        llm_json_repair_attempts=args.llm_json_repair_attempts,
        llm_request_lock_path=args.llm_request_lock_path,
        llm_request_lock_stale_seconds=args.llm_request_lock_stale_seconds,
    )
    baseline = next(
        row for row in summary["leaderboard"] if row["candidate_id"] == summary["decision"]["baseline_candidate_id"]
    )
    best = next(
        row for row in summary["leaderboard"] if row["candidate_id"] == summary["decision"]["best_candidate_id"]
    )
    print("Hydro DSL HBV v0.3.2 POC complete")
    print(f"Output: {args.output_dir}")
    print(f"Agent mode: {summary['agent_mode']}")
    print(f"LLM model: {summary['llm_model']}")
    print(f"LLM call mode: {summary['llm_call_mode']}")
    print(f"Data mode: {summary['data_mode']}")
    print(f"Basin ID: {summary['basin_id']}")
    print(f"Forcing product: {summary['forcing_product']}")
    print(f"Max LLM iterations: {summary['max_llm_iterations']}")
    print(f"Min LLM iterations before early stop: {summary['effective_min_llm_iterations']}")
    print(f"Min evaluated candidates before early stop: {summary['min_evaluated_candidates_before_stop']}")
    print(f"Candidate generation policy: {summary['candidate_generation_policy']}")
    print(f"Candidate workers: {summary['parallel']['candidate_workers']}")
    print(f"Evaluated non-baseline candidates: {summary['evaluated_non_baseline_candidate_count']}")
    print(f"Max calibrated parameters: {summary['budget']['max_calibrated_parameters']}")
    print(f"Max search evaluations: {summary['budget']['max_search_evaluations']}")
    print(f"Baseline dev score: {baseline['development_score']:.6f}")
    print(f"Best dev score: {best['development_score']:.6f} ({best['candidate_id']})")
    print(f"Best change type: {best.get('change_type', '')}")
    print(f"Best target modules: {best.get('target_modules', '')}")
    print(f"Best complexity change: {best.get('complexity_change', '')}")
    print(f"Best candidate mode: {best.get('candidate_mode', '')}")
    print(f"Best DSL contract: {best.get('dsl_contract_version', '')}")
    print(f"Best code path: {best['code_path']}")
    print(f"Best final-test score: {best['final_test_score']:.6f}")
    print("")
    print("Selected detailed metrics:")
    _print_selected_metrics(summary["selected_metrics"])
    print(f"Metrics CSV: {args.output_dir / 'metrics_summary.csv'}")
    print(f"Selected metrics CSV: {args.output_dir / 'selected_metrics.csv'}")
    print(f"LLM stop reason: {summary['decision']['llm_stop_reason']}")
    print(f"Accepted: {summary['decision']['accepted']}")


def _resolve_basin_ids(default_basin_id: str, basin_ids: str | None, basin_file: Path | None) -> list[str]:
    resolved: list[str] = []
    if basin_file is not None:
        resolved.extend(
            line.strip()
            for line in basin_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    if basin_ids:
        resolved.extend(item.strip() for item in basin_ids.split(",") if item.strip())
    if not resolved:
        resolved.append(default_basin_id)
    return [item.zfill(8) for item in resolved]


def _print_selected_metrics(rows: list[dict]) -> None:
    header = (
        "role split mode dsl change_type target_modules complexity score KGE NSE logNSE PBIAS lowBias highBias recession candidate"
    )
    print(header)
    for row in rows:
        print(
            "{role} {split} {mode} {dsl} {change_type} {target_modules} {complexity} "
            "{score:.6f} {kge:.6f} {nse:.6f} {lognse:.6f} "
            "{pbias:.6f} {low:.6f} {high:.6f} {recession:.6f} {candidate}".format(
                role=row["model_role"],
                split=row["split"],
                mode=row.get("candidate_mode", ""),
                dsl=row.get("dsl_contract_version", "") or "none",
                change_type=row.get("change_type", ""),
                target_modules=row.get("target_modules", ""),
                complexity=row.get("complexity_change", ""),
                score=float(row["development_score"]),
                kge=float(row["KGE"]),
                nse=float(row["NSE"]),
                lognse=float(row["logNSE"]),
                pbias=float(row["PBIAS_percent"]),
                low=float(row["low_flow_bias_percent"]),
                high=float(row["high_flow_bias_percent"]),
                recession=float(row["recession_slope_relative_error"]),
                candidate=row["candidate_id"],
            )
        )


if __name__ == "__main__":
    main()

