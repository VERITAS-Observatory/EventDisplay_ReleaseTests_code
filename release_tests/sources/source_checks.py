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
from argparse import Namespace
from pathlib import Path

import yaml
from astropy.table import Table
from gammapy.data import DataStore
from v2dl5.configuration import configuration

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


def prepare(args):
    """Freeze normalized selections, numeric positions and eligible jobs."""
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    registry_path = Path(args.registry).resolve()
    registry = yaml.safe_load(registry_path.read_text())
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
    stores = {}
    for cut in args.cuts:
        path = Path(args.dl3_base).resolve() / f"dl3_pointlike_{cut}"
        try:
            store = DataStore.from_dir(path)
            available = set(map(int, store.obs_table["OBS_ID"]))
            for hdu_type in ("events", "gti", "aeff", "edisp"):
                matching = store.hdu_table[store.hdu_table["HDU_TYPE"] == hdu_type]
                available &= {
                    int(row["OBS_ID"])
                    for row in matching
                    if (path / str(row["FILE_DIR"]) / str(row["FILE_NAME"])).is_file()
                }
            stores[cut] = (path, available, "")
        except (OSError, ValueError, KeyError, IndexError) as exc:
            stores[cut] = (path, set(), str(exc))
    jobs, selections = [], []
    for source in targets:
        if args.source and source not in args.source:
            continue
        definition = registry["sources"].get(source, {})
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
                reason = error or definition.get("blocked", "")
                if "lon" not in definition or "lat" not in definition:
                    reason = reason or "Missing reviewed coordinates in registry"
                missing = sorted(set(runs) - available)
                reason = (
                    reason
                    or store_error
                    or (f"Missing observations/required HDUs: {missing}" if missing else "")
                )
                config = copy.deepcopy(base_config)
                config["observations"]["datastore"] = str(store_path)
                if getattr(args, "cache", None):
                    config["datasets"]["cache_dir"] = str(Path(args.cache).resolve())
                config.pop("on_region", None)
                config["on_region"] = {
                    key: definition[key]
                    for key in ("target", "frame", "lon", "lat")
                    if key in definition
                }
                exclusions = definition.get("regions_file")
                if exclusions:
                    regions_file = (registry_path.parent / exclusions).resolve()
                    config["datasets"]["exclusion_region"]["regions_file"] = str(regions_file)
                    if not regions_file.is_file():
                        reason = reason or f"Missing exclusions: {regions_file}"
                config_path = directory / "config.yaml"
                config_path.write_text(yaml.safe_dump(config, sort_keys=False))
                result = directory / "result"
                if not reason:
                    try:
                        configuration(
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
    manifest = {
        "reference": args.reference,
        "release": args.release,
        "analysis_type": args.analysis_type,
        "registry": registry,
        "registry_sha256": digest(registry_path),
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


def collect(output):
    """Include every declared job in ECSV and Markdown, including absent results."""
    output = Path(output)
    manifest = json.loads((output / "manifest.json").read_text())
    rows = []
    for job in manifest["jobs"]:
        status_path = Path(job["result"]) / "status.json"
        try:
            state = json.loads(status_path.read_text()) if status_path.exists() else job.copy()
            if state.get("status") == "complete":
                for product, checksum in state.get("products", {}).items():
                    if digest(Path(job["result"]) / product) != checksum:
                        raise ValueError(f"Changed product: {product}")
        except (OSError, ValueError) as exc:
            state = {"status": "invalid_products", "reason": str(exc)}
        flux = {}
        flux_path = Path(job["result"]) / "data" / "integral_flux.ecsv"
        if flux_path.exists() and state.get("status") != "invalid_products":
            try:
                flux = dict(Table.read(flux_path, format="ascii.ecsv")[0])
            except (OSError, ValueError, IndexError, KeyError) as exc:
                state = {"status": "invalid_products", "reason": str(exc)}
        numbers = [
            float(flux[key]) if key in flux else math.nan
            for key in ("e_min", "e_max", "flux", "flux_err", "flux_ul", "ts")
        ]
        rows.append(
            (
                job["source"],
                job["selection"],
                job["cut"],
                job["release"],
                job["analysis_type"],
                state.get("status", "not_run"),
                job["requested"],
                state.get("accepted", 0),
                state.get("reason", ""),
                job["result"],
                *numbers,
            )
        )
    table = Table(
        rows=rows,
        names=(
            "source",
            "selection",
            "cut",
            "release",
            "analysis_type",
            "status",
            "requested",
            "accepted",
            "reason",
            "result",
            "e_min",
            "e_max",
            "flux",
            "flux_err",
            "flux_ul",
            "ts",
        ),
    )
    for key in ("e_min", "e_max"):
        table[key].unit = "TeV"
    for key in ("flux", "flux_err", "flux_ul"):
        table[key].unit = "cm-2 s-1"
    table.write(output / "summary.ecsv", format="ascii.ecsv", overwrite=True)
    lines = [
        "# Gammapy point source checks",
        "",
        "Fluxes and one-sided 95% limits are in cm^-2 s^-1 for the listed effective TeV band.",
        "TS tests fixed-index normalization in that band; results use a point source hypothesis.",
        "Selections and cuts may share events; do not sum their exposure or significances.",
        "",
        (
            "| Source | Selection | Cut | Status | Accepted/requested | Band [TeV] | "
            "Flux | UL | TS | Details |"
        ),
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in table:
        reason = str(row["reason"]).replace("|", "/").replace("\n", " ")
        lines.append(
            f"| {row['source']} | {row['selection']} | {row['cut']} | {row['status']} | "
            f"{row['accepted']}/{row['requested']} | {row['e_min']:.6g}–{row['e_max']:.6g} | "
            f"{row['flux']:.3g} | {row['flux_ul']:.3g} | {row['ts']:.2f} | {reason} |"
        )
    (output / "report.md").write_text("\n".join(lines) + "\n")
    return table


def compare(current, reference):
    """Compare matched completed jobs without assigning independent-error significances."""
    current, reference = Path(current), Path(reference)
    new, old = collect(current), collect(reference)
    rows = []
    keys = ("source", "selection", "cut", "analysis_type")
    for row in new:
        matches = [other for other in old if all(row[key] == other[key] for key in keys)]
        reason, delta = "No reference job", math.nan
        if len(matches) == 1:
            other = matches[0]
            reason = "Incomplete result"
            if row["status"] == other["status"] == "complete":
                new_dir, old_dir = Path(row["result"]), Path(other["result"])
                new_ids = set(Table.read(new_dir / "data/runs.ecsv")["name"])
                old_ids = set(Table.read(old_dir / "data/runs.ecsv")["name"])
                configs = [
                    yaml.safe_load((directory / "config.resolved.yaml").read_text())
                    for directory in (new_dir, old_dir)
                ]
                # Store path and target display name may differ; scientific settings must match.
                for config in configs:
                    config.pop("observations", None)
                    config.pop("run_list", None)
                    config.pop("output_dir", None)
                    config["on_region"].pop("target", None)
                    config["datasets"].pop("cache_dir", None)
                if new_ids != old_ids:
                    reason = (
                        "Different accepted runs; prepare common-run campaigns for both releases"
                    )
                elif configs[0] != configs[1]:
                    reason = "Different scientific settings"
                elif row["e_min"] != other["e_min"] or row["e_max"] != other["e_max"]:
                    reason = "Different flux bands"
                elif math.isfinite(other["flux"]) and other["flux"] > 0:
                    delta = row["flux"] / other["flux"] - 1
                    reason = (
                        "Matched; correlated releases: investigate changes; "
                        "independent-error pulls are not applicable"
                    )
        rows.append(tuple(row[key] for key in keys) + (delta, reason))
    Table(rows=rows, names=(*keys, "flux_fractional_change", "reason")).write(
        current / "comparison.ecsv", format="ascii.ecsv", overwrite=True
    )


def main():
    """Campaign command line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--output", required=True, help="New campaign directory")
    prep.add_argument("--dl3-base", required=True)
    prep.add_argument("--release", required=True)
    prep.add_argument("--analysis-type", choices=["AP", "NN"], required=True)
    prep.add_argument("--cuts", nargs="+", required=True)
    prep.add_argument("--source", action="append", help="Optional pilot source (repeatable)")
    prep.add_argument("--registry", default=str(SOURCES / "source_checks.yml"))
    prep.add_argument("--config", default=str(SOURCES / "ANALYSIS.v2dl5.reflected_region.yml"))
    prep.add_argument("--plots", action="store_true")
    prep.add_argument("--cache", help="Optional shared cache of identical per-run reductions")
    prep.add_argument("--reference", help="Restrict selections to intersection with this campaign")
    comp = commands.add_parser("compare")
    comp.add_argument("campaign")
    comp.add_argument("reference")
    for name in ("run", "collect"):
        command = commands.add_parser(name)
        command.add_argument("campaign")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args)
    elif args.action == "compare":
        compare(args.campaign, args.reference)
    elif args.action == "collect":
        collect(args.campaign)
    else:
        manifest = json.loads((Path(args.campaign) / "manifest.json").read_text())
        failed = any(job["status"] != "ready" for job in manifest["jobs"])
        for job in manifest["jobs"]:
            if job["status"] == "ready":
                result = Path(job["result"])
                with (result.parent / "v2dl5.log").open("a") as log:
                    failed |= (
                        subprocess.run(
                            job["command"],
                            stdout=log,
                            stderr=subprocess.STDOUT,
                            check=False,
                        ).returncode
                        != 0
                    )
        collect(args.campaign)
        sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
