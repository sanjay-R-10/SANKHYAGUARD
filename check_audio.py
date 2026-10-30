import csv, os, wave
import numpy as np

ids = [r["id"] for r in csv.DictReader(open("dataset_script.csv", encoding="utf-8"))]
FOLDERS = ["audio", "audio_snr10", "audio_snr5", "audio_phone"]
problems = 0

for folder in FOLDERS:
    if not os.path.isdir(folder):
        print(f"[{folder}] MISSING FOLDER"); problems += 1; continue
    found = {f[:-4] for f in os.listdir(folder) if f.endswith(".wav")}
    missing = [i for i in ids if i not in found]
    extra = sorted(found - set(ids))
    per_lang = {lang: sum(1 for i in ids if i.startswith(lang + "_") and i in found)
                for lang in ("en", "kn", "hi")}
    print(f"[{folder}] en={per_lang['en']} kn={per_lang['kn']} hi={per_lang['hi']}"
          f" | missing={len(missing)} | extra={len(extra)}")
    if missing:
        print("   missing:", ", ".join(missing)); problems += 1
    if extra:
        print("   extra (not in CSV):", ", ".join(extra))

print("\nClean clip details (audio/):")
for i in ids:
    path = os.path.join("audio", i + ".wav")
    if not os.path.exists(path):
        continue
    with wave.open(path, "rb") as w:
        rate, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
        sig = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float64)
    dur = n / rate
    rms = float(np.sqrt(np.mean(sig ** 2))) if n else 0.0
    flags = []
    if dur < 1.0: flags.append("under 1 s")
    if dur > 30.0: flags.append("over 30 s")
    if rate != 16000 or ch != 1: flags.append(f"format {rate} Hz, {ch} ch")
    if rms < 100: flags.append("almost silent")
    if flags:
        problems += 1
        print(f"   {i}: {dur:.1f}s  ->  " + ", ".join(flags))

print("\nRESULT:", "ALL OK" if problems == 0 else f"{problems} problem(s) above")
