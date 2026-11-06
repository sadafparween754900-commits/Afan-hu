
import os
import math
import wave
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
import imageio.v2 as imageio

W, H, FPS = 720, 1280, 20
OUT = Path("output")
OUT.mkdir(exist_ok=True)

story = [
    "Ek jungle mein Chiku naam ka khargosh rehta tha.",
    "Ek din use ek chhota pakshi mila.",
    "Pakshi ud nahi paa raha tha.",
    "Chiku ne apne doston ki madad se use bachaya.",
    "Sabne Chiku ki bahaduri ki tareef ki.",
    "Seekh: Hamesha doosron ki madad karo."
]

def font(size):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    return ImageFont.truetype(path, size)

def make_frame(t, text, scene):
    im = Image.new("RGB", (W, H), (135, 205, 245))
    d = ImageDraw.Draw(im)

    # Sky and sun
    d.ellipse((540, 80, 650, 190), fill=(255, 220, 60))

    # Green hills
    d.polygon([(0, 700), (180, 450), (360, 700)], fill=(80, 160, 90))
    d.polygon([(250, 700), (500, 430), (720, 700)], fill=(60, 145, 75))
    d.rectangle((0, 700, W, H), fill=(65, 170, 80))

    # Tree
    d.rectangle((80, 550, 120, 800), fill=(110, 65, 35))
    d.ellipse((30, 440, 170, 610), fill=(30, 125, 55))

    # Animated bunny
    x = 350 + int(20 * math.sin(t * 2))
    y = 780 + int(10 * math.sin(t * 5))

    d.ellipse((x-70, y-130, x+70, y+70),
              fill="white", outline="black", width=4)

    d.ellipse((x-45, y-250, x-10, y-100),
              fill="white", outline="black", width=3)
    d.ellipse((x+10, y-250, x+45, y-100),
              fill="white", outline="black", width=3)

    d.ellipse((x-45, y-190, x+45, y-90),
              fill="white", outline="black", width=3)

    d.ellipse((x-22, y-155, x-12, y-145), fill="black")
    d.ellipse((x+12, y-155, x+22, y-145), fill="black")
    d.ellipse((x-7, y-130, x+7, y-120), fill="pink")

    # Bird
    if scene >= 2:
        d.ellipse((520, 620, 600, 690), fill="yellow", outline="black", width=3)
        d.ellipse((565, 635, 575, 645), fill="black")
        d.polygon([(590, 650), (625, 660), (590, 670)], fill="orange")

    # Header
    d.rounded_rectangle((20, 20, 700, 120), radius=20, fill=(20, 60, 85))
    d.text((360, 70), "CHIKU CARTOON STORY",
           font=font(30), fill="white", anchor="mm")

    # Subtitle
    d.rounded_rectangle((20, 980, 700, 1190),
                        radius=25, fill="white", outline="black", width=3)

    words = text.split()
    lines = []
    line = ""
    for word in words:
        test = (line + " " + word).strip()
        if d.textbbox((0, 0), test, font=font(28))[2] < 620:
            line = test
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)

    for i, line in enumerate(lines[:4]):
        d.text((360, 1030 + i*42), line,
               font=font(28), fill="black", anchor="mm")

    return np.array(im)

def make_music(path, duration):
    rate = 22050
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)

        samples = bytearray()
        notes = [261, 329, 392, 329, 293, 349, 440, 349]

        for i in range(rate * duration):
            t = i / rate
            freq = notes[int(t / 0.5) % len(notes)]
            value = int(1200 * math.sin(2 * math.pi * freq * t))
            samples.extend(value.to_bytes(2, "little", signed=True))

        f.writeframes(samples)

def main():
    narration = " ".join(story)
    voice = OUT / "voice.mp3"
    music = OUT / "music.wav"
    silent = OUT / "cartoon.mp4"
    final = OUT / "final_video.mp4"

    print("Hindi voice generating...")
    gTTS(text=narration, lang="hi").save(str(voice))

    print("Cartoon animation generating...")
    duration = 36

    writer = imageio.get_writer(
        str(silent), fps=FPS, codec="libx264"
    )

    try:
        for frame_no in range(FPS * duration):
            t = frame_no / FPS
            scene = min(5, int(t / 6))
            frame = make_frame(t, story[scene], scene)
            writer.append_data(frame)
    finally:
        writer.close()

    print("Background music generating...")
    make_music(music, duration)

    print("Final video creating...")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(silent),
        "-i", str(voice),
        "-i", str(music),
        "-filter_complex",
        "[1:a]volume=1.0[v];[2:a]volume=0.12[m];[v][m]amix=inputs=2:duration=first[a]",
        "-map", "0:v:0",
        "-map", "[a]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(final)
    ], check=True)

    print("SUCCESS! Video ready:", final)

if __name__ == "__main__":
    main()
