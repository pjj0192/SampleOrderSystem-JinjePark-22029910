"""Smoke test for the seed_samples CLI (Plan.md Step 8.3, optional convenience
tool -- not part of the graded feature set). Confirms it writes the requested
count to the target file and doesn't collide across repeated runs."""

import json

from app.tools.seed_samples import main


def test_seed_samples_generates_and_persists_requested_count(tmp_path, capsys):
    file_path = tmp_path / "samples.json"

    main(["--count", "15", "--file", str(file_path), "--seed", "42"])

    saved = json.loads(file_path.read_text(encoding="utf-8"))
    assert len(saved) == 15
    assert "15개의 더미 시료를" in capsys.readouterr().out


def test_seed_samples_appends_without_colliding_on_second_run(tmp_path):
    file_path = tmp_path / "samples.json"

    main(["--count", "5", "--file", str(file_path), "--seed", "1"])
    main(["--count", "5", "--file", str(file_path), "--seed", "2"])

    saved = json.loads(file_path.read_text(encoding="utf-8"))
    ids = [item["sample_id"] for item in saved]
    assert len(ids) == len(set(ids)) == 10
