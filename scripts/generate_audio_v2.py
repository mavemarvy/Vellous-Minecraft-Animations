#!/usr/bin/env python3
from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

RATE = 44100
DUR = 5.0
N = int(RATE * DUR)
OUT = Path("projects/short-001-zombie-fight/exports/v2-preview-audio.wav")
OUT.parent.mkdir(parents=True, exist_ok=True)
random.seed(2202)

L = [0.0] * N
R = [0.0] * N

def clamp(x: float) -> float:
    return max(-1.0, min(1.0, x))

def add_tone(start, dur, freq, amp, decay=2.5, pan=0.0, wobble=0.0):
    i0 = max(0, int(start * RATE))
    i1 = min(N, int((start + dur) * RATE))
    for i in range(i0, i1):
        t = (i - i0) / RATE
        f = freq * (1 + wobble * math.sin(2 * math.pi * 4 * t))
        env = math.exp(-decay * t / max(dur, 1e-5))
        s = math.sin(2 * math.pi * f * t) * amp * env
        L[i] += s * (1 - max(0, pan))
        R[i] += s * (1 + min(0, pan))

def add_noise(start, dur, amp, decay=5.0, pan=0.0):
    i0 = max(0, int(start * RATE))
    i1 = min(N, int((start + dur) * RATE))
    prev = 0.0
    for i in range(i0, i1):
        t = (i - i0) / RATE
        env = math.exp(-decay * t / max(dur, 1e-5))
        raw = random.uniform(-1.0, 1.0)
        prev = 0.85 * prev + 0.15 * raw
        s = (raw - prev) * amp * env
        L[i] += s * (1 - max(0, pan))
        R[i] += s * (1 + min(0, pan))

def add_impact(t, strength=1.0, pan=0.0):
    add_tone(t, 0.35, 52, 0.32 * strength, decay=6, pan=pan)
    add_tone(t, 0.14, 104, 0.16 * strength, decay=8, pan=pan)
    add_noise(t, 0.20, 0.18 * strength, decay=9, pan=pan)

for beat in [x * 0.5 for x in range(10)]:
    add_tone(beat, 0.18, 60, 0.06, decay=8)

for start, chord in [
    (0.0, (55, 82.41, 110)),
    (1.2, (49, 73.42, 98)),
    (2.2, (61.74, 92.5, 123.47)),
    (3.2, (55, 82.41, 110)),
    (4.0, (46.25, 69.3, 92.5)),
]:
    for f in chord:
        add_tone(start, 1.1, f, 0.03, decay=0.9)

add_noise(0.05, 0.55, 0.14, decay=3.5)
add_impact(0.10, 1.05)
add_impact(0.85, 0.70, pan=-0.2)
add_noise(0.95, 0.35, 0.06, decay=4.0)
add_noise(1.60, 0.32, 0.05, decay=3.0, pan=0.2)
add_noise(1.95, 0.22, 0.10, decay=6.0, pan=0.2)
add_noise(2.35, 0.24, 0.12, decay=7.0, pan=-0.15)
add_impact(2.62, 1.25, pan=-0.1)
add_noise(2.80, 0.45, 0.07, decay=4.0, pan=-0.3)
add_tone(4.00, 0.80, 146.83, 0.03, decay=1.2, wobble=0.02)
add_tone(4.00, 0.80, 220.00, 0.022, decay=1.2, wobble=0.02)

peak = max(max(abs(x) for x in L), max(abs(x) for x in R), 1e-6)
gain = 0.92 / peak

with wave.open(str(OUT), 'wb') as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(RATE)
    frames = bytearray()
    for l, r in zip(L, R):
        frames.extend(struct.pack('<hh', int(clamp(l * gain) * 32767), int(clamp(r * gain) * 32767)))
    wf.writeframes(frames)

print(f"Generated {OUT}")
