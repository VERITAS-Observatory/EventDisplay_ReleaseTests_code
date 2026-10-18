"""Checks for campaign selection accounting without production DL3 access."""

import json
import os
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

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
    monkeypatch.setattr(source_checks, "make_index_store", lambda *_args: None)

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

    monkeypatch.setattr(source_checks, "load_data_store", lambda _path: Store())
    output = tmp_path / "campaign"
    source_checks.prepare(
        Namespace(
            output=str(output),
            registry=str(registry),
            config=str(template),
            source=None,
            reference=None,
            cuts=["moderate2tel"],
            indexer="v2dl3-generate-index-file",
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


def test_prepare_indexes_all_discovered_cuts_for_all_sources(tmp_path, monkeypatch):
    sources = tmp_path / "sources"
    sources.mkdir()
    (sources / "TARGETS.dat").write_text("A\nB\n")
    for source in ("A", "B"):
        source_dir = sources / source
        source_dir.mkdir()
        (source_dir / "runlist_releaseTesting_V6.dat").write_text("7\n")
    registry = sources / "registry.yml"
    registry.write_text(
        yaml.safe_dump(
            {
                "sources": {
                    source: {"frame": "icrs", "lon": "100 deg", "lat": "20 deg"}
                    for source in ("A", "B")
                }
            }
        )
    )
    template = Path(source_checks.SOURCES) / "ANALYSIS.v2dl5.reflected_region.yml"
    monkeypatch.setattr(source_checks, "SOURCES", sources)

    dl3_base = tmp_path / "dl3"
    for cut in ("moderate2tel", "soft2tel"):
        cut_dir = dl3_base / f"dl3_pointlike_{cut}"
        cut_dir.mkdir(parents=True)
        (cut_dir / "7.fits").touch()

    generated = []

    def make_indexes(command, check, capture_output, text):
        assert not check and capture_output and text
        generated.append(command)
        index_dir = Path(command[command.index("--index_file_dir") + 1])
        index_dir.mkdir(parents=True, exist_ok=True)
        (index_dir / "hdu-index.fits.gz").touch()
        (index_dir / "obs-index.fits.gz").touch()
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(source_checks.subprocess, "run", make_indexes)

    def load_store(index_dir):
        cut = index_dir.name.removeprefix("dl3_pointlike_")
        file_path = dl3_base / f"dl3_pointlike_{cut}" / "7.fits"
        file_dir = os.path.relpath(file_path.parent, index_dir)
        return SimpleNamespace(
            obs_table=Table({"OBS_ID": [7]}),
            hdu_table=Table(
                {
                    "OBS_ID": [7] * 4,
                    "HDU_TYPE": ["events", "gti", "aeff", "edisp"],
                    "FILE_DIR": [file_dir] * 4,
                    "FILE_NAME": [file_path.name] * 4,
                }
            ),
        )

    monkeypatch.setattr(source_checks, "load_data_store", load_store)
    monkeypatch.setattr(source_checks, "validate_configuration", lambda _args: None)
    output = tmp_path / "campaign"
    source_checks.prepare(
        Namespace(
            output=str(output),
            registry=str(registry),
            config=str(template),
            source=None,
            reference=None,
            cuts=None,
            indexer="v2dl3-generate-index-file",
            dl3_base=str(dl3_base),
            release="v-test",
            analysis_type="AP",
            plots=False,
        )
    )

    manifest = json.loads((output / "manifest.json").read_text())
    assert len(generated) == 2
    assert {job["source"] for job in manifest["jobs"]} == {"A", "B"}
    assert {job["cut"] for job in manifest["jobs"]} == {"moderate2tel", "soft2tel"}
    assert all(job["status"] == "ready" for job in manifest["jobs"])
    for cut in ("moderate2tel", "soft2tel"):
        index_dir = output / "datastores" / f"dl3_pointlike_{cut}"
        assert (index_dir / "hdu-index.fits.gz").is_file()
        assert (index_dir / "obs-index.fits.gz").is_file()
        assert manifest["datastores"][cut] == str(index_dir)
        cut_jobs = [job for job in manifest["jobs"] if job["cut"] == cut]
        assert all(
            yaml.safe_load(Path(job["result"]).parent.joinpath("config.yaml").read_text())[
                "observations"
            ]["datastore"]
            == str(index_dir)
            for job in cut_jobs
        )
