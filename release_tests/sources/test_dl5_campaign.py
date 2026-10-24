"""Checks for campaign selection accounting without production DL3 access."""

import json
import os
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from threading import Barrier

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
    (sources / "A/TARGET.txt").write_text("Tycho SNR\n")
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
    assert manifest["jobs"][0]["status"] == "ready"  # v2dl5 skips and reports missing runs
    science = next(item for item in manifest["selections"] if item["status"] == "normalized")
    assert science["runs"] == [7, 8]
    assert science["removed_duplicates"] == [7]
    assert any(item["status"] == "diagnostic_only" for item in manifest["selections"])
    assert len(Table.read(output / "summary.ecsv")) == 1
    with pytest.raises(FileExistsError):
        source_checks.prepare(Namespace(output=str(output)))


@pytest.mark.parametrize("workers", [1, 2])
@pytest.mark.parametrize("failed_cut", [None, "soft2tel"])
def test_prepare_indexes_all_discovered_cuts_for_all_sources(
    tmp_path, monkeypatch, workers, failed_cut
):
    sources = tmp_path / "sources"
    sources.mkdir()
    (sources / "TARGETS.dat").write_text("A\nB\n")
    for source in ("A", "B"):
        source_dir = sources / source
        source_dir.mkdir()
        (source_dir / "runlist_releaseTesting_V6.dat").write_text("7\n")
        if source == "A":
            (source_dir / "TARGET.txt").write_text("Target A\n")
    template = Path(source_checks.SOURCES) / "ANALYSIS.v2dl5.reflected_region.yml"
    monkeypatch.setattr(source_checks, "SOURCES", sources)

    dl3_base = tmp_path / "dl3"
    for cut in ("moderate2tel", "soft2tel"):
        cut_dir = dl3_base / f"dl3_pointlike_{cut}"
        cut_dir.mkdir(parents=True)
        (cut_dir / "7.fits").touch()

    generated = []
    indexing = Barrier(2) if workers == 2 else None
    preparing = Barrier(2) if workers == 2 else None

    def make_indexes(command, check, capture_output, text):
        assert not check and capture_output and text
        if indexing:
            indexing.wait(timeout=5)
        generated.append(command)
        index_dir = Path(command[command.index("--index_file_dir") + 1])
        if index_dir.name == f"dl3_pointlike_{failed_cut}":
            return SimpleNamespace(returncode=1, stderr="Index failed", stdout="")
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
    validate = source_checks.validate_configuration

    def validate_in_parallel(args):
        if preparing:
            preparing.wait(timeout=5)
        return validate(args)

    monkeypatch.setattr(source_checks, "validate_configuration", validate_in_parallel)
    output = tmp_path / "campaign"
    source_checks.prepare(
        Namespace(
            workers=workers,
            output=str(output),
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
    assert [(job["source"], job["cut"]) for job in manifest["jobs"]] == [
        (source, cut) for source in ("A", "B") for cut in ("moderate2tel", "soft2tel")
    ]
    assert len(generated) == 2
    assert {job["source"] for job in manifest["jobs"]} == {"A", "B"}
    assert {job["cut"] for job in manifest["jobs"]} == {"moderate2tel", "soft2tel"}
    for job in manifest["jobs"]:
        if job["cut"] == failed_cut:
            assert job["status"] == "blocked"
            assert "Index failed" in job["reason"]
            assert not Path(job["worker"]).with_name("job.sub").exists()
        else:
            assert job["status"] == "ready"
            assert Path(job["worker"]).with_name("job.sub").exists()
    assert len(Table.read(output / "summary.ecsv")) == 4
    for job in manifest["jobs"]:
        config = yaml.safe_load(Path(job["result"]).parent.joinpath("config.yaml").read_text())
        expected_target = "Target A" if job["source"] == "A" else "B"
        assert config["on_region"] == {"target": expected_target}

    for cut in ("moderate2tel", "soft2tel"):
        index_dir = output / "datastores" / f"dl3_pointlike_{cut}"
        assert (index_dir / "hdu-index.fits.gz").is_file() == (cut != failed_cut)
        assert (index_dir / "obs-index.fits.gz").is_file() == (cut != failed_cut)
        assert manifest["datastores"][cut] == str(index_dir)
        cut_jobs = [job for job in manifest["jobs"] if job["cut"] == cut]
        assert all(
            yaml.safe_load(Path(job["result"]).parent.joinpath("config.yaml").read_text())[
                "observations"
            ]["datastore"]
            == str(index_dir)
            for job in cut_jobs
        )


@pytest.mark.parametrize("workers", [0, -1])
def test_prepare_rejects_invalid_workers_before_creating_output(tmp_path, workers):
    output = tmp_path / "campaign"
    with pytest.raises(ValueError, match="workers must be at least 1"):
        source_checks.prepare(Namespace(output=str(output), workers=workers))
    assert not output.exists()


@pytest.mark.parametrize("significance,fit_success,detected", [
    (7.5, True, True),
    (1.2, False, False),
])
def test_collect_reads_significance_and_power_law(tmp_path, significance, fit_success, detected):
    result = tmp_path / "result"
    (result / "data").mkdir(parents=True)
    (result / "status.json").write_text(json.dumps({"status": "complete", "accepted": 1}))
    (result / "data/significance.yaml").write_text(yaml.safe_dump(
        {"ontime_s": 3600.0, "n_on": 30, "n_off": 100, "alpha": 0.1, "excess": 20.0,
         "significance": significance}))
    (result / "data/fit.yaml").write_text(yaml.safe_dump({"success": fit_success}))
    (result / "data/models.yaml").write_text(yaml.safe_dump({"components": [{"spectral": {
        "parameters": [{"name": "index", "value": 2.5, "error": 0.1},
                       {"name": "amplitude", "value": 3e-11, "error": 1e-12}]}}]}))
    job = dict(source="Crab", selection="runs", cut="moderate", release="v491",
               analysis_type="AP", requested=1, result=str(result), status="ready")
    (tmp_path / "manifest.json").write_text(json.dumps({"jobs": [job]}))
    row = source_checks.collect(tmp_path)[0]
    assert row["status"] == "complete"
    assert row["significance"] == significance
    assert row["ontime_h"] == 1.0
    assert row["detected"] == detected
    assert (row["index"] == 2.5) == fit_success
    report = (tmp_path / "report.md").read_text()
    assert ("2.500 ± 0.100" in report) == (detected and fit_success)


def test_collect_reports_absent_result_as_not_run(tmp_path):
    job = dict(source="Crab", selection="runs", cut="moderate", release="v491",
               analysis_type="AP", requested=1, result=str(tmp_path / "none"), status="ready")
    (tmp_path / "manifest.json").write_text(json.dumps({"jobs": [job]}))
    row = source_checks.collect(tmp_path)[0]
    assert row["status"] == "not_run"
