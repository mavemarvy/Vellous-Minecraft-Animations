# Rendering the First Video

The first production test renders automatically with GitHub Actions.

## What it does

The **Render Minecraft Video** workflow:

1. installs Blender and FFmpeg on the GitHub runner;
2. creates an original 10-second procedural soundtrack;
3. builds a Minecraft-style village scene from code;
4. animates Steve, three zombies, flying wall debris and the camera;
5. renders a vertical 9:16 motion preview;
6. combines video and audio;
7. uploads the finished MP4 as a GitHub Actions artifact.

## First preview quality

The first render is intentionally **360x640 at 24 fps**. It is a motion/pipeline validation render so we can quickly inspect choreography before spending much longer rendering a production-quality 1080x1920 version.

## Preview on iPhone

1. Open this repository on GitHub.
2. Open **Actions**.
3. Open **Render Minecraft Video**.
4. Open the newest successful run.
5. Scroll to **Artifacts**.
6. Download **vellous-short-001-preview**.
7. Open the ZIP and play **vellous-short-001-preview.mp4**.

The artifact also contains the original WAV soundtrack and the generated Blender scene so later iterations can reuse them.
