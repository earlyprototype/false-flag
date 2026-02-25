import os
import json
import hashlib
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

import feedparser  # type: ignore
import requests  # type: ignore


def _hash_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def fetch_rss_episodes(feed_url: str, limit: int = 5) -> List[Dict[str, Any]]:
    feed = feedparser.parse(feed_url)
    items = []
    for e in feed.entries[:limit]:
        enclosure = None
        # RSS enclosures
        if hasattr(e, "links"):
            for link in e.links:
                if link.get("rel") == "enclosure" and "audio" in link.get("type", ""):
                    enclosure = link.get("href")
                    break
        items.append({
            "title": getattr(e, "title", ""),
            "published": getattr(e, "published", ""),
            "link": getattr(e, "link", ""),
            "audio": enclosure,
        })
    return [i for i in items if i.get("audio")]


def download_audio(url: str, out_dir: Path, referer: Optional[str] = None) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "audio/*,application/octet-stream;q=0.9,*/*;q=0.8",
        "Range": "bytes=0-",
    }
    if referer:
        headers["Referer"] = referer
        try:
            session.get(referer, headers=headers, timeout=30, allow_redirects=True)
        except Exception:
            pass

    resp = session.get(url, headers=headers, stream=True, timeout=60, allow_redirects=True)
    if resp.status_code in (401, 403) and "Referer" not in headers:
        headers["Referer"] = "https://feeds.captivate.fm/"
        resp = session.get(url, headers=headers, stream=True, timeout=60, allow_redirects=True)
    resp.raise_for_status()

    # Decide extension from response or URL
    content_type = resp.headers.get("Content-Type", "")
    ext = ".mp3"
    if "audio/mpeg" in content_type or url.endswith(".mp3"):
        ext = ".mp3"
    elif "audio/x-m4a" in content_type or url.endswith(".m4a"):
        ext = ".m4a"

    # Stream to a temporary file while hashing
    import hashlib as _hl
    hasher = _hl.sha256()
    tmp = None
    try:
        tmp = Path(tempfile.NamedTemporaryFile(delete=False, dir=str(out_dir), suffix=".part").name)
    except Exception:
        tmp = out_dir / (".download_" + _hash_bytes(os.urandom(8)) + ".part")
    with tmp.open("wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            if not chunk:
                continue
            f.write(chunk)
            hasher.update(chunk)
    digest16 = hasher.hexdigest()[:16]
    final_path = out_dir / f"episode_{digest16}{ext}"
    tmp.replace(final_path)
    return final_path


def transcribe_whisper(audio_path: Path, model_name: str = "base") -> Dict[str, Any]:
    import whisper  # type: ignore

    model = whisper.load_model(model_name)
    result = model.transcribe(str(audio_path))
    # normalize segments
    segments = []
    for s in result.get("segments", []):
        segments.append({
            "start": float(s.get("start", 0.0)),
            "end": float(s.get("end", 0.0)),
            "text": s.get("text", "").strip(),
        })
    return {"text": result.get("text", "").strip(), "segments": segments}


def diarize_pyannote(audio_path: Path) -> Optional[List[Dict[str, Any]]]:
    token = os.environ.get("HUGGINGFACE_TOKEN")
    if not token:
        return None
    try:
        from pyannote.audio import Pipeline  # type: ignore
    except Exception:
        return None
    try:
        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=token)
        diarization = pipeline(str(audio_path))
        diar_segments: List[Dict[str, Any]] = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            diar_segments.append({
                "start": float(turn.start),
                "end": float(turn.end),
                "speaker": str(speaker),
            })
        return diar_segments
    except Exception:
        return None


def assign_speakers(whisper_segments: List[Dict[str, Any]], diar_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # naive overlap-based assignment
    out = []
    for ws in whisper_segments:
        w_start, w_end = ws["start"], ws["end"]
        best_speaker = None
        best_overlap = 0.0
        for ds in diar_segments:
            d_start, d_end = ds["start"], ds["end"]
            overlap = max(0.0, min(w_end, d_end) - max(w_start, d_start))
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = ds["speaker"]
        out.append({
            "start": w_start,
            "end": w_end,
            "text": ws["text"],
            "speaker": best_speaker or "SPEAKER_00",
        })
    return out


def save_outputs(base_dir: Path, meta: Dict[str, Any], diarised_segments: List[Dict[str, Any]]) -> None:
    base_dir.mkdir(parents=True, exist_ok=True)
    # JSONL segments
    jsonl_path = base_dir / f"{meta['id']}.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for seg in diarised_segments:
            f.write(json.dumps(seg, ensure_ascii=False) + "\n")
    # Markdown provenance
    md = [
        f"# Transcript — {meta.get('title','')} ",
        "",
        f"- Source: {meta.get('link','')} ",
        f"- Published: {meta.get('published','')} ",
        f"- Audio: {meta.get('audio','')} ",
        f"- Hash: {meta.get('hash','')} ",
        f"- ASR: Whisper", 
        f"- Diarisation: {'pyannote 3.1' if os.environ.get('HUGGINGFACE_TOKEN') else 'none'}",
        "",
    ]
    (base_dir / f"{meta['id']}.md").write_text("\n".join(md), encoding="utf-8")


def ingest_feed(feed_url: str, out_dir: Path, limit: int = 1, whisper_model: str = "base") -> None:
    print(f"[Feed] Fetching: {feed_url} (limit={limit})")
    episodes = fetch_rss_episodes(feed_url, limit=limit)
    print(f"[Feed] {len(episodes)} playable episodes found")
    for ep in episodes:
        print("")
        print(f"[Episode] {ep.get('title','(untitled)')}")
        audio = ep["audio"]
        # Prefer episode page link as referer; otherwise use the feed URL.
        referer = ep.get("link") or feed_url
        audio_path: Optional[Path] = None
        try:
            print(f"[Download] starting")
            audio_path = download_audio(audio, out_dir / "audio", referer=referer)
            try:
                size_mb = audio_path.stat().st_size / (1024 * 1024)
                print(f"[Download] done: {audio_path.name} ({size_mb:.1f} MB)")
            except Exception:
                print(f"[Download] done: {audio_path.name}")
        except requests.HTTPError as http_err:
            status = getattr(getattr(http_err, "response", None), "status_code", None)
            print(f"[Download] failed: HTTP {status if status is not None else '?'} — {http_err}")
            raise
        assert audio_path is not None
        print(f"[ASR] Whisper {whisper_model}: starting")
        asr = transcribe_whisper(audio_path, model_name=whisper_model)
        print(f"[ASR] done: {len(asr.get('segments', []))} segments")
        token = os.environ.get("HUGGINGFACE_TOKEN")
        diar = None
        if token:
            print(f"[Diarisation] pyannote 3.1: starting")
            diar = diarize_pyannote(audio_path)
            if diar:
                print(f"[Diarisation] done: {len(diar)} segments")
            else:
                print(f"[Diarisation] skipped or failed (pyannote not installed or runtime error)")
        else:
            print(f"[Diarisation] skipped (no HUGGINGFACE_TOKEN set)")
        if diar:
            segments = assign_speakers(asr["segments"], diar)
        else:
            segments = [
                {"start": s["start"], "end": s["end"], "text": s["text"], "speaker": "SPEAKER_00"}
                for s in asr["segments"]
            ]
        meta = {
            "id": f"ep_{_hash_bytes(audio_path.read_bytes())}",
            "title": ep.get("title", ""),
            "published": ep.get("published", ""),
            "link": ep.get("link", ""),
            "audio": ep.get("audio", ""),
            "hash": _hash_bytes(audio_path.read_bytes()),
        }
        out_transcripts = out_dir / "@filing" / "transcripts"
        print(f"[Save] writing to {out_transcripts}")
        save_outputs(out_transcripts, meta, segments)
        print(f"[Save] done: {meta['id']}.jsonl + {meta['id']}.md")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("feed", help="Podcast RSS feed URL")
    parser.add_argument("--out", default=str(Path.cwd()), help="Output root directory (default: CWD)")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--whisper", default="base")
    args = parser.parse_args()
    ingest_feed(args.feed, Path(args.out), limit=args.limit, whisper_model=args.whisper)


