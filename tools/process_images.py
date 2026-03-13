"""
Image processing pipeline for BUMBLEBEE (camaro.to).
Generates responsive WebP/JPG variants, LQIP base64 placeholders, OG image, favicon, and video poster.

Usage:
    python process_images.py

Requires: Pillow, opencv-python (pip install Pillow opencv-python)
"""

import base64
import io
import json
import shutil
from pathlib import Path
from PIL import Image, ImageOps

# === Configuration ===

SOURCES = {
    "2025.12":       Path(r"C:\Users\mdzho\Downloads\CAMARO\2017 2SS\2025.12"),
    "mobile.bg":     Path(r"C:\Users\mdzho\Downloads\CAMARO\2017 2SS\2024 - mobile.bg"),
    "photo_session": Path(r"C:\Users\mdzho\Downloads\CAMARO\_photo session\Photos Jun 2024"),
}

OUTPUT_BASE = Path(__file__).resolve().parent.parent / "img"

VIDEO_SOURCE = Path(r"C:\Users\mdzho\Downloads\CAMARO\_photo session\video\best\DJI_0017_8MB.mp4")
VIDEO_OUTPUT = Path(__file__).resolve().parent.parent / "video" / "drone.mp4"

STANDARD_WIDTHS = [640, 960, 1280, 1920]
DETAIL_WIDTHS = [400, 800, 1280]

TIER_WIDTHS = {
    "hero": STANDARD_WIDTHS,
    "full": STANDARD_WIDTHS,
    "detail": DETAIL_WIDTHS,
}

WEBP_QUALITY = 80
WEBP_METHOD = 6
JPG_QUALITY = 82
LQIP_WIDTH = 20
LQIP_QUALITY = 20

FAVICON_FILES = {
    256: "android-chrome-256x256.png",
    192: "android-chrome-192x192.png",
    180: "apple-touch-icon.png",
    32:  "favicon-32x32.png",
    16:  "favicon-16x16.png",
}

# (name, source_key, relative_path, output_dir, tier)
IMAGES = [
    # HERO
    ("hero",             "2025.12",       "DSC_0493.jpg",   "hero",    "hero"),
    ("hero_mobile",      "2025.12",       "DSC_0497.jpg",   "hero",    "hero"),

    # FULL (panels + gallery + lightbox)
    ("profile_rooftop",  "2025.12",       "DSC_0533.jpg",   "gallery", "full"),
    ("front_zl1",        "2025.12",       "DSC_0497.jpg",   "gallery", "full"),
    ("rear_center",      "2025.12",       "DSC_0513.jpg",   "gallery", "full"),
    ("rear_quarter",     "2025.12",       "DSC_0514.jpg",   "gallery", "full"),
    ("rear_borla",       "2025.12",       "DSC_0517.jpg",   "gallery", "full"),
    ("night_taillights", "2025.12",       "DSC_0567.jpg",   "gallery", "full"),
    ("night_front",      "2025.12",       "DSC_0581.jpg",   "gallery", "full"),
    ("night_christmas",  "2025.12",       "DSC_0569.jpg",   "gallery", "full"),
    ("side_city",        "mobile.bg",     "DSC04836.jpg",   "gallery", "full"),
    ("side_mountains",   "mobile.bg",     "DSC04853.jpg",   "gallery", "full"),
    ("rear_camaro",      "mobile.bg",     "DSC04928.jpg",   "gallery", "full"),
    ("trio",             "photo_session", "DSC07178.jpg",   "gallery", "full"),

    # DETAIL (split-layout, never full-bleed)
    ("engine",           "2025.12",       "DSC_0530.JPG",   "gallery", "detail"),
    ("cockpit",          "mobile.bg",     "DSC04870.jpg",   "gallery", "detail"),
    ("zl1_grille",       "mobile.bg",     "DSC04891.jpg",   "gallery", "detail"),
    ("headlight",        "mobile.bg",     "DSC05000.jpg",   "gallery", "detail"),
    ("sill_plate",       "mobile.bg",     "DSC04880.jpg",   "gallery", "detail"),
]


def load_image(source_path):
    """Open image, auto-orient EXIF, ensure RGB."""
    img = Image.open(source_path)
    if source_path.suffix.lower() in (".jpg", ".jpeg"):
        img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA", "PA"):
        background = Image.new("RGB", img.size, (10, 10, 10))
        background.paste(img, mask=img.split()[-1])
        return background
    if img.mode != "RGB":
        return img.convert("RGB")
    return img


def process_image(name, source_path, output_dir, tier):
    """Process a single image: generate responsive variants + LQIP."""
    print(f"  Processing: {name} ({source_path.name}) [{tier}]")

    img = load_image(source_path)
    orig_w, orig_h = img.size
    aspect = orig_h / orig_w

    widths = TIER_WIDTHS[tier]
    out_dir = OUTPUT_BASE / output_dir

    results = {"name": name, "tier": tier, "variants": [], "lqip": None}
    smallest_variant = None

    for w in widths:
        if w > orig_w:
            w = orig_w  # Don't upscale

        h = round(w * aspect)
        resized = img.resize((w, h), Image.LANCZOS)

        # Track smallest for LQIP
        if smallest_variant is None:
            smallest_variant = resized

        # WebP variant
        webp_path = out_dir / f"{name}_{w}w.webp"
        resized.save(webp_path, "WEBP", quality=WEBP_QUALITY, method=WEBP_METHOD)
        webp_size = webp_path.stat().st_size

        results["variants"].append({
            "width": w,
            "height": h,
            "webp": str(webp_path.relative_to(OUTPUT_BASE.parent)),
            "size_kb": round(webp_size / 1024, 1),
        })

        print(f"    {w}w WebP: {round(webp_size / 1024)}KB")

    # JPG fallback — reuse last resized (largest width)
    jpg_path = out_dir / f"{name}_{resized.width}w.jpg"
    resized.save(jpg_path, "JPEG", quality=JPG_QUALITY, optimize=True)
    jpg_size = jpg_path.stat().st_size
    results["jpg_fallback"] = str(jpg_path.relative_to(OUTPUT_BASE.parent))
    print(f"    JPG fallback: {round(jpg_size / 1024)}KB")

    # LQIP from smallest variant (cheaper than from full-res)
    lqip_h = round(LQIP_WIDTH * aspect)
    lqip = smallest_variant.resize((LQIP_WIDTH, lqip_h), Image.LANCZOS)
    buf = io.BytesIO()
    lqip.save(buf, "WEBP", quality=LQIP_QUALITY)
    lqip_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    results["lqip"] = f"data:image/webp;base64,{lqip_b64}"
    print(f"    LQIP: {len(lqip_b64)} chars base64")

    return results


def generate_og_image(img):
    """Generate 1200x630 OG image, center-cropped."""
    print("  Generating OG image...")
    target_aspect = 1200 / 630
    orig_w, orig_h = img.size
    orig_aspect = orig_w / orig_h

    if orig_aspect > target_aspect:
        new_w = round(orig_h * target_aspect)
        left = (orig_w - new_w) // 2
        cropped = img.crop((left, 0, left + new_w, orig_h))
    else:
        new_h = round(orig_w / target_aspect)
        top = (orig_h - new_h) // 2
        cropped = img.crop((0, top, orig_w, top + new_h))

    cropped = cropped.resize((1200, 630), Image.LANCZOS)
    og_path = OUTPUT_BASE / "og-image.jpg"
    cropped.save(og_path, "JPEG", quality=85, optimize=True)
    print(f"    OG image: {round(og_path.stat().st_size / 1024)}KB")


def generate_favicon(img):
    """Generate favicon set from pre-loaded image, center-cropped to square."""
    print("  Generating favicon...")
    orig_w, orig_h = img.size
    size = min(orig_w, orig_h)
    left = (orig_w - size) // 2
    top = (orig_h - size) // 2
    square = img.crop((left, top, left + size, top + size))

    favicon_dir = OUTPUT_BASE / "favicon"
    # Resize from largest to smallest, reusing progressively
    prev = square
    for s in sorted(FAVICON_FILES.keys(), reverse=True):
        resized = prev.resize((s, s), Image.LANCZOS)
        resized.save(favicon_dir / FAVICON_FILES[s], "PNG")
        prev = resized
        print(f"    favicon {s}x{s}")

    # Generate .ico from the 32px version (already computed)
    img32 = square.resize((32, 32), Image.LANCZOS)
    img32.save(favicon_dir / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32)])
    print("    favicon.ico")


def extract_video_poster(video_path, output_path, timestamp_sec=3):
    """Extract a frame from video at given timestamp using OpenCV."""
    try:
        import cv2
    except ImportError:
        print("  WARNING: opencv-python not installed, skipping poster extraction")
        return

    print(f"  Extracting poster frame at {timestamp_sec}s...")
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"  WARNING: Could not open video: {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_num = int(fps * timestamp_sec)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)

    ret, frame = cap.read()
    cap.release()

    if ret:
        cv2.imwrite(str(output_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        size_kb = output_path.stat().st_size / 1024
        print(f"    Poster: {round(size_kb)}KB")
    else:
        print("  WARNING: Could not read frame from video")


def copy_video(source, dest):
    """Copy video file to output directory."""
    print(f"  Copying video ({round(source.stat().st_size / 1024 / 1024, 1)}MB)...")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    print(f"    Copied to {dest}")


def main():
    print("=== BUMBLEBEE - Image Pipeline ===\n")

    # Ensure output dirs exist
    (OUTPUT_BASE / "hero").mkdir(parents=True, exist_ok=True)
    (OUTPUT_BASE / "gallery").mkdir(parents=True, exist_ok=True)
    (OUTPUT_BASE / "favicon").mkdir(parents=True, exist_ok=True)

    all_results = []

    for name, source_key, rel_path, output_dir, tier in IMAGES:
        source = SOURCES[source_key] / rel_path
        if not source.exists():
            print(f"  WARNING: Source not found: {source}")
            continue
        result = process_image(name, source, output_dir, tier)
        all_results.append(result)

    # Load hero source once for OG + favicon
    hero_source = SOURCES["2025.12"] / "DSC_0493.jpg"
    if hero_source.exists():
        hero_img = load_image(hero_source)
        generate_og_image(hero_img)
        generate_favicon(hero_img)

    # Video: copy + extract poster
    if VIDEO_SOURCE.exists():
        copy_video(VIDEO_SOURCE, VIDEO_OUTPUT)
        poster_path = OUTPUT_BASE / "poster.jpg"
        extract_video_poster(VIDEO_SOURCE, poster_path)
    else:
        print(f"  WARNING: Video not found: {VIDEO_SOURCE}")

    # Write manifest with LQIP data for embedding in HTML
    manifest_path = OUTPUT_BASE / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n  Manifest written to {manifest_path}")

    print("\n=== Done! ===")


if __name__ == "__main__":
    main()
