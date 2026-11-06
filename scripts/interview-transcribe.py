#!/usr/bin/env python3
"""Live interview transcriber — local offline whisper, no audio leaves the machine.

Usage:
    ~/.venvs/interview/bin/python scripts/interview-transcribe.py
    ~/.venvs/interview/bin/python scripts/interview-transcribe.py --list-devices
    ~/.venvs/interview/bin/python scripts/interview-transcribe.py --device 1 --model small
    ~/.venvs/interview/bin/python scripts/interview-transcribe.py --file some_audio.wav
"""
import argparse, datetime, queue, re, sys, threading, time, wave, io
import numpy as np

SR = 16000


def banner(text):
    print(f"\n=== {text} ===", flush=True)


def list_devices():
    import sounddevice as sd
    print(sd.query_devices())


def load_model(name):
    from faster_whisper import WhisperModel
    t0 = time.time()
    model = WhisperModel(name, device="cpu", compute_type="int8")
    print(f"model '{name}' ready in {time.time()-t0:.0f}s", flush=True)
    return model


def transcribe_file(model, path, lang, prompt=""):
    import subprocess
    pcm = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path,
         "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
        capture_output=True, check=True).stdout
    audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
    segs, _ = model.transcribe(audio, language=lang, beam_size=1,
                               condition_on_previous_text=False,
                               initial_prompt=prompt)
    for s in segs:
        ts = str(datetime.timedelta(seconds=int(s.start)))
        print(f"[{ts}] {s.text.strip()}")


def rms(x):
    return float(np.sqrt(np.mean(x * x))) if len(x) else 0.0


def stream_loop(model, args):
    import sounddevice as sd
    dev = None if args.device is None else int(args.device)
    out = open(args.out, "a", encoding="utf-8")
    out.write(f"\n# session started {datetime.datetime.now().isoformat(timespec='seconds')}\n")
    out.flush()
    banner(f"listening in {args.chunk}s slices — Ctrl+C to stop")
    start_wall = time.time()
    offset = 0.0
    last_text = ""
    while True:
        x = sd.rec(int(args.chunk * SR), samplerate=SR, channels=1,
                    dtype="float32", device=dev)[:, 0]
        sd.wait()
        if rms(x) < max(args.rms_threshold, 3e-4):
            offset += args.chunk
            continue
        segs, info = model.transcribe(
            x, language=args.lang, beam_size=1,
            condition_on_previous_text=False, no_speech_threshold=0.6,
            initial_prompt=args.prompt)
        for s in segs:
            text = s.text.strip()
            if not text or text == last_text:
                continue
            last_text = text
            wall = datetime.datetime.fromtimestamp(start_wall + offset + s.start)
            line = f"[{wall.strftime('%H:%M:%S')}] {text}"
            print(line, flush=True)
            out.write(line + "\n")
            out.flush()
        offset += args.chunk
        lag = time.time() - start_wall - offset
        if lag > args.chunk:
            print(f"[warning] {lag:.0f}s behind live audio — raise --chunk or use --model tiny", file=sys.stderr)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--device", help="input device index (see --list-devices)")
    p.add_argument("--list-devices", action="store_true")
    p.add_argument("--model", default="base", choices=["tiny", "base", "small"])
    p.add_argument("--lang", default="en")
    p.add_argument("--chunk", type=float, default=4.0)
    p.add_argument("--overlap", type=float, default=0.8)
    p.add_argument("--rms-threshold", type=float, default=0.0015)
    p.add_argument("--prompt", default=(
        "Banks Dada, Webawesome Consult, MPLC, Simpro, BigChange, business analyst, "
        "requirements, stakeholders, Claude, Codex, RPA, Azure, Salesforce, Dynamics 365, "
        "NHS Professionals, HMRC, Virgin Active, discovery, UAT, backlog."))
    p.add_argument("--file", help="transcribe a file once instead of streaming")
    p.add_argument("--out", default=f"interview-{datetime.date.today().isoformat()}.txt")
    args = p.parse_args()

    if args.list_devices:
        list_devices()
        return
    model = load_model(args.model)
    if args.file:
        transcribe_file(model, args.file, args.lang, args.prompt)
        return
    try:
        stream_loop(model, args)
    except KeyboardInterrupt:
        banner("stopped")


if __name__ == "__main__":
    main()
