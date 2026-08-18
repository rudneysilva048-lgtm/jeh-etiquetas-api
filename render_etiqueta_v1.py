from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json, sys, os

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / "TEMPLATE_ETIQUETA_JEH_V1_CONFIG.json").read_text(encoding="utf-8"))
BASE = ROOT / CONFIG["background"]

def font_path(name):
    # Linux environment used by the renderer; fall back to DejaVu Sans Condensed.
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu") / name,
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"),
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError("Fonte fixa não encontrada.")

def fit_font(draw, text, max_width, preferred_size):
    size = preferred_size
    while size > 20:
        f = ImageFont.truetype(str(font_path("DejaVuSansCondensed-Bold.ttf")), size)
        bbox = draw.textbbox((0,0), text, font=f)
        if bbox[2] - bbox[0] <= max_width:
            return f
        size -= 1
    return ImageFont.truetype(str(font_path("DejaVuSansCondensed-Bold.ttf")), 20)

def render(data, output):
    img = Image.open(BASE).convert("RGB")
    draw = ImageDraw.Draw(img)

    fields = CONFIG["variable_fields"]

    title = data["protein_title"].strip().upper()
    f = fit_font(draw, title, fields["protein_title"]["max_width"], fields["protein_title"]["size"])
    draw.text(
        (fields["protein_title"]["x_center"], fields["protein_title"]["y"]),
        title, font=f, fill=(0,0,0), anchor="mm", align="center"
    )

    for i in range(1,4):
        value = data.get(f"ingredient_{i}", "")
        if value:
            spec = fields[f"ingredient_{i}"]
            f = fit_font(draw, value.upper(), spec["max_width"], spec["size"])
            draw.text((spec["x"], spec["y"]), value.upper(),
                      font=f, fill=(0,0,0), anchor="lm")

    fw = data.get("final_weight", "")
    if fw:
        spec = fields["final_weight"]
        f = fit_font(draw, fw, spec["max_width"], spec["size"])
        draw.text((spec["x"], spec["y"]), fw,
                  font=f, fill=(0,0,0), anchor="lm")

    date = data.get("manufacturing_date", "")
    if date:
        spec = fields["manufacturing_date"]
        f = fit_font(draw, date, spec["max_width"], spec["size"])
        draw.text((spec["x"], spec["y"]), date,
                  font=f, fill=(0,0,0), anchor="lm")

    img.save(output, quality=100, subsampling=0)

if __name__ == "__main__":
    # Example:
    # python render_etiqueta_v1.py output.png "FRANGO GRELHADO" "ARROZ BRANCO 100g" "FEIJÃO PRETO 100g" "ABOBRINHA" "500g" "14/08/2026"
    if len(sys.argv) != 8:
        raise SystemExit("Uso: render_etiqueta_v1.py SAIDA.png PROTEINA ING1 ING2 ING3 PESO DATA")
    data = {
        "protein_title": sys.argv[2],
        "ingredient_1": sys.argv[3],
        "ingredient_2": sys.argv[4],
        "ingredient_3": sys.argv[5],
        "final_weight": sys.argv[6],
        "manufacturing_date": sys.argv[7],
    }
    render(data, sys.argv[1])