#!/usr/bin/env python3
"""Prepare, run and collect an explicit Gammapy point-source campaign.

Use the installed v2dl5 environment. Preparation never submits or analyses data.
"""

import argparse
import copy
import hashlib
import json
import math
import shlex
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from argparse import Namespace
from pathlib import Path

import yaml
from astropy.table import Table

SOURCES = Path(__file__).resolve().parent


def digest(path):
    """Hash an input file without changing it."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(path):
    """Preserve order, remove duplicates and reject annotated science records."""
    runs, duplicates = [], []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        value = line.split("#", 1)[0].strip()
        if not value:
            continue
        if not value.isdecimal() or int(value) <= 0:
            raise ValueError(f"Invalid run record {path}:{number}: {value}")
        run = int(value)
        (duplicates if run in runs else runs).append(run)
    if not runs:
        raise ValueError(f"Empty run list: {path}")
    return runs, duplicates


def available_cuts(dl3_base):
    """List cut stores present under a DL3 release and analysis directory."""
    prefix = "dl3_pointlike_"
    return sorted(
        path.name.removeprefix(prefix)
        for path in Path(dl3_base).glob(f"{prefix}*")
        if path.is_dir()
    )


def make_index_store(dl3_path, index_path, indexer, obs_ids=None):
    """Build campaign-local Gammapy indexes for an existing V2DL3 store."""
    index_path.mkdir(parents=True, exist_ok=True)
    if obs_ids is None:
        input_path = dl3_path
        print(f"Indexing all DL3 files under {dl3_path} into {index_path}...", flush=True)
    else:
        run_list = index_path / "_selected_runs.txt"
        run_list.write_text("".join(f"{obs_id}\n" for obs_id in sorted(obs_ids)))
        input_path = dl3_path
        print(
            f"Indexing files for {len(obs_ids)} requested run IDs under {dl3_path} "
            f"into {index_path}...",
            flush=True,
        )
    command = [
        indexer,
        "--folder_location",
        str(input_path),
        "--index_file_dir",
        str(index_path),
    ]
    if obs_ids is not None:
        command.extend(["--run_list", str(run_list)])
    started = time.monotonic()
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise ValueError(f"Cannot run V2DL3 indexer {indexer!r}: {exc}") from exc
    for output_text in (result.stdout, result.stderr):
        if output_text:
            print(output_text.rstrip(), flush=True)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise ValueError(f"V2DL3 index generation failed for {dl3_path}: {detail}")
    missing = [
        name
        for name in ("hdu-index.fits.gz", "obs-index.fits.gz")
        if not (index_path / name).is_file()
    ]
    if missing:
        detail = (result.stderr or result.stdout).strip()
        message = f"V2DL3 indexer did not create {', '.join(missing)} for {dl3_path}"
        if detail:
            message += f": {detail}"
        raise ValueError(message)
    print(f"Indexing complete for {dl3_path} ({time.monotonic() - started:.1f} s).", flush=True)


def load_data_store(path):
    """Load a generated campaign index with Gammapy."""
    from gammapy.data import DataStore

    return DataStore.from_dir(path)


def validate_configuration(args):
    """Validate a generated job configuration with V2DL5."""
    from v2dl5.configuration import configuration

    return configuration(args)


def prepare(args):
    """Prepare normalized selections and jobs using TARGET.txt source names."""
    workers = getattr(args, "workers", 2)
    if workers < 1:
        raise ValueError("--workers must be at least 1")
    output = Path(args.output).resolve()
    if output.exists():
        raise FileExistsError(output)
    dl3_base = Path(args.dl3_base).resolve()
    cuts = list(dict.fromkeys(args.cuts or available_cuts(dl3_base)))
    if not cuts:
        raise ValueError(f"No dl3_pointlike_* cut stores found under {dl3_base}")
    output.mkdir(parents=True, exist_ok=False)
    template = Path(args.config).resolve()
    base_config = yaml.safe_load(template.read_text())
    targets = [
        s
        for s in (SOURCES / "TARGETS.dat").read_text().splitlines()
        if s.strip() and not s.startswith("#")
    ]
    unknown = set(args.source or []) - set(targets)
    if unknown:
        raise ValueError(f"Unknown sources: {sorted(unknown)}")
    reference = None
    if args.reference:
        reference = json.loads((Path(args.reference) / "manifest.json").read_text())
    selected_obs_ids = None
    if args.source:
        selected_obs_ids = set()
        for source in args.source:
            for runlist in (SOURCES / source).glob("runlist_releaseTesting*.dat"):
                if "runs_with_problems" in runlist.stem:
                    continue
                try:
                    runs, _duplicates = normalize(runlist)
                    if reference is not None:
                        matches = [
                            item
                            for item in reference["selections"]
                            if item["source"] == source and item["selection"] == runlist.stem
                        ]
                        common = set(matches[0].get("runs", [])) if matches else set()
                        runs = [run for run in runs if run in common]
                    selected_obs_ids.update(runs)
                except ValueError:
                    continue

    def prepare_cut(item):
        cut_number, cut = item
        dl3_path = dl3_base / f"dl3_pointlike_{cut}"
        index_path = output / "datastores" / f"dl3_pointlike_{cut}"
        print(f"Preparing cut {cut} ({cut_number}/{len(cuts)})", flush=True)
        try:
            make_index_store(dl3_path, index_path, args.indexer, selected_obs_ids)
            store = load_data_store(index_path)
            available = set(map(int, store.obs_table["OBS_ID"]))
            for hdu_type in ("events", "gti", "aeff", "edisp"):
                matching = store.hdu_table[store.hdu_table["HDU_TYPE"] == hdu_type]
                available &= {
                    int(row["OBS_ID"])
                    for row in matching
                    if (index_path / str(row["FILE_DIR"]) / str(row["FILE_NAME"])).is_file()
                }
            print(
                f"Indexed {len(available)} observations with required event, GTI, effective-area "
                f"and energy-dispersion files for cut {cut}.",
                flush=True,
            )
            return index_path, available, ""
        except (OSError, ValueError, KeyError, IndexError) as exc:
            print(f"Index preparation failed for cut {cut}: {exc}", flush=True)
            return index_path, set(), str(exc)

    print(f"Preparing campaign with up to {workers} workers", flush=True)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        stores = dict(zip(cuts, executor.map(prepare_cut, enumerate(cuts, start=1))))
    indexed_stores = {cut: str(store[0]) for cut, store in stores.items()}
    selected_targets = [source for source in targets if not args.source or source in args.source]

    def prepare_source(source):
        jobs, selections = [], []
        target_path = SOURCES / source / "TARGET.txt"
        target = target_path.read_text().strip() if target_path.exists() else source
        if not target:
            raise ValueError(f"Empty target name: {target_path}")
        seen = {}
        for runlist in sorted((SOURCES / source).glob("runlist_releaseTesting*.dat")):
            selection = runlist.stem
            if "runs_with_problems" in selection:
                selections.append(
                    {
                        "source": source,
                        "selection": selection,
                        "status": "diagnostic_only",
                        "original": str(runlist),
                        "sha256": digest(runlist),
                    }
                )
                continue
            try:
                runs, duplicates = normalize(runlist)
                if reference is not None:
                    matches = [
                        item
                        for item in reference["selections"]
                        if item["source"] == source and item["selection"] == selection
                    ]
                    common = set(matches[0].get("runs", [])) if matches else set()
                    runs = [run for run in runs if run in common]
                    if not runs:
                        raise ValueError("No common runs with reference selection")
                error = ""
            except ValueError as exc:
                runs, duplicates, error = [], [], str(exc)
            print(
                f"Preparing selection {source}/{selection} ({len(runs)} requested runs).",
                flush=True,
            )
            selection_dir = output / "selections" / source
            selection_dir.mkdir(parents=True, exist_ok=True)
            normalized = selection_dir / runlist.name
            normalized.write_text("".join(f"{run}\n" for run in runs))
            selections.append(
                {
                    "source": source,
                    "selection": selection,
                    "original": str(runlist),
                    "sha256": digest(runlist),
                    "runs": runs,
                    "removed_duplicates": duplicates,
                    "overlaps": {key: len(set(runs) & ids) for key, ids in seen.items()},
                    "status": "invalid_run_list" if error else "normalized",
                }
            )
            seen[selection] = set(runs)
            for cut, (store_path, available, store_error) in stores.items():
                directory = output / args.release / args.analysis_type / cut / source / selection
                directory.mkdir(parents=True)
                # Runs missing from the store are skipped by v2dl5 and reported, not blocking.
                missing = sorted(set(runs) - available)
                reason = error or store_error or ("" if set(runs) - set(missing) else
                                                  "No requested run in DL3 store")
                config = copy.deepcopy(base_config)
                config["observations"]["datastore"] = str(store_path)
                if getattr(args, "cache", None):
                    config["datasets"]["cache_dir"] = str(Path(args.cache).resolve())
                config["on_region"] = {"target": target}
                config_path = directory / "config.yaml"
                config_path.write_text(yaml.safe_dump(config, sort_keys=False))
                result = directory / "result"
                if not reason:
                    try:
                        validate_configuration(
                            Namespace(
                                config=str(config_path),
                                run_list=str(normalized),
                                output_dir=str(result),
                            )
                        )
                    except (ValueError, TypeError, KeyError) as exc:
                        reason = str(exc)
                command = [
                    sys.executable,
                    "-m",
                    "v2dl5.scripts.reflected_region_analysis",
                    "--run_list",
                    str(normalized),
                    "--config",
                    str(config_path),
                    "--output_dir",
                    str(result),
                    "--resume",
                ]
                if not args.plots:
                    command.append("--no-plots")
                worker = directory / "run.sh"
                worker.write_text(
                    "#!/bin/bash\nset -euo pipefail\nexport MPLBACKEND=Agg\nexec "
                    + shlex.join(command)
                    + "\n"
                )
                worker.chmod(0o755)
                if not reason:
                    (directory / "job.sub").write_text(
                        f'executable = "{worker}"\n'
                        f'output = "{directory}/worker.out"\n'
                        f'error = "{directory}/worker.err"\n'
                        f'log = "{directory}/worker.log"\n'
                        "request_memory = 8GB\nrequest_disk = 5GB\ngetenv = True\nqueue\n"
                    )
                jobs.append(
                    {
                        "source": source,
                        "selection": selection,
                        "cut": cut,
                        "release": args.release,
                        "analysis_type": args.analysis_type,
                        "status": "blocked" if reason else "ready",
                        "reason": reason,
                        "requested": len(runs),
                        "missing": missing,
                        "command": command,
                        "result": str(result),
                        "worker": str(worker),
                    }
                )
        return jobs, selections

    jobs, selections = [], []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for number, (source_jobs, source_selections) in enumerate(
            executor.map(prepare_source, selected_targets), start=1
        ):
            jobs.extend(source_jobs)
            selections.extend(source_selections)
            print(f"Prepared target {number}/{len(selected_targets)}", flush=True)
    manifest = {
        "reference": args.reference,
        "release": args.release,
        "analysis_type": args.analysis_type,
        "cuts": cuts,
        "index_scope": "selected_runs" if selected_obs_ids is not None else "all_files",
        "indexed_run_ids": sorted(selected_obs_ids) if selected_obs_ids is not None else None,
        "datastores": indexed_stores,
        "template_sha256": digest(template),
        "runner_sha256": digest(Path(__file__)),
        "selections": selections,
        "jobs": jobs,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    collect(output)
    print(
        f"Prepared {len(jobs)} jobs, "
        f"{sum(job['status'] == 'ready' for job in jobs)} ready: {output}"
    )


DETECTION_THRESHOLD = 5.0
COLUMNS = (
    "ontime_h", "n_on", "n_off", "alpha", "excess", "significance",
    "index", "index_err", "amplitude", "amplitude_err",
)


def _load_yaml(path):
    """Read a YAML product; absent or unreadable files give an empty dictionary."""
    try:
        return yaml.safe_load(Path(path).read_text()) or {}
    except (OSError, yaml.YAMLError):
        return {}


def read_result(result):
    """Read significance (all events) and power-law fit parameters of one job."""
    data = Path(result) / "data"
    significance = _load_yaml(data / "significance.yaml")
    values = dict.fromkeys(COLUMNS, math.nan)
    values["ontime_h"] = significance.get("ontime_s", math.nan) / 3600.0
    for key in ("n_on", "n_off", "alpha", "excess", "significance"):
        values[key] = float(significance.get(key, math.nan))
    fit_success = bool(_load_yaml(data / "fit.yaml").get("success", False))
    if fit_success:
        for component in _load_yaml(data / "models.yaml").get("components", []):
            for parameter in component.get("spectral", {}).get("parameters", []):
                if parameter["name"] in ("index", "amplitude"):
                    values[parameter["name"]] = float(parameter["value"])
                    values[parameter["name"] + "_err"] = float(parameter.get("error", math.nan))
    return values, fit_success


def collect(output):
    """Summarize every declared job (ECSV and Markdown), including absent results."""
    output = Path(output)
    manifest = json.loads((output / "manifest.json").read_text())
    rows = []
    for job in manifest["jobs"]:
        state = _load_yaml(Path(job["result"]) / "status.json")  # JSON is valid YAML
        status = state.get("status", "not_run" if job["status"] == "ready" else job["status"])
        values, fit_success = read_result(job["result"])
        rows.append(
            (
                job["source"],
                job["selection"],
                job["cut"],
                job["release"],
                job["analysis_type"],
                status,
                job["requested"],
                state.get("accepted", 0),
                str(state.get("reason", job.get("reason", ""))),
                job["result"],
                fit_success,
                bool(values["significance"] >= DETECTION_THRESHOLD),
                *(values[key] for key in COLUMNS),
            )
        )
    table = Table(
        rows=rows,
        names=(
            "source", "selection", "cut", "release", "analysis_type", "status",
            "requested", "accepted", "reason", "result", "fit_success", "detected",
            *COLUMNS,
        ),
    )
    table["ontime_h"].unit = "h"
    for key in ("amplitude", "amplitude_err"):
        table[key].unit = "TeV-1 s-1 cm-2"
    table.write(output / "summary.ecsv", format="ascii.ecsv", overwrite=True)
    lines = [
        "# Gammapy point source checks",
        "",
        "Significance: Li & Ma (WStat sqrt(TS)) of all events in the ON/OFF (reflected) regions,",
        "summed over all runs; no energy range or safe-energy cut is applied.",
        "",
        "Spectrum: power law dN/dE = N0 (E / 1 TeV)^-index, forward-folded fit of the stacked runs",
        "in the safe energy range (effective area > 10% of maximum). Listed for detections only",
        f"(significance >= {DETECTION_THRESHOLD:g} and successful fit). N0 in 1e-12 TeV^-1 cm^-2 s^-1.",
        "",
        "Selections and cuts share events; do not combine their significances.",
        "",
        "| Source | Selection | Cut | Status | Runs (acc/req) | Ontime [h] | N_on | N_off | alpha "
        "| Excess | Significance | Index | N0 | Details |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in table:
        if row["detected"] and row["fit_success"]:
            index = f"{row['index']:.3f} ± {row['index_err']:.3f}"
            norm = f"{row['amplitude'] * 1e12:.3f} ± {row['amplitude_err'] * 1e12:.3f}"
        else:
            index = norm = "–"
        reason = str(row["reason"]).replace("|", "/").replace("\n", " ")
        lines.append(
            f"| {row['source']} | {row['selection']} | {row['cut']} | {row['status']} | "
            f"{row['accepted']}/{row['requested']} | {row['ontime_h']:.1f} | "
            f"{row['n_on']:.0f} | {row['n_off']:.0f} | {row['alpha']:.3f} | "
            f"{row['excess']:.1f} | {row['significance']:.1f} | {index} | {norm} | {reason} |"
        )
    (output / "report.md").write_text("\n".join(lines) + "\n")
    return table


def run_job(number, total, job):
    """Run one campaign job, keeping its output in its own log file."""
    label = f"{job['source']}/{job['selection']} [{job['cut']}]"
    result = Path(job["result"])
    log_path = result.parent / "v2dl5.log"
    print(f"[{number}/{total}] START {label}; log: {log_path}", flush=True)
    started = time.monotonic()
    try:
        with log_path.open("a") as log:
            process = subprocess.Popen(
                job["command"],
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            next_update = started + 60
            while process.poll() is None:
                time.sleep(min(5, max(0, next_update - time.monotonic())))
                now = time.monotonic()
                if process.poll() is None and now >= next_update:
                    print(
                        f"[{number}/{total}] RUNNING {label}; elapsed {now - started:.0f} s",
                        flush=True,
                    )
                    next_update = now + 60
            returncode = process.returncode
        elapsed = time.monotonic() - started
        if returncode:
            message = f"exit {returncode}; see {log_path}"
        else:
            message = ""
    except OSError as exc:
        elapsed = time.monotonic() - started
        returncode = 1
        message = f"could not start job: {exc}"
    return number, label, elapsed, returncode, message


def compare(current, reference):
    """Compare significance and power-law parameters of matched jobs of two campaigns."""
    current, reference = Path(current), Path(reference)
    new, old = collect(current), collect(reference)
    keys = ("source", "selection", "cut", "analysis_type")
    old_rows = {tuple(row[key] for key in keys): row for row in old}
    rows = []
    for row in new:
        other = old_rows.get(tuple(row[key] for key in keys))
        ratio = delta_index = norm_ratio = math.nan
        if other is None:
            reason = "No reference job"
        else:
            reason = "" if row["accepted"] == other["accepted"] else "Different accepted runs"
            if other["significance"] > 0:
                ratio = row["significance"] / other["significance"]
            if row["fit_success"] and other["fit_success"]:
                delta_index = row["index"] - other["index"]
                norm_ratio = row["amplitude"] / other["amplitude"]
        rows.append(tuple(row[key] for key in keys) + (ratio, delta_index, norm_ratio, reason))
    Table(
        rows=rows,
        names=(*keys, "significance_ratio", "index_difference", "amplitude_ratio", "reason"),
    ).write(current / "comparison.ecsv", format="ascii.ecsv", overwrite=True)


def main():
    """Campaign command line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument(
        "--workers", "-j", type=int, default=2,
        help="Maximum concurrent cut indexing or target preparation tasks (default: 2)",
    )
    prep.add_argument("--output", required=True, help="New campaign directory")
    prep.add_argument("--dl3-base", required=True)
    prep.add_argument("--release", required=True)
    prep.add_argument("--analysis-type", choices=["AP", "NN"], required=True)
    prep.add_argument(
        "--cuts",
        nargs="+",
        help="Cut names to prepare (default: discover every dl3_pointlike_* store)",
    )
    prep.add_argument(
        "--indexer",
        default="v2dl3-generate-index-file",
        help="V2DL3 index generation executable",
    )
    prep.add_argument("--source", action="append", help="Optional pilot source (repeatable)")
    prep.add_argument("--config", default=str(SOURCES / "ANALYSIS.v2dl5.reflected_region.yml"))
    prep.add_argument("--plots", action="store_true")
    prep.add_argument("--cache", help="Optional shared cache of identical per-run reductions")
    prep.add_argument("--reference", help="Restrict selections to intersection with this campaign")
    comp = commands.add_parser("compare")
    comp.add_argument("campaign")
    comp.add_argument("reference")
    run = commands.add_parser("run")
    run.add_argument("campaign")
    run.add_argument(
        "--workers",
        "-j",
        type=int,
        default=2,
        help="Maximum number of analysis jobs to run concurrently (default: 2)",
    )
    commands.add_parser("collect").add_argument("campaign")
    args = parser.parse_args()
    if args.action == "prepare":
        if args.workers < 1:
            parser.error("--workers must be at least 1")
        prepare(args)
    elif args.action == "compare":
        compare(args.campaign, args.reference)
    elif args.action == "collect":
        collect(args.campaign)
    else:
        if args.workers < 1:
            parser.error("--workers must be at least 1")
        manifest = json.loads((Path(args.campaign) / "manifest.json").read_text())
        jobs = manifest["jobs"]
        failed = False
        total = len(jobs)
        ready = []
        print(
            f"Running {total} campaign jobs from {args.campaign} "
            f"with up to {args.workers} workers",
            flush=True,
        )
        for number, job in enumerate(jobs, start=1):
            label = f"{job['source']}/{job['selection']} [{job['cut']}]"
            if job["status"] != "ready":
                failed = True
                print(
                    f"[{number}/{total}] SKIP {label}: {job.get('reason', 'not ready')}",
                    flush=True,
                )
            else:
                ready.append((number, job))
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = [
                executor.submit(run_job, number, total, job)
                for number, job in ready
            ]
            for future in as_completed(futures):
                number, label, elapsed, returncode, message = future.result()
                if returncode:
                    failed = True
                    print(
                        f"[{number}/{total}] FAILED {label}; {message}; "
                        f"after {elapsed:.1f} s",
                        flush=True,
                    )
                else:
                    print(
                        f"[{number}/{total}] DONE {label}; elapsed {elapsed:.1f} s",
                        flush=True,
                    )
        print("Collecting campaign results...", flush=True)
        collect(args.campaign)
        print(f"Campaign results updated: {args.campaign}/report.md", flush=True)
        sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
