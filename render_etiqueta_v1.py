from PIL import Image, ImageDraw, ImageFont
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


def crop_to_label(img):
    """
    Localiza automaticamente a área real da etiqueta dentro do
    canvas 738x1600, removendo apenas as áreas externas em branco.

    Não altera o desenho da etiqueta.
    """

    gray = img.convert("L")

    # Pixels abaixo deste valor são considerados conteúdo da etiqueta.
    threshold = 245

    # Detecta pixels que não são praticamente brancos.
    mask = gray.point(
        lambda p: 255 if p < threshold else 0
    )

    bbox = mask.getbbox()

    # Segurança: se não encontrar conteúdo, mantém a imagem original.
    if bbox is None:
        return img

    left, top, right, bottom = bbox

    return img.crop(
        (left, top, right, bottom)
    )


def prepare_for_printer(img):
    """
    Prepara a etiqueta para o aplicativo da impressora.

    Saída obrigatória:
    100 x 80 pixels.

    A proporção original é preservada.
    Nunca estica a imagem de forma independente nos eixos.
    """

    TARGET_WIDTH = 100
    TARGET_HEIGHT = 80

    # Cria uma tela branca exatamente 100x80.
    output = Image.new(
        "RGB",
        (TARGET_WIDTH, TARGET_HEIGHT),
        (255, 255, 255)
    )

    # Redimensiona mantendo a proporção.
    copy = img.copy()

    copy.thumbnail(
        (TARGET_WIDTH, TARGET_HEIGHT),
        Image.Resampling.LANCZOS
    )

    # Centraliza a etiqueta.
    x = (TARGET_WIDTH - copy.width) // 2
    y = (TARGET_HEIGHT - copy.height) // 2

    output.paste(
        copy,
        (x, y)
    )

    return output


def render(data, output):

    img = Image.open(BASE).convert("RGB")
    draw = ImageDraw.Draw(img)

    fields = CONFIG["variable_fields"]

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
            spec["max_width"],
            spec["size"]
        )

        draw.text(
            (
                spec["x_center"],
                spec["y"]
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
            spec["max_width"],
            spec["size"]
        )

        draw.text(
            (
                spec["x"],
                spec["y"]
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
            spec["max_width"],
            spec["size"]
        )

        draw.text(
            (
                spec["x"],
                spec["y"]
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
            spec["max_width"],
            spec["size"]
        )

        draw.text(
            (
                spec["x"],
                spec["y"]
            ),
            date,
            font=f,
            fill=(0, 0, 0),
            anchor=spec.get("anchor", "lm")
        )

    # ---------------------------------------------------------
    # PREPARAÇÃO PARA IMPRESSORA
    # ---------------------------------------------------------

    # 1. Remove o espaço branco externo do canvas original.
    label = crop_to_label(img)

    # 2. Converte a etiqueta para exatamente 100x80.
    final_image = prepare_for_printer(label)

    # ---------------------------------------------------------
    # SALVAR
    # ---------------------------------------------------------

    final_image.save(
        output,
        format="PNG",
        optimize=True
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
