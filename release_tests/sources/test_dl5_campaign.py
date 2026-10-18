"""Checks for campaign selection accounting without production DL3 access."""

import json
from argparse import Namespace
from pathlib import Path

import pytest
import source_checks
import yaml
from astropy.table import Table


def test_normalize_removes_duplicates_but_rejects_annotations(tmp_path):
    path = tmp_path / "runs.dat"
    path.write_text("# selected\n7\n8\n7\n")
    assert source_checks.normalize(path) == ([7, 8], [7])
    path.write_text("7 - missing VPM\n")
    with pytest.raises(ValueError, match="Invalid run record"):
        source_checks.normalize(path)


def test_prepare_accounts_for_science_diagnostic_and_missing_runs(tmp_path, monkeypatch):
    sources = tmp_path / "sources"
    (sources / "A").mkdir(parents=True)
    (sources / "TARGETS.dat").write_text("A\n")
    (sources / "A/runlist_releaseTesting_V6.dat").write_text("7\n8\n7\n")
    (sources / "A/runlist_releaseTestingV5.runs_with_problems.dat").write_text("9 bad\n")
    registry = sources / "registry.yml"
    registry.write_text(
        yaml.safe_dump({"sources": {"A": {"frame": "icrs", "lon": "100 deg", "lat": "20 deg"}}})
    )
    template = Path(source_checks.SOURCES) / "ANALYSIS.v2dl5.reflected_region.yml"
    monkeypatch.setattr(source_checks, "SOURCES", sources)

    datafile = tmp_path / "obs7.fits"
    datafile.touch()

    class Store:
        obs_table = Table({"OBS_ID": [7]})
        hdu_table = Table(
            {
                "OBS_ID": [7] * 4,
                "HDU_TYPE": ["events", "gti", "aeff", "edisp"],
                "FILE_DIR": [str(tmp_path)] * 4,
                "FILE_NAME": ["obs7.fits"] * 4,
            }
        )

    monkeypatch.setattr(source_checks.DataStore, "from_dir", lambda _path: Store())
    output = tmp_path / "campaign"
    source_checks.prepare(
        Namespace(
            output=str(output),
            registry=str(registry),
            config=str(template),
            source=None,
            reference=None,
            cuts=["moderate2tel"],
            dl3_base=str(tmp_path),
            release="v-test",
            analysis_type="AP",
            plots=False,
        )
    )
    manifest = json.loads((output / "manifest.json").read_text())
    assert len(manifest["jobs"]) == 1
    assert manifest["jobs"][0]["missing"] == [8]
    assert manifest["jobs"][0]["status"] == "blocked"
    science = next(item for item in manifest["selections"] if item["status"] == "normalized")
    assert science["runs"] == [7, 8]
    assert science["removed_duplicates"] == [7]
    assert any(item["status"] == "diagnostic_only" for item in manifest["selections"])
    assert len(Table.read(output / "summary.ecsv")) == 1
    with pytest.raises(FileExistsError):
        source_checks.prepare(Namespace(output=str(output)))
