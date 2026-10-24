#!/usr/bin/env python3
"""Compare Gammapy campaign results (summary.ecsv) with Eventdisplay anasum source test summaries.

Usage:
    python compare_anasum.py <campaign> <SourceTestSummary> [--version v491.0]
"""

import argparse
import math
import re
from pathlib import Path

from astropy.table import Table

LINE1 = re.compile(
    r"^(?P<version>v[\d.]+\w*): (?P<runs>\d+) runs .*?, (?P<minutes>[\d.]+) min, "
    r"Non: (?P<non>\d+), Noff: (?P<noff_scaled>[\d.]+) \(\s*(?P<noff>\d+), norm (?P<norm>[\d.]+)\)"
)
LINE2 = re.compile(
    r"^(?P<version>v[\d.]+\w*): (?P<sigma>-?[\d.]+) sigma, Rates:\s+(?P<rate>-?[\d.]+) \+/-\s+"
    r"(?P<rate_err>[\d.]+) gamma/min"
)


def read_reference(path, version):
    """Read one anasum results_<source>_<epoch>_<cut>.md entry for a given version."""
    values = {}
    for line in path.read_text().splitlines():
        for pattern in (LINE1, LINE2):
            match = pattern.match(line.strip())
            if match and match["version"] == version:
                values.update({k: float(v) for k, v in match.groupdict().items() if k != "version"})
    return values


def epoch(selection):
    """Map campaign selection names (runlist_releaseTesting_V6, ...TestingV5) to epochs."""
    name = selection.removeprefix("runlist_releaseTesting").lstrip("_")
    return name if name in ("V4", "V5", "V6", "all") else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign")
    parser.add_argument("reference")
    parser.add_argument("--version", default="v491.0")
    parser.add_argument("--fallback", default="v491.1", help="Version used if --version is absent")
    args = parser.parse_args()
    campaign, reference = Path(args.campaign), Path(args.reference)
    summary = Table.read(campaign / "summary.ecsv")
    rows = []
    for row in summary:
        ep = epoch(row["selection"])
        if ep is None:
            continue
        path = reference / row["source"] / f"results_{row['source']}_{ep}_{row['cut']}.md"
        ref, ref_version = {}, ""
        for version in (args.version, args.fallback):
            ref = read_reference(path, version) if path.exists() else {}
            if "sigma" in ref:
                ref_version = version
                break
        minutes = row["ontime_h"] * 60.0
        rate = row["excess"] / minutes if minutes > 0 else math.nan
        rows.append(
            (
                row["source"],
                ep,
                row["cut"],
                row["status"],
                ref_version,
                row["accepted"],
                ref.get("runs", math.nan),
                minutes,
                ref.get("minutes", math.nan),
                row["n_on"],
                ref.get("non", math.nan),
                row["n_off"] * row["alpha"],
                ref.get("noff_scaled", math.nan),
                row["significance"],
                ref.get("sigma", math.nan),
                rate,
                ref.get("rate", math.nan),
                ref.get("rate_err", math.nan),
                row["index"] if row["detected"] and row["fit_success"] else math.nan,
                row["index_err"] if row["detected"] and row["fit_success"] else math.nan,
                row["amplitude"] if row["detected"] and row["fit_success"] else math.nan,
            )
        )
    names = (
        "source",
        "epoch",
        "cut",
        "status",
        "ref_version",
        "runs",
        "runs_ref",
        "ontime_min",
        "ontime_min_ref",
        "n_on",
        "n_on_ref",
        "background",
        "background_ref",
        "significance",
        "significance_ref",
        "rate",
        "rate_ref",
        "rate_err_ref",
        "index",
        "index_err",
        "amplitude",
    )
    table = Table(rows=rows, names=names)
    table.write(campaign / "comparison_anasum.ecsv", format="ascii.ecsv", overwrite=True)

    def ratio(a, b):
        return a / b if b and math.isfinite(a) and math.isfinite(b) and b != 0 else math.nan

    lines = [
        f"# Gammapy (V2DL5) vs. Eventdisplay anasum ({args.version})",
        "",
        "Gammapy: reflected regions, all events (no energy cut), Li & Ma (WStat).",
        "Gamma rate = excess / ontime. Spectra (power law, 1 TeV) for Gammapy detections only;",
        "the anasum summaries contain no spectral fits.",
        f"Reference values marked * are from {args.fallback} ({args.version} entry absent).",
        "",
        "| Source | Epoch | Cut | Runs G/A | Ontime [min] G/A | N_on G/A | Bkg G/A "
        "| Sig. G/A | Sig. ratio | Rate G/A [γ/min] | Rate ratio | Index (G) | N0 (G) [1e-12] |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in table:
        display_epoch = f"{r['epoch']}*" if r["ref_version"] == args.fallback else r["epoch"]
        spec = (
            (f"{r['index']:.2f} ± {r['index_err']:.2f}", f"{r['amplitude'] * 1e12:.3g}")
            if math.isfinite(r["index"])
            else ("–", "–")
        )
        lines.append(
            f"| {r['source']} | {display_epoch} | {r['cut']} | "
            f"{r['runs']}/{r['runs_ref']:.0f} | "
            f"{r['ontime_min']:.0f}/{r['ontime_min_ref']:.0f} | "
            f"{r['n_on']:.0f}/{r['n_on_ref']:.0f} | "
            f"{r['background']:.1f}/{r['background_ref']:.1f} | "
            f"{r['significance']:.1f}/{r['significance_ref']:.1f} | "
            f"{ratio(r['significance'], r['significance_ref']):.2f} | "
            f"{r['rate']:.3f}/{r['rate_ref']:.3f} | {ratio(r['rate'], r['rate_ref']):.2f} | "
            f"{spec[0]} | {spec[1]} |"
        )
    (campaign / "comparison_anasum.md").write_text("\n".join(lines) + "\n")
    print(f"Wrote {campaign / 'comparison_anasum.md'} ({len(table)} rows)")


if __name__ == "__main__":
    main()
