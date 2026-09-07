from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from llm_hydro_structure_v032 import CalibrationBudget, run_hbv_baseline_batch  # noqa: E402
from llm_hydro_structure_v032.baseline_batch import DEFAULT_OUTPUT_DIR  # noqa: E402
from llm_hydro_structure_v032.paths import DEFAULT_CAMELS_ROOT  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run or collect baseline HBV CAMELS-US calibration results."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--camels-root", type=Path, default=DEFAULT_CAMELS_ROOT)
    parser.add_argument("--forcing-product", choices=["daymet", "maurer", "nldas"], default="daymet")
    parser.add_argument("--basin-ids", default=None, help="Comma-separated basin IDs.")
    parser.add_argument("--basin-file", type=Path, default=None, help="One basin ID per line.")
    parser.add_argument(
        "--all-basins",
        action="store_true",
        help="Discover and run all basins available for the selected forcing product.",
    )
    parser.add_argument(
        "--reuse-result-root",
        type=Path,
        action="append",
        default=[],
        help="Existing experiment output root containing basin_id/results.json directories.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild output records even when output-dir/basins/<id>/baseline_result.json exists.",
    )
    parser.add_argument("--warmup-start", default="1980-10-01")
    parser.add_argument("--calibration-start", default="1981-10-01")
    parser.add_argument("--calibration-end", default="1989-09-30")
    parser.add_argument("--development-start", default="1989-10-01")
    parser.add_argument("--development-end", default="1994-09-30")
    parser.add_argument("--final-test-start", default="1994-10-01")
    parser.add_argument("--final-test-end", default="1999-09-30")
    parser.add_argument("--kg-points", type=int, default=24)
    parser.add_argument("--power-points", type=int, default=18)
    parser.add_argument("--control-points", type=int, default=10)
    parser.add_argument("--max-calibrated-parameters", type=int, default=16)
    parser.add_argument("--max-search-evaluations", type=int, default=2000)
    parser.add_argument(
        "--max-workers",
        type=int,
        default=None,
        help=(
            "Number of basin calibration worker processes. Defaults to serial unless "
            "HYDROAGENT_BASELINE_BASIN_WORKERS or HYDROAGENT_MAX_WORKERS is set."
        ),
    )
    parser.add_argument("--sampling-seed", type=int, default=1107)
    parser.add_argument("--sceua-complexes", type=int, default=3)
    parser.add_argument("--sceua-complex-size", type=int, default=0)
    parser.add_argument("--sceua-evolutions-per-complex", type=int, default=2)
    parser.add_argument("--water-balance-tolerance", type=float, default=1.0e-6)
    args = parser.parse_args()

    budget = CalibrationBudget(
        kg_points=args.kg_points,
        power_points=args.power_points,
        control_points=args.control_points,
        max_calibrated_parameters=args.max_calibrated_parameters,
        max_search_evaluations=args.max_search_evaluations,
        sampling_seed=args.sampling_seed,
        sceua_complexes=args.sceua_complexes,
        sceua_complex_size=args.sceua_complex_size,
        sceua_evolutions_per_complex=args.sceua_evolutions_per_complex,
        water_balance_tolerance=args.water_balance_tolerance,
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
    basin_ids = _resolve_basin_ids(args.basin_ids, args.basin_file)
    manifest = run_hbv_baseline_batch(
        output_dir=args.output_dir,
        basin_ids=basin_ids,
        all_basins=args.all_basins,
        camels_root=args.camels_root,
        forcing_product=args.forcing_product,
        periods=periods,
        budget=budget,
        reuse_result_roots=args.reuse_result_root,
        skip_existing=not args.force,
        max_workers=args.max_workers,
    )
    print("HBV baseline batch complete")
    print(f"Output: {manifest['output_dir']}")
    print(f"Requested basins: {manifest['requested_basin_count']}")
    print(f"Completed records: {manifest['completed_basin_count']}")
    print(f"Basin workers: {manifest['parallel']['baseline_basin_workers']}")
    print(f"Status CSV: {manifest['files']['status']}")
    print(f"Metrics CSV: {manifest['files']['metrics']}")
    print(f"Parameters CSV: {manifest['files']['parameters_wide']}")
    print(f"Split CSV: {manifest['files']['splits']}")


def _resolve_basin_ids(basin_ids: str | None, basin_file: Path | None) -> list[str]:
    resolved: list[str] = []
    if basin_file is not None:
        resolved.extend(
            line.strip()
            for line in basin_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    if basin_ids:
        resolved.extend(item.strip() for item in basin_ids.split(",") if item.strip())
    return [item.zfill(8) for item in resolved]


if __name__ == "__main__":
    main()
