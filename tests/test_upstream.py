import io
import json
import tarfile
from pathlib import Path

import pytest

from tools.upstream import GitHub, UpstreamError, build_request


def _tarball(files: dict[str, str], root: str = "unclebob-crapper-abc123") -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, content in files.items():
            data = content.encode()
            info = tarfile.TarInfo(f"{root}/{name}")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


class FakeFetch:
    def __init__(self, responses: dict[str, bytes]) -> None:
        self.responses = responses
        self.calls: list[str] = []

    def __call__(self, url: str) -> bytes:
        self.calls.append(url)
        return self.responses[url]


def test_resolve_sha_returns_commit_sha_for_ref():
    fetch = FakeFetch(
        {"https://api.github.com/repos/unclebob/crapper/commits/master": b'{"sha": "abc123"}'}
    )
    assert GitHub(fetch).resolve_sha("unclebob/crapper", "master") == "abc123"


def test_resolve_sha_raises_when_response_has_no_sha():
    fetch = FakeFetch({"https://api.github.com/repos/unclebob/crapper/commits/master": b"{}"})
    with pytest.raises(UpstreamError):
        GitHub(fetch).resolve_sha("unclebob/crapper", "master")


def test_changed_paths_lists_files_between_two_shas():
    payload = json.dumps({"files": [{"filename": "src/a.py"}, {"filename": "README.md"}]})
    url = "https://api.github.com/repos/unclebob/crapper/compare/aaa...bbb"
    assert GitHub(FakeFetch({url: payload.encode()})).changed_paths(
        "unclebob/crapper", "aaa", "bbb"
    ) == ["src/a.py", "README.md"]


def test_extract_tarball_returns_repo_root_without_github_prefix(tmp_path: Path):
    url = "https://api.github.com/repos/unclebob/crapper/tarball/abc123"
    fetch = FakeFetch({url: _tarball({"README.md": "hi", "src/crapper/cli.py": "x"})})
    root = GitHub(fetch).extract_tarball("unclebob/crapper", "abc123", tmp_path)
    assert (root / "README.md").read_text() == "hi"
    assert (root / "src/crapper/cli.py").read_text() == "x"


def test_extract_tarball_rejects_path_traversal(tmp_path: Path):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        info = tarfile.TarInfo("root/../../evil.txt")
        info.size = 1
        tar.addfile(info, io.BytesIO(b"x"))
    url = "https://api.github.com/repos/unclebob/crapper/tarball/abc123"
    with pytest.raises(UpstreamError):
        GitHub(FakeFetch({url: buf.getvalue()})).extract_tarball(
            "unclebob/crapper", "abc123", tmp_path
        )


def test_build_request_adds_bearer_token_when_given():
    request = build_request("https://api.github.com/x", token="t0k")
    assert request.get_header("Authorization") == "Bearer t0k"


def test_build_request_omits_authorization_without_token():
    assert build_request("https://api.github.com/x", token=None).get_header("Authorization") is None


def test_changed_paths_raises_when_the_comparison_hits_the_file_limit():
    payload = json.dumps({"files": [{"filename": f"f{i}.py"} for i in range(300)]})
    url = "https://api.github.com/repos/unclebob/crapper/compare/aaa...bbb"
    with pytest.raises(UpstreamError):
        GitHub(FakeFetch({url: payload.encode()})).changed_paths("unclebob/crapper", "aaa", "bbb")
