from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
from datetime import datetime
import json
import sys
import os
import reportlab


ROOT = Path(__file__).resolve().parent

CONFIG = json.loads(
    (
        ROOT / "TEMPLATE_ETIQUETA_JEH_V1_CONFIG.json"
    ).read_text(encoding="utf-8-sig")
)

BASE = ROOT / CONFIG["background"]


def font_path(name):
    """
    Localiza uma fonte TTF de forma independente do sistema operacional.

    Primeiro tenta a fonte solicitada no projeto.
    Depois tenta fontes do sistema.
    Por fim usa a fonte VeraBd que vem dentro do ReportLab.
    """

    candidates = [
        ROOT / name,

        Path("/usr/share/fonts/truetype/dejavu") / name,
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),

        Path(reportlab.__file__).resolve().parent / "fonts" / "VeraBd.ttf",
        Path(reportlab.__file__).resolve().parent / "fonts" / "Vera.ttf",
    ]

    for p in candidates:
        if p.exists():
            return p

    raise FileNotFoundError(
        "Nenhuma fonte TTF disponível foi encontrada no servidor."
    )


def fit_font(draw, text, max_width, preferred_size):
    """
    Escolhe o maior tamanho de fonte que caiba na largura definida.
    """

    size = int(preferred_size)

    while size > 20:
        f = ImageFont.truetype(
            str(font_path("DejaVuSansCondensed-Bold.ttf")),
            size
        )

        bbox = draw.textbbox(
            (0, 0),
            text,
            font=f
        )

        width = bbox[2] - bbox[0]

        if width <= max_width:
            return f

        size -= 1

    return ImageFont.truetype(
        str(font_path("DejaVuSansCondensed-Bold.ttf")),
        20
    )


def render(data, output):

    # ---------------------------------------------------------
    # ÁREA REAL DA ETIQUETA
    # Remove o espaço branco externo da imagem-base.
    # ---------------------------------------------------------

    source = Image.open(BASE).convert("RGB")

    crop_box = (
        176,
        2204,
        2876,
        4204
    )

    img = source.crop(crop_box)

    # ---------------------------------------------------------
    # DIMENSÃO FINAL DA IMAGEM
    # 100 x 80 mm / proporção 5:4
    # ---------------------------------------------------------

    FINAL_WIDTH = 1402
    FINAL_HEIGHT = 1122

    # Mantém a arte inteira e adapta somente a dimensão final.
    img = img.resize(
        (FINAL_WIDTH, FINAL_HEIGHT),
        Image.Resampling.LANCZOS
    )
    
    img = img.filter(
    ImageFilter.UnsharpMask(
        radius=1.2,
        percent=600,
        threshold=0
    )
)
    
    img = img.filter(
    ImageFilter.UnsharpMask(
        radius=1.0,
        percent=400,
        threshold=0
    )
)

    draw = ImageDraw.Draw(img)

    fields = CONFIG["variable_fields"]

    # Fatores usados para transportar as coordenadas
    # existentes da imagem original para a nova dimensão.
    SCALE_X = FINAL_WIDTH / 738
    SCALE_Y = FINAL_HEIGHT / 507

    # ---------------------------------------------------------
    # PROTEÍNA
    # ---------------------------------------------------------

    title = str(
        data.get("protein_title", "")
    ).strip().upper()

    if title and "protein_title" in fields:

        spec = fields["protein_title"]

        f = fit_font(
            draw,
            title,
            int(spec["max_width"] * SCALE_X),
            int(spec["size"] * SCALE_X)
        )

        draw.text(
            (
                int(spec["x_center"] * SCALE_X),
                int((spec["y"] - 546) * SCALE_Y)
            ),
            title,
            font=f,
            fill=(0, 0, 0),
            anchor=spec.get("anchor", "mm"),
            align=spec.get("align", "center")
        )

    # ---------------------------------------------------------
    # INGREDIENTES
    # ---------------------------------------------------------

    for i in range(1, 4):

        key = f"ingredient_{i}"

        value = str(
            data.get(key, "")
        ).strip()

        if not value:
            continue

        if key not in fields:
            continue

        spec = fields[key]

        text = value.upper()

        f = fit_font(
            draw,
            text,
            int(spec["max_width"] * SCALE_X),
            int(spec["size"] * SCALE_X)
        )

        draw.text(
            (
                int(spec["x"] * SCALE_X),
                int((spec["y"] - 546) * SCALE_Y)
            ),
            text,
            font=f,
            fill=(0, 0, 0),
            anchor=spec.get("anchor", "lm")
        )

    # ---------------------------------------------------------
    # PESO FINAL
    # ---------------------------------------------------------

    fw = str(
        data.get("final_weight", "")
    ).strip()

    if fw and "final_weight" in fields:

        spec = fields["final_weight"]

        f = fit_font(
            draw,
            fw,
            int(spec["max_width"] * SCALE_X),
            int(spec["size"] * SCALE_X)
        )

        draw.text(
            (
                int(spec["x"] * SCALE_X),
                int((spec["y"] - 546) * SCALE_Y)
            ),
            fw,
            font=f,
            fill=(0, 0, 0),
            anchor=spec.get("anchor", "lm")
        )

    # ---------------------------------------------------------
    # DATA DE FABRICAÇÃO
    # ---------------------------------------------------------

    date = str(
        data.get("manufacturing_date", "")
    ).strip()

    if date and "manufacturing_date" in fields:

        spec = fields["manufacturing_date"]

        f = fit_font(
            draw,
            date,
            int(spec["max_width"] * SCALE_X),
            int(spec["size"] * SCALE_X)
        )

        draw.text(
            (
                int(spec["x"] * SCALE_X),
                int((spec["y"] - 546) * SCALE_Y)
            ),
            date,
            font=f,
            fill=(0, 0, 0),
            anchor=spec.get("anchor", "lm")
        )

    # ---------------------------------------------------------
    # SALVAR
    # ---------------------------------------------------------

    img.save(
        output,
        quality=100,
        subsampling=0,
        dpi=(300, 300)
    )


if __name__ == "__main__":

    if len(sys.argv) != 8:
        raise SystemExit(
            "Uso: render_etiqueta_v1.py "
            "SAIDA.png PROTEINA ING1 ING2 ING3 PESO DATA"
        )

    data = {
        "protein_title": sys.argv[2],
        "ingredient_1": sys.argv[3],
        "ingredient_2": sys.argv[4],
        "ingredient_3": sys.argv[5],
        "final_weight": sys.argv[6],
        "manufacturing_date": sys.argv[7],
    }

    render(
        data,
        sys.argv[1]
    )
