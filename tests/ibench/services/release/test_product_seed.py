from pathlib import Path

from ibench.services.release.compiler import load_release, prepare_solve, snapshot_release


def test_product_solve_freezes_gt_seed_without_replay_or_judge_material(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[4]
    manifest = load_release(root, ("product-tab-opening",))
    task = manifest.tasks[0]
    task_root = root / "tasks" / task.id
    fixture = task_root / "score/steps/score/workdir/case-context/issues/1/fixtures/reference-after"
    source_seed = task_root / "solve/steps/solve/workdir/seed"
    for name in ("setup.sh", "cleanup.sh"):
        assert (source_seed / name).is_symlink()
        assert (source_seed / name).resolve() == fixture / name

    snapshot = tmp_path / "snapshot"
    snapshot_release(root, manifest, snapshot)
    compiled = prepare_solve(snapshot, task, tmp_path / "solve", "intent")
    seed = compiled / "steps/solve/workdir/seed"
    assert {path.name for path in seed.iterdir()} == {"setup.sh", "cleanup.sh"}
    for name in ("setup.sh", "cleanup.sh"):
        assert not (seed / name).is_symlink()
        assert (seed / name).read_bytes() == (fixture / name).read_bytes()
    assert not list(compiled.rglob("action.mjs"))
    assert not list(compiled.rglob("setup.mjs"))
    assert not list(compiled.rglob("rubric.json"))
    assert not list(compiled.rglob("presentation.json"))
