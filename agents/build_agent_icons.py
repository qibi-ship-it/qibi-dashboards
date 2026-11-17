"""Qibi agent faces — ONE source for the Slack avatars and the Stream Deck keys (chosen by Marius 17 Nov 2026).

  csm        Q-Support (the Qibi face with its headset — Qibi's own icon)
  forecast   the Qibi face, one eye under a magnifying glass ("il examine les chiffres")
  estimatif  the Qibi face with « + = » eyes (the calculator)

Writes, next to this file:
  <agent>.svg / <agent>.png   Slack avatar: Qibi green on black, 512x512
  <agent>_mask.png            white on transparent — the Deck key builders tint it to the key's colour
A new agent: add its shapes to faces(), run this, copy agent_identity.py into its repo.
    python3 agents/build_agent_icons.py      (renders with headless Chrome — no extra library needed)
"""
import os
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
GREEN, BLACK = "#20ff00", "#0a0a0a"

SMILE = ("M192.06,294.41c-66.68,0-120.93-54.25-120.93-120.93h47.75c0,40.35,32.82,73.17,73.17,73.17s73.17-32.82,"
         "73.17-73.17h47.75c0,66.68-54.25,120.93-120.93,120.93")
SUPPORT = ("M230.4,221.69c14.26,0,25.82-11.56,25.82-25.82s-11.56-25.82-25.82-25.82-25.82,11.56-25.82,25.82,11.56,"
           "25.82,25.82,25.82ZM155.48,170.05c-14.26,0-25.82,11.56-25.82,25.82s11.56,25.82,25.82,25.82,25.82-11.56,"
           "25.82-25.82-11.56-25.82-25.82-25.82ZM314.28,139.4h-6.59c-6.34-12.27-16.56-24.24-29.85-34.49-24.57-18.97"
           "-55.38-29.41-86.75-29.41-53.73,0-99.27,30.68-116.53,63.91h-4.16c-11.84,0-21.43,9.6-21.43,21.43v70.07c0,"
           "11.84,9.6,21.43,21.43,21.43h15.66c11.84,0,21.43-9.6,21.43-21.43v-72.82c0-7.98-5.02-14.78-12.07-17.45,"
           "5.07-7.36,11.97-14.57,20.29-21,21.33-16.47,48.11-25.54,75.39-25.54s54.05,9.07,75.38,25.54c9.03,6.97,"
           "16.38,14.88,21.55,22.89-5.03,3.35-8.36,9.06-8.36,15.56v73.38c0,10.63,7.96,19.39,18.24,20.69-9.7,14.87"
           "-25.33,26.48-44.11,32.36-3.16-7.23-10.36-12.29-18.76-12.29h-29.39c-11.3,0-20.47,9.16-20.47,20.47v2.53c0,"
           "11.3,9.16,20.47,20.47,20.47h29.39c11.3,0,20.47-9.16,20.47-20.47v-1.5c23.33-7.04,42.46-22.08,53.14-41.38"
           "h5.63c11.53,0,20.87-9.34,20.87-20.87v-71.19c0-11.53-9.34-20.87-20.87-20.87Z")


def faces(c):
    smile = f'<path d="{SMILE}" fill="{c}"/>'
    return {
        "csm": f'<path d="{SUPPORT}" fill="{c}"/>',
        "forecast": (f'<g transform="translate(0,-22)"><circle cx="147.4" cy="134.03" r="30.54" fill="{c}"/>'
                     f'<circle cx="236.02" cy="126" r="54" fill="none" stroke="{c}" stroke-width="17"/>'
                     f'<circle cx="236.02" cy="126" r="34" fill="{c}"/>'
                     f'<line x1="276" y1="86" x2="318" y2="44" stroke="{c}" stroke-width="26" stroke-linecap="round"/></g>'
                     + smile),
        "estimatif": (f'<g fill="{c}"><rect x="117" y="121" width="61" height="26" rx="6"/>'
                      f'<rect x="134.5" y="103.5" width="26" height="61" rx="6"/>'
                      f'<rect x="205" y="106" width="62" height="22" rx="6"/>'
                      f'<rect x="205" y="140" width="62" height="22" rx="6"/></g>' + smile),
    }


def slack_svg(inner, px=512):
    s = px / 384.11 * 0.78
    off = (px - 384.11 * s) / 2
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {px} {px}" width="{px}" height="{px}">'
            f'<rect width="{px}" height="{px}" fill="{BLACK}"/>'
            f'<g transform="translate({off:.2f},{off:.2f}) scale({s:.5f})">{inner}</g></svg>')


def mask_svg(inner, px=768):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384.11 384.11" width="{px}" height="{px}" '
            f'style="display:block">{inner}</svg>')


def render(svg, png, px):
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "i.html")
        open(src, "w").write(f'<html><body style="margin:0;background:transparent">{svg}</body></html>')
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--default-background-color=00000000", f"--window-size={px},{px}",
                        f"--screenshot={png}", "file://" + src], check=True, capture_output=True, timeout=60)


if __name__ == "__main__":
    for name, inner in faces(GREEN).items():
        svg = slack_svg(inner)
        open(os.path.join(HERE, f"{name}.svg"), "w").write(svg)
        render(svg, os.path.join(HERE, f"{name}.png"), 512)
    for name, inner in faces("#ffffff").items():
        render(mask_svg(inner), os.path.join(HERE, f"{name}_mask.png"), 768)
    print("built:", ", ".join(faces(GREEN)))
