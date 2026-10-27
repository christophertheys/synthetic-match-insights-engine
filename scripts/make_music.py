"""Generate a short copyright-free ambient bed for the demo film."""

from __future__ import annotations

import math
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "demo" / "score.wav"
SR = 44100
SECONDS = 110


def envelope(n: int, attack=0.08, release=0.18) -> np.ndarray:
    a = int(n * attack)
    r = int(n * release)
    env = np.ones(n)
    env[:a] = np.linspace(0, 1, a)
    env[-r:] = np.linspace(1, 0, r)
    return env


def tone(freq: float, n: int) -> np.ndarray:
    t = np.arange(n) / SR
    wave = (
        0.55 * np.sin(2 * math.pi * freq * t)
        + 0.28 * np.sin(2 * math.pi * freq * 2 * t)
        + 0.12 * np.sin(2 * math.pi * freq * 3 * t)
    )
    return wave * envelope(n)


def main() -> None:
    n = SR * SECONDS
    mix = np.zeros(n, dtype=np.float64)
    # Slow C-minor / E-flat lift, no percussion.
    chords = [
        (0, [130.81, 155.56, 196.00, 261.63]),
        (12, [146.83, 174.61, 220.00, 293.66]),
        (24, [174.61, 207.65, 261.63, 329.63]),
        (36, [130.81, 196.00, 246.94, 311.13]),
        (48, [155.56, 196.00, 233.08, 311.13]),
        (64, [130.81, 164.81, 196.00, 261.63]),
        (80, [174.61, 220.00, 261.63, 329.63]),
        (96, [130.81, 196.00, 261.63]),
    ]
    for start, freqs in chords:
        length = int(SR * 16)
        s = int(start * SR)
        e = min(n, s + length)
        pad = np.zeros(e - s)
        for f in freqs:
            pad += tone(f, e - s)
        pad /= max(1, len(freqs))
        mix[s:e] += pad * 0.22

    # Gentle high shimmer
    t = np.arange(n) / SR
    mix += 0.03 * np.sin(2 * math.pi * 784 * t) * (0.5 + 0.5 * np.sin(2 * math.pi * t / 11))

    peak = np.max(np.abs(mix)) or 1
    mix = 0.85 * mix / peak
    pcm = (mix * 32767).astype(np.int16)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
