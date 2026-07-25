#!/usr/bin/env python3
"""
Otimiza os assets do site: gera AVIF + WebP em múltiplas larguras
a partir dos PNGs originais, além de um LQIP (placeholder borrado em base64).

Uso:  python3 otimizar-assets.py <pasta-origem> <pasta-destino>
"""
import sys, os, io, base64, json
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else "assets-originais"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets"

# nome: (larguras alvo, qualidade)
PLANO = {
    "ceramica":        ([640, 1280, 1920], 62),
    "fibras":          ([640, 1280, 1920], 62),
    "madeira":         ([640, 1280, 1920], 62),
    "bijuterias":      ([640, 1280, 1920], 62),
    "bonito":          ([640, 1280, 1920], 62),
    "bird-1":          ([640, 1280, 1920], 62),
    "bird-2":          ([480, 960, 1440],  62),
    "bird-3":          ([480, 960, 1440],  62),
    "bird-4":          ([416, 832],        68),
    "bird-asset":      ([960, 1920],       62),
    "bg":              ([1280, 2000],      55),
    "museu-da-pessoa": ([300, 600],        80),
}

os.makedirs(OUT, exist_ok=True)
manifesto = {}

for nome, (larguras, q) in PLANO.items():
    src = os.path.join(SRC, nome + ".png")
    if not os.path.exists(src):
        print(f"  !! nao encontrado: {src}")
        continue
    im = Image.open(src)
    tem_alpha = im.mode in ("RGBA", "LA") or "transparency" in im.info
    im = im.convert("RGBA" if tem_alpha else "RGB")
    w0, h0 = im.size
    gerados = []

    for w in larguras:
        if w > w0:
            w = w0
        h = round(h0 * w / w0)
        red = im.resize((w, h), Image.LANCZOS)

        p_webp = os.path.join(OUT, f"{nome}-{w}.webp")
        red.save(p_webp, "WEBP", quality=q, method=6)

        p_avif = os.path.join(OUT, f"{nome}-{w}.avif")
        try:
            red.save(p_avif, "AVIF", quality=max(q - 10, 35), speed=4)
        except Exception as e:
            p_avif = None
            print(f"  (avif falhou em {nome}-{w}: {e})")

        gerados.append((w, p_webp, p_avif))

    # LQIP: 20px de largura, embutido como data URI
    lq = im.convert("RGB").resize((20, max(1, round(h0 * 20 / w0))), Image.LANCZOS)
    buf = io.BytesIO()
    lq.save(buf, "WEBP", quality=40)
    manifesto[nome] = {
        "original": f"{w0}x{h0}",
        "larguras": [g[0] for g in gerados],
        "lqip": "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode(),
    }

    orig_kb = os.path.getsize(src) / 1024
    novo_kb = os.path.getsize(gerados[-1][1]) / 1024
    avif_kb = os.path.getsize(gerados[-1][2]) / 1024 if gerados[-1][2] else 0
    print(f"{nome:18s} {orig_kb:9.0f} KB  ->  webp {novo_kb:7.0f} KB | avif {avif_kb:7.0f} KB")

with open(os.path.join(OUT, "manifesto.json"), "w") as f:
    json.dump(manifesto, f, indent=2)

total_orig = sum(os.path.getsize(os.path.join(SRC, n + ".png")) for n in PLANO
                 if os.path.exists(os.path.join(SRC, n + ".png")))
total_novo = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT)
                 if f.endswith((".webp", ".avif")))
print(f"\nTotal PNG: {total_orig/1e6:.1f} MB  ->  Total otimizado (todas as variantes): {total_novo/1e6:.1f} MB")
