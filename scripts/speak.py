#!/usr/bin/env python3
"""Speak text aloud with the macOS voice — morning briefs, mock-interview prompts.

Usage:
    python3 scripts/speak.py --file /tmp/brief.txt
    echo "Hello Banks" | python3 scripts/speak.py
    python3 scripts/speak.py --voices
Voice: --voice flag or AIOS_VOICE env var (default Daniel). No-op off macOS.
"""
import argparse, os, shutil, subprocess, sys


def voices():
    out = subprocess.run(["say", "-v", "?"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if "en_" in line:
            print(line)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("text", nargs="?", help="text to speak, or '-' for stdin")
    p.add_argument("--file", help="read text from a file instead")
    p.add_argument("--voice", default=os.environ.get("AIOS_VOICE", "Daniel"))
    p.add_argument("--rate", type=int, default=190)
    p.add_argument("--voices", action="store_true")
    args = p.parse_args()

    if not shutil.which("say"):
        print("speak: 'say' not found (not macOS?) — skipped", file=sys.stderr)
        return
    if args.voices:
        voices()
        return
    if args.file:
        text = open(args.file, encoding="utf-8").read()
    elif args.text == "-":
        text = sys.stdin.read()
    elif args.text:
        text = args.text
    else:
        p.error("give text, '-' for stdin, or --file")
    text = " ".join(text.split())
    subprocess.run(["say", "-v", args.voice, "-r", str(args.rate), text])


if __name__ == "__main__":
    main()
