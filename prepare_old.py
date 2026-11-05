from pathlib import Path
import subprocess

# Project folders
RAW_AUDIO = Path("raw_audio")
OUTPUT_AUDIO = Path("audio")

# FFmpeg location on your computer
FFMPEG = Path(
    r"C:\Users\sanja\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
)

# Supported audio formats
SUPPORTED_FORMATS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".ogg",
    ".flac",
    ".wma",
}


def prepare_audio():
    # Check input folder
    if not RAW_AUDIO.exists():
        print("ERROR: raw_audio folder not found.")
        return

    # Check FFmpeg
    if not FFMPEG.exists():
        print("ERROR: FFmpeg not found.")
        print("Check the FFmpeg path inside prepare.py.")
        return

    # Create output folder if needed
    OUTPUT_AUDIO.mkdir(exist_ok=True)

    # Find audio files
    audio_files = [
        file
        for file in RAW_AUDIO.iterdir()
        if file.is_file()
        and file.suffix.lower() in SUPPORTED_FORMATS
    ]

    if not audio_files:
        print("No audio files found in raw_audio.")
        return

    converted = 0
    skipped = 0
    failed = 0

    print(f"Found {len(audio_files)} audio files.")
    print()

    for input_file in audio_files:

        # Keep the original filename
        output_file = OUTPUT_AUDIO / (
            input_file.stem + ".wav"
        )

        # Do not overwrite existing converted files
        if output_file.exists():
            print(f"SKIPPED: {input_file.name}")
            skipped += 1
            continue

        command = [
            str(FFMPEG),
            "-i",
            str(input_file),
            "-ar",
            "16000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(output_file),
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print(f"CONVERTED: {input_file.name}")
                converted += 1

            else:
                print(f"FAILED: {input_file.name}")
                print(result.stderr)
                failed += 1

                # Remove incomplete output if created
                if output_file.exists():
                    output_file.unlink()

        except Exception as error:
            print(f"ERROR: {input_file.name}")
            print(error)
            failed += 1

    print()
    print("========== SUMMARY ==========")
    print(f"Converted: {converted}")
    print(f"Skipped:   {skipped}")
    print(f"Failed:    {failed}")
    print(f"Output:    {OUTPUT_AUDIO.resolve()}")


if __name__ == "__main__":
    prepare_audio()