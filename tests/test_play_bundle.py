"""The shipped browser build is one coherent thing, and says which one it is.

``tests/test_opening_beats.py`` already proves the committed ``docs/game.zip``
matches the repo. That is necessary but not sufficient: the bundle and the page
assets beside it are fetched separately and cached separately, so a browser can
hold a fresh ``app.js`` next to a months-old engine and run the two together.

That mixture is not a hypothetical. A cached bundle from before the threadless
batch fix failed every batched LLM call inside Pyodide, answered the player from
the offline stand-in, and displayed a notice blaming their network — while the
deploy it was talking to was entirely current.

The build stamp is what makes that impossible: one content hash over the bundle
and the page assets, written into the bundle, declared by ``index.html``, and
appended to every asset URL, so a changed build changes every URL at once and a
browser either has all of it or fetches all of it. These tests check the
committed artifacts carry a consistent stamp. Nothing is rebuilt, so a failure
means "run the builder", never a side effect of running the suite.
"""

import importlib.util
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "docs" / "game.zip"
PAGE = ROOT / "docs" / "index.html"

REBUILD = ("Run `python3 dev-scripts/build_play_bundle.py` and commit the "
           "result.")


@pytest.fixture(scope="module")
def builder():
    """Import dev-scripts/build_play_bundle.py (not an importable package)."""
    path = ROOT / "dev-scripts" / "build_play_bundle.py"
    spec = importlib.util.spec_from_file_location("build_play_bundle", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def stamp(builder):
    """The build every committed artifact should currently be declaring."""
    return builder.compute_stamp(builder.collect_files())


def test_bundle_carries_a_stamp_matching_its_contents(builder, stamp):
    """The bundle reports the build it actually is.

    Without this the page has nothing to compare against, and a cache serving
    an old bundle looks exactly like the game misbehaving.
    """
    with zipfile.ZipFile(BUNDLE) as z:
        assert builder.BUILD_STAMP_ARCNAME in z.namelist(), (
            f"docs/game.zip has no {builder.BUILD_STAMP_ARCNAME}. {REBUILD}")
        packed = z.read(builder.BUILD_STAMP_ARCNAME).decode().strip()
    assert packed == stamp, (
        f"docs/game.zip is stamped {packed!r} but its contents hash to "
        f"{stamp!r}. {REBUILD}")


def test_page_declares_the_same_build_the_bundle_was_stamped_with(stamp):
    """The page names the build, so a cache pairing it wrongly can be seen."""
    text = PAGE.read_text(encoding="utf-8")
    assert f'<meta name="ff-build" content="{stamp}">' in text, (
        f"docs/index.html does not declare build {stamp}, so the page cannot "
        f"tell when a cache has paired it with a different engine. {REBUILD}")


def test_every_cacheable_asset_is_fetched_with_the_stamp(builder, stamp):
    """An unstamped asset is one a browser may keep across a deploy.

    That is the whole mechanism of the mixed-build failure, so it is worth
    asserting per asset rather than trusting the builder ran.
    """
    text = PAGE.read_text(encoding="utf-8")
    unstamped = [name for name in builder.STAMPED_ASSETS
                 if f"{name}?v={stamp}" not in text]
    assert not unstamped, (
        f"referenced without the current build stamp, so they can be served "
        f"stale against a newer engine: {unstamped}. {REBUILD}")


def test_the_stamp_changes_when_any_shipped_file_changes(builder, tmp_path):
    """A stamp that did not move on a change would be worse than none.

    It would assert coherence a browser does not have — the cached-asset
    problem, plus a claim that everything is fine.
    """
    files = builder.collect_files()
    baseline = builder.compute_stamp(files)

    edited = tmp_path / "edited.py"
    original_path, arcname = files[0]
    edited.write_bytes(original_path.read_bytes() + b"\n# changed\n")
    assert builder.compute_stamp(
        [(edited, arcname)] + files[1:]) != baseline, (
        "the stamp ignored a change to a bundled source file")


def test_the_stamp_follows_page_asset_contents_not_just_their_names(
        builder, monkeypatch, tmp_path):
    """Editing app.js must move the stamp, or the page never re-fetches it.

    Asserted by editing bytes rather than by dropping the asset lists: an
    implementation that hashed asset *names* and ignored their contents would
    satisfy the weaker form, and would ship precisely the stale-CSS-against-
    fresh-markup pairing this stamp exists to prevent.
    """
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "app.js").write_bytes(b"// one\n")
    (docs / "play.css").write_bytes(b"body{}\n")
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    monkeypatch.setattr(builder, "STAMPED_ASSETS", ["app.js", "play.css"])
    monkeypatch.setattr(builder, "UNSTAMPED_IN_HASH", [])

    baseline = builder.compute_stamp([])
    (docs / "app.js").write_bytes(b"// two\n")
    assert builder.compute_stamp([]) != baseline, (
        "a change to app.js left the stamp — and every cached asset URL — "
        "asserting a build the browser no longer has")


def test_the_stamp_distinguishes_a_byte_moving_between_two_files(builder,
                                                                 tmp_path):
    """Entries are framed, so a shifted boundary is not a silent no-op.

    Hashing names and contents as two flat runs let content move from one
    file into the next without changing the stream. The stamp would hold
    steady across a real change, which is the one failure mode a build stamp
    must not have.
    """
    a, b = tmp_path / "a.py", tmp_path / "b.py"
    a.write_bytes(b"X")
    b.write_bytes(b"YZ")
    before = builder.compute_stamp([(a, "a.py"), (b, "b.py")])

    a.write_bytes(b"XY")
    b.write_bytes(b"Z")
    assert builder.compute_stamp([(a, "a.py"), (b, "b.py")]) != before


def test_a_missing_page_asset_fails_the_build_rather_than_hashing_around_it(
        builder, monkeypatch, tmp_path):
    """A deploy missing app.js must not be handed a stamp saying it is whole."""
    docs = tmp_path / "docs"
    docs.mkdir()
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    monkeypatch.setattr(builder, "STAMPED_ASSETS", ["app.js"])
    monkeypatch.setattr(builder, "UNSTAMPED_IN_HASH", [])
    with pytest.raises(FileNotFoundError):
        builder.compute_stamp([])


def test_a_missing_page_fails_the_build(builder, monkeypatch, tmp_path):
    """No index.html means nothing tells a browser which build it is running."""
    monkeypatch.setattr(builder, "PAGE", tmp_path / "absent.html")
    monkeypatch.setattr(builder, "OUT", tmp_path / "game.zip")
    assert builder.build() == 1
    with pytest.raises(FileNotFoundError):
        builder.stamp_page("deadbeef1234")
