"""TR/EN repair entry point: local review artifacts, no delivery or TTS APIs."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from editorial_quality_gate import (EditorialGateError, check_media_duration,
                                     check_photo_evidence, check_storyboard, media_sha256)
from source_evidence import EvidenceError, check_script, packet_sha256, text_sha256
from media_evidence import MediaEvidenceError, inspect_audio


def workspace_file(root: Path, value: str) -> Path:
    """An evidence packet cannot read media outside this isolated snapshot."""
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise EvidenceError("Local input must be a file inside this snapshot")
    return path


def prepare_preview(*, root: Path, output: Path, today: datetime, packet_path: str,
                    discover, render, language: str = "tr") -> dict:
    """Keep a durable honest plan on every missing-proof path; never auto-approve.

    render is a local FFmpeg adapter. Neither discovery nor packet metadata can
    enable WordPress, GitHub assets, Facebook or paid voice generation.
    """
    output = output.resolve()
    if not output.is_relative_to(root.resolve()):
        raise EvidenceError("Preview output must stay inside this snapshot")
    output.mkdir(parents=True, exist_ok=True)
    result = {"preview_only": True, "delivery_allowed": False, "editorial_approved": False,
              "status": "BLOCKED_PREVIEW", "blockers": [], "video_created": False}
    candidate = {}
    try:
        if packet_path:
            candidate = json.loads(workspace_file(root, packet_path).read_text(encoding="utf-8-sig"))
            if not isinstance(candidate, dict):
                raise EvidenceError("Editorial packet must be an object")
        else:
            candidates = discover([], today=today)
            candidate = candidates[0]
        # Persist discovery even when the next source gate blocks it.
        (output / "preview-plan.json").write_text(json.dumps(candidate, ensure_ascii=False, indent=2), encoding="utf-8")
        if candidate.get("research_date") != today.date().isoformat():
            raise EvidenceError("Packet research date differs from requested preview day")
        if candidate.get("reels_language") != language:
            raise EvidenceError("Packet language differs from requested channel")
        script = check_script(candidate)
        photos = check_photo_evidence(candidate)
        use_storyboard = language == 'tr' or 'visual_storyboard' in candidate
        if use_storyboard:
            check_storyboard(candidate)
        paths = []
        for photo in photos:
            path = workspace_file(root, str(photo.get("local_path") or ""))
            if media_sha256(path) != photo["asset_sha256"]:
                raise EvidenceError("Local artist photo hash differs from documented asset")
            from PIL import Image
            with Image.open(path) as image:
                if image.size != (photo["width"], photo["height"]):
                    raise EvidenceError("Decoded photo resolution differs from evidence")
                image.verify()
            paths.append(path)
        voice = workspace_file(root, str(candidate.get("local_voiceover") or ""))
        evidence = candidate.get("voice_evidence") or {}
        if (evidence.get("sha256") != media_sha256(voice) or
                evidence.get("script_sha256") != text_sha256(script) or
                evidence.get("transcript") != script or evidence.get("language") != language or
                evidence.get("unmodified_speed") is not True):
            raise EvidenceError("Local narration must be hash-bound to exact script/language at natural speed")
        result["voice_measurement"] = inspect_audio(voice)
        if use_storyboard:
            check_storyboard(candidate, result['voice_measurement']['decoded_seconds'])
        # Reuse only a completed, hash-checked checkpoint for this exact packet
        # and renderer revision. Ambiguous/partial output stops, never overwrites.
        digest = packet_sha256(candidate)
        code_digest = text_sha256("".join(media_sha256(root / name) for name in
            ("worker.py", "video_factory.py", "media_evidence.py", "source_evidence.py",
             "editorial_quality_gate.py", "reels_preview.py")))
        render_dir = output / f"{digest[:16]}-{code_digest[:12]}"
        render_dir.mkdir(exist_ok=True)
        target = render_dir / f"{language}-unapproved-preview.mp4"
        receipt = render_dir / "render-receipt.json"
        if target.exists():
            if not receipt.is_file():
                raise EvidenceError("Ambiguous prior render has no completed receipt; reconcile before retry")
            saved = json.loads(receipt.read_text(encoding="utf-8"))
            if saved.get("media_sha256") != media_sha256(target):
                raise EvidenceError("Existing render differs from saved media receipt; reconcile before retry")
            result["reused_checkpoint"] = True
        else:
            render(candidate, paths, voice, target)
            result["reused_checkpoint"] = False
        result["media"] = check_media_duration(target)
        (render_dir / "content.json").write_text(json.dumps(candidate, ensure_ascii=False, indent=2), encoding="utf-8")
        receipt.write_text(json.dumps({"candidate_sha256": digest, "code_sha256": code_digest,
            "media_sha256": result["media"]["media_sha256"]}, indent=2), encoding="utf-8")
        result.update(status="UNAPPROVED_MEDIA_PREVIEW", video_created=True,
                      candidate_sha256=digest, video_path=str(target))
        result["blockers"] = ["Independent original-source, photo and natural DJ review required; no delivery authorized"]
    except (EvidenceError, EditorialGateError, MediaEvidenceError, RuntimeError, OSError, ValueError, IndexError, TypeError, KeyError) as exc:
        result["blockers"].append(str(exc))
    (output / "preview-status.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
