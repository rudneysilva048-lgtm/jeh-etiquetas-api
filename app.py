from flask import Flask, request, send_file, jsonify
from pathlib import Path
from datetime import datetime
import tempfile
import os

from render_etiqueta_v1 import render

app = Flask(__name__)


@app.get("/")
def health():
    return jsonify({
        "status": "online",
        "service": "jeh-etiquetas-api",
        "version": "v1"
    })


@app.post("/gerar-etiqueta")
def gerar_etiqueta():
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "erro": "JSON não enviado."
            }), 400

        protein_title = str(data.get("protein_title", "")).strip()

        if not protein_title:
            return jsonify({
                "erro": "protein_title é obrigatório."
            }), 400

        etiqueta_data = {
            "protein_title": protein_title,
            "ingredient_1": str(data.get("ingredient_1", "")).strip(),
            "ingredient_2": str(data.get("ingredient_2", "")).strip(),
            "ingredient_3": str(data.get("ingredient_3", "")).strip(),
            "final_weight": str(data.get("final_weight", "")).strip(),
            "manufacturing_date": str(
                data.get(
                    "manufacturing_date",
                    datetime.now().strftime("%d/%m/%Y")
                )
            ).strip()
        }

        temp_dir = tempfile.mkdtemp()
        output_file = Path(temp_dir) / "etiqueta.jpg"

        render(etiqueta_data, output_file)

        return send_file(
            output_file,
            mimetype="image/jpeg",
            as_attachment=False,
            download_name="etiqueta.jpg"
        )

    except Exception as e:
        return jsonify({
            "erro": "Erro ao gerar etiqueta.",
            "detalhes": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
