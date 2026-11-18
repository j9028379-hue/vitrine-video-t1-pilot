"""Full-duration visual integrity scan: frame continuity, blackouts and red diagnostic-box guard."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import cv2
import numpy as np

W, H, FPS, FRAMES = 720, 1280, 30, 900


def red_outline_candidates(frame: np.ndarray) -> list[dict[str, int]]:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # Exclude the authored orange brand color; look only for saturated pure-red annotation strokes.
    mask = cv2.inRange(hsv, np.array([0, 150, 100], np.uint8), np.array([7, 255, 255], np.uint8))
    mask |= cv2.inRange(hsv, np.array([173, 150, 100], np.uint8), np.array([179, 255, 255], np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    found = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w < 100 or h < 44 or w > 680 or h > 1200:
            continue
        area = max(1, w * h)
        density = cv2.countNonZero(mask[y:y+h, x:x+w]) / area
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.025 * perimeter, True)
        roi = mask[y:y+h, x:x+w]
        band = max(2, min(5, w // 50, h // 50))
        edge_cover = [float((roi[:band, :] > 0).mean()), float((roi[-band:, :] > 0).mean()),
                      float((roi[:, :band] > 0).mean()), float((roi[:, -band:] > 0).mean())]
        # Require all four rectangle edges to be predominantly pure red; food hues/shapes do not qualify.
        if 0.008 <= density <= 0.16 and len(approx) == 4 and min(edge_cover) >= 0.55:
            found.append({"x": x, "y": y, "w": w, "h": h, "red_density_per_bbox": round(density, 4)})
    return found


def scan_video(path: Path) -> dict:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {path}")
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = float(cap.get(cv2.CAP_PROP_FPS))
    count = 0
    black_frames = []
    red_boxes = []
    frozen_pairs = []
    prev = None
    min_luma = 255.0
    max_luma = 0.0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_luma = float(gray.mean())
        min_luma = min(min_luma, mean_luma)
        max_luma = max(max_luma, mean_luma)
        if float(np.percentile(gray, 99)) < 12.0:
            black_frames.append(count)
        boxes = red_outline_candidates(frame)
        if boxes:
            red_boxes.extend({"frame": count, **b} for b in boxes)
        if prev is not None:
            diff = cv2.absdiff(gray, prev)
            if float(diff.mean()) < 0.025 and float(np.percentile(diff, 95)) < 0.10:
                frozen_pairs.append(count - 1)
        prev = gray
        count += 1
    cap.release()
    report = {
        "file": path.name,
        "decoded_frames": count,
        "expected_frames": FRAMES,
        "dimensions": [actual_w, actual_h],
        "fps": actual_fps,
        "dimensions_ok": actual_w == W and actual_h == H,
        "fps_ok": abs(actual_fps - FPS) < 0.01,
        "black_frames": black_frames,
        "suspected_red_diagnostic_rectangles": red_boxes,
        "near_identical_frame_pairs": frozen_pairs,
        "mean_luma_range": [round(min_luma, 2), round(max_luma, 2)],
        "result": "PASS" if count == FRAMES and actual_w == W and actual_h == H and abs(actual_fps - FPS) < 0.01 and not black_frames and not red_boxes and not frozen_pairs else "FAIL",
    }
    return report


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--video", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    report = scan_video(args.video)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["result"] != "PASS":
        raise SystemExit(1)

if __name__ == "__main__":
    main()
