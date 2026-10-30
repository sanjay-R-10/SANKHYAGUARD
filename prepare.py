import os, subprocess

RAW, OUT = "raw_audio", "audio"
EXTS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".mp4", ".opus", ".amr"}
os.makedirs(OUT, exist_ok=True)

converted = skipped = failed = 0
for name in sorted(os.listdir(RAW)):
    base, ext = os.path.splitext(name)
    if ext.lower() not in EXTS:
        continue
    dst = os.path.join(OUT, base + ".wav")
    if os.path.exists(dst):
        skipped += 1
        continue
    r = subprocess.run(["ffmpeg", "-y", "-i", os.path.join(RAW, name),
                        "-ac", "1", "-ar", "16000", dst], capture_output=True)
    if r.returncode == 0:
        converted += 1
    else:
        failed += 1
        print("FAILED:", name)
print(f"Converted: {converted}, Skipped (already done): {skipped}, Failed: {failed}")
