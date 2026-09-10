#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate topic-specific Chenpi article images with SiliconFlow."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parents[1]
IMAGE_DIR = REPO_DIR / "images"
API_URL = os.environ.get("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1").rstrip("/") + "/images/generations"
MODEL = os.environ.get("SILICONFLOW_IMAGE_MODEL", "Kwai-Kolors/Kolors")

ARTICLES = [
    ("article-20260903-time-philosophy.png", "A cinematic editorial still life about the philosophy of time in aged Xinhui chenpi: carefully opened dried mandarin orange peels in a traditional wooden drying room, warm shafts of sunlight, ceramic storage jars, visible natural texture and oil-cell patterns, calm contemplative atmosphere, premium Chinese food culture photography, no text, no logos, no people close-up"),
    ("article-20260903-overseas-chenpi.jpg", "A cinematic documentary-style scene showing Xinhui chenpi prepared for compliant overseas export: labeled paper cartons and traceability documents beside carefully packed dried mandarin orange peels, modern port logistics softly visible in the background, warm natural light, credible food supply chain editorial photography, no readable text, no logos, no flags, no people close-up"),
    ("article-20260904-chenpi-selection.png", "A refined editorial still life for a Xinhui chenpi buying guide: several dried mandarin orange peels, a simple magnifying glass, neutral packaging with blank labels, a tea tray and notebook on a clean wooden table, natural texture and restrained warm colors, trustworthy consumer education photography, no readable text, no logos"),
    ("article-20260905-industry-craft.png", "A wide cinematic documentary image about the Xinhui chenpi industry from orchard to teacup: tea-branch mandarin orchard in the foreground, workers carefully opening and drying peels in the middle distance, tea cup and storage shelves subtly in the background, warm Guangdong light, realistic editorial photography, no readable text, no logos"),
    ("article-20260906-geographical-protection.jpg", "A documentary editorial image about protecting the Xinhui chenpi geographical indication: orderly mandarin orchard, dried peels on bamboo drying trays, a traceability notebook and sealed storage crate in the foreground, layered visual journey from harvest to warehouse, warm realistic Chinese agricultural photography, no readable text, no logos"),
    ("article-20260907-festival-traceability.jpg", "A warm documentary scene about Xinhui chenpi cultural heritage and traceability: community agricultural exchange beside a traditional drying yard, mandarin peels, bamboo trays and orderly storage, festive but authentic local culture atmosphere, golden late-afternoon light, realistic editorial photography, no readable text, no logos"),
    ("article-20260908-autumn-harvest.jpg", "An atmospheric autumn Xinhui mandarin harvest scene: ripe mandarins in a waterside orchard, freshly opened peels drying on bamboo trays, a small tea set waiting nearby, soft autumn morning mist and warm sunlight, inviting realistic editorial food photography, no readable text, no logos"),
]


def request_image(prompt: str) -> str:
    key = os.environ.get("SILICONFLOW_API_KEY", "").strip()
    if not key:
        raise RuntimeError("SILICONFLOW_API_KEY is not available")
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "image_size": "1024x1024",
        "batch_size": 1,
        "num_inference_steps": 28,
        "negative_prompt": "text, watermark, logo, label, extra fingers, distorted objects, blurry, low quality",
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "X-Enable-Watermark": "0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"SiliconFlow HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"SiliconFlow network error: {exc.reason}") from exc
    images = data.get("images") or []
    if not images or not images[0].get("url"):
        raise RuntimeError(f"SiliconFlow response did not contain an image URL: {json.dumps(data, ensure_ascii=False)[:500]}")
    return images[0]["url"]


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "chenpi-site-image-generator/1.0"})
    with urllib.request.urlopen(request, timeout=180) as response:
        content = response.read()
    if len(content) < 10_000:
        raise RuntimeError(f"Downloaded image is unexpectedly small: {len(content)} bytes")
    destination.write_bytes(content)


def main() -> int:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating {len(ARTICLES)} SiliconFlow images with model {MODEL}...")
    for index, (filename, prompt) in enumerate(ARTICLES, start=1):
        destination = IMAGE_DIR / filename
        print(f"[{index}/{len(ARTICLES)}] {filename}")
        url = request_image(prompt)
        download(url, destination)
        print(f"  saved {destination.stat().st_size} bytes")
        if index < len(ARTICLES):
            time.sleep(1)
    print("IMAGE_GENERATION_COMPLETE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"IMAGE_GENERATION_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
