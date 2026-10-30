import os, subprocess, wave
import numpy as np

SRC = "audio"
rng = np.random.default_rng(7)


def read_wav(path):
    with wave.open(path, "rb") as w:
        rate = w.getframerate()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64)
    return data, rate


def write_wav(path, data, rate):
    data = np.clip(data, -32768, 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(data.tobytes())


def add_noise(sig, snr_db):
    power = np.mean(sig ** 2)
    noise = rng.normal(0, np.sqrt(power / (10 ** (snr_db / 10))), len(sig))
    return sig + noise


def phone_quality(src, dst):
    tmp = dst + ".tmp.wav"
    subprocess.run(["ffmpeg", "-y", "-i", src, "-af", "highpass=f=300,lowpass=f=3400",
                    "-ar", "8000", "-ac", "1", "-c:a", "pcm_mulaw", tmp], check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-i", tmp, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", dst],
                   check=True, capture_output=True)
    os.remove(tmp)


for folder in ("audio_snr10", "audio_snr5", "audio_phone"):
    os.makedirs(folder, exist_ok=True)

for name in sorted(os.listdir(SRC)):
    if not name.endswith(".wav") or name.startswith("joined"):
        continue
    sig, rate = read_wav(os.path.join(SRC, name))
    write_wav(os.path.join("audio_snr10", name), add_noise(sig, 10), rate)
    write_wav(os.path.join("audio_snr5", name), add_noise(sig, 5), rate)
    phone_quality(os.path.join(SRC, name), os.path.join("audio_phone", name))
    print("made 3 versions of", name)