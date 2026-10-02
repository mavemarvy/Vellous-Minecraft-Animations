#!/usr/bin/env python3
"""Generate an original procedural 10-second soundtrack for Short 001.
No third-party songs or samples are used.
"""
import math
import random
import struct
import wave
from pathlib import Path

SR = 44100
DURATION = 10.0
COUNT = int(SR * DURATION)
OUT = Path("projects/short-001-zombie-fight/exports/original-preview-audio.wav")
OUT.parent.mkdir(parents=True, exist_ok=True)
random.seed(1701)

left = [0.0] * COUNT
right = [0.0] * COUNT

def tone(start, duration, freq, amp, pan=0.0, decay=2.0):
    a = max(0, int(start * SR))
    b = min(COUNT, int((start + duration) * SR))
    for i in range(a, b):
        t = (i - a) / SR
        env = math.exp(-decay * t / max(duration, 0.001))
        v = math.sin(2 * math.pi * freq * t) * amp * env
        left[i] += v * (1.0 - max(0.0, pan))
        right[i] += v * (1.0 + min(0.0, pan))

def noise(start, duration, amp, pan=0.0, decay=5.0):
    a = max(0, int(start * SR))
    b = min(COUNT, int((start + duration) * SR))
    sm = 0.0
    for i in range(a, b):
        t = (i - a) / SR
        env = math.exp(-decay * t / max(duration, 0.001))
        raw = random.uniform(-1.0, 1.0)
        sm = 0.82 * sm + 0.18 * raw
        v = (raw - sm) * amp * env
        left[i] += v * (1.0 - max(0.0, pan))
        right[i] += v * (1.0 + min(0.0, pan))

def whoosh(start, duration, amp, pan=0.0):
    a = max(0, int(start * SR))
    b = min(COUNT, int((start + duration) * SR))
    sm = 0.0
    for i in range(a, b):
        t = (i - a) / SR
        p = t / max(duration, 0.001)
        env = math.sin(math.pi * min(1.0, p)) ** 1.5
        raw = random.uniform(-1.0, 1.0)
        sm = 0.90 * sm + 0.10 * raw
        v = (raw - sm) * amp * env
        left[i] += v * (1.0 - max(0.0, pan))
        right[i] += v * (1.0 + min(0.0, pan))

def impact(at, strength=1.0, pan=0.0):
    tone(at, 0.35, 48, 0.34 * strength, pan, 6.0)
    tone(at, 0.16, 96, 0.17 * strength, pan, 8.0)
    noise(at, 0.20, 0.18 * strength, pan, 9.0)

# Original low cinematic pulse bed.
for start, root in [(0,55.0),(2,49.0),(4,61.74),(6,55.0),(8,46.25)]:
    for ratio in (1.0, 1.5, 2.0):
        tone(start, 2.1, root * ratio, 0.028, decay=0.75)

for beat in [x * 0.5 for x in range(20)]:
    tone(beat, 0.15, 62, 0.060, decay=8.0)

# Scene-synchronized effects.
whoosh(0.00, 0.65, 0.24, -0.1)
impact(0.12, 1.0)
noise(0.15, 0.85, 0.08, decay=3.0)
impact(1.35, 0.62, -0.2)
whoosh(2.15, 0.35, 0.10, 0.2)
noise(2.60, 0.75, 0.03, decay=1.8)
whoosh(4.10, 0.32, 0.18, 0.2)
whoosh(4.85, 0.55, 0.24, -0.2)
whoosh(6.05, 0.30, 0.26, 0.25)
impact(6.30, 1.15, 0.25)
whoosh(6.65, 0.34, 0.28, -0.25)
impact(6.95, 1.25, -0.2)
whoosh(7.20, 0.70, 0.16, 0.45)
tone(8.10, 1.7, 146.83, 0.030, decay=0.65)
tone(8.10, 1.7, 220.00, 0.022, decay=0.65)

peak = max(max(abs(v) for v in left), max(abs(v) for v in right), 1e-9)
gain = min(0.90 / peak, 1.0)

with wave.open(str(OUT), "wb") as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(SR)
    data = bytearray()
    for l, r in zip(left, right):
        lv = max(-32767, min(32767, int(l * gain * 32767)))
        rv = max(-32767, min(32767, int(r * gain * 32767)))
        data.extend(struct.pack("<hh", lv, rv))
    wf.writeframes(data)

print(f"Generated {OUT}")
