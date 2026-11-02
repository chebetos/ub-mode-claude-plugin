import json
from pathlib import Path

from tools.sync import Change, apply, check, classify, commit_message, main


class FakeGitHub:
    def __init__(self, heads: dict[str, str], files: dict[str, list[str]]) -> None:
        self.heads = heads
        self.files = files

    def resolve_sha(self, repo: str, ref: str) -> str:
        return self.heads[repo]

    def changed_paths(self, repo: str, base: str, head: str) -> list[str]:
        return self.files[repo]


def _lock() -> dict[str, dict[str, str]]:
    return {
        name: {"repo": f"unclebob/{name}", "ref": "master", "sha": f"old-{name}"}
        for name in ("ub-mode", "crapper", "dryer", "mutator", "uml-viewer")
    }


def test_classify_skill_change_is_feat():
    assert classify("ub-mode", ["SKILL.md", "README.md"]) == "feat"


def test_classify_ub_mode_readme_only_is_fix():
    assert classify("ub-mode", ["README.md"]) == "fix"


def test_classify_tool_source_change_is_feat():
    assert classify("crapper", ["README.md", "src/crapper/cli.py"]) == "feat"


def test_classify_tool_docs_or_tests_only_is_fix():
    assert classify("dryer", ["README.md", "tests/test_x.py"]) == "fix"


def test_classify_uml_viewer_is_always_fix():
    assert classify("uml-viewer", ["src/uml_viewer/domain/ir.clj"]) == "fix"


def test_check_reports_only_upstreams_with_new_commits_in_fixed_order():
    heads = {f"unclebob/{n}": f"old-{n}" for n in _lock()}
    heads["unclebob/mutator"] = "new-mutator"
    heads["unclebob/crapper"] = "new-crapper"
    files = {"unclebob/mutator": ["README.md"], "unclebob/crapper": ["src/crapper/cli.py"]}
    changes = check(_lock(), FakeGitHub(heads, files))
    assert [(c.name, c.type, c.new_sha) for c in changes] == [
        ("crapper", "feat", "new-crapper"),
        ("mutator", "fix", "new-mutator"),
    ]


def test_check_returns_nothing_when_all_shas_match():
    heads = {f"unclebob/{n}": f"old-{n}" for n in _lock()}
    assert check(_lock(), FakeGitHub(heads, {})) == []


def test_commit_message_has_scope_short_sha_and_changed_files():
    change = Change("crapper", "feat", "aaaaaaaaaa", "6fd92c4c9bcc", ["src/a.py", "README.md"])
    assert commit_message(change) == (
        "feat(upstream/crapper): sync to 6fd92c4\n\n"
        "Changed upstream files:\n- src/a.py\n- README.md"
    )


def test_commit_message_truncates_long_file_lists():
    change = Change("crapper", "feat", "a", "b" * 12, [f"f{i}" for i in range(25)])
    message = commit_message(change)
    assert "- f19" in message
    assert "- f20" not in message
    assert message.endswith("- ... and 5 more")


def test_apply_creates_one_commit_per_change_updating_lock_each_time(tmp_path: Path):
    lock_path = tmp_path / "upstream.lock.json"
    lock = _lock()
    changes = [
        Change("crapper", "feat", "old-crapper", "new-crapper", ["src/x.py"]),
        Change("mutator", "fix", "old-mutator", "new-mutator", ["README.md"]),
    ]
    events: list[str] = []
    locks_at_build: list[str] = []

    def build() -> None:
        events.append("build")
        locks_at_build.append(json.loads(lock_path.read_text())["crapper"]["sha"])

    def git(*args: str) -> None:
        events.append(" ".join(args[:2]))

    apply(changes, lock, lock_path, build, git, ["plugins"])

    assert events == ["build", "add -A", "commit -m", "build", "add -A", "commit -m"]
    assert locks_at_build == ["new-crapper", "new-crapper"]
    assert json.loads(lock_path.read_text())["mutator"]["sha"] == "new-mutator"
    assert json.loads(lock_path.read_text())["dryer"]["sha"] == "old-dryer"


def test_main_check_exits_10_and_prints_json_when_changes_exist(capsys, tmp_path: Path):
    lock_path = tmp_path / "lock.json"
    lock_path.write_text(json.dumps(_lock()))
    heads = {f"unclebob/{n}": f"old-{n}" for n in _lock()}
    heads["unclebob/dryer"] = "new-dryer"
    code = main(["--check"], lock_path, FakeGitHub(heads, {"unclebob/dryer": ["README.md"]}))
    report = json.loads(capsys.readouterr().out)
    assert code == 10
    assert report == [
        {"name": "dryer", "type": "fix", "old_sha": "old-dryer", "new_sha": "new-dryer"}
    ]


def test_main_check_exits_0_when_up_to_date(capsys, tmp_path: Path):
    lock_path = tmp_path / "lock.json"
    lock_path.write_text(json.dumps(_lock()))
    heads = {f"unclebob/{n}": f"old-{n}" for n in _lock()}
    assert main(["--check"], lock_path, FakeGitHub(heads, {})) == 0
    assert json.loads(capsys.readouterr().out) == []
