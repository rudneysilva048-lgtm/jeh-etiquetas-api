from flask import Flask, request, send_file, jsonify
from pathlib import Path
from datetime import datetime
import tempfile
import os
import uuid

from render_etiqueta_v1 import render

app = Flask(__name__)

# Diretório temporário onde as etiquetas geradas ficarão disponíveis
ETIQUETAS_DIR = Path(tempfile.gettempdir()) / "jeh_etiquetas"
ETIQUETAS_DIR.mkdir(parents=True, exist_ok=True)

# Endereço público da API no Render
PUBLIC_BASE_URL = "https://jeh-etiquetas-api.onrender.com"


@app.get("/")
def health():
    return jsonify({
        "status": "online",
        "service": "jeh-etiquetas-api",
        "version": "v1"
    })


@app.get("/teste-etiqueta")
def teste_etiqueta():
    try:
        etiqueta_data = {
            "protein_title": "FRANGO GRELHADO",
            "ingredient_1": "ARROZ",
            "ingredient_2": "FEIJAO",
            "ingredient_3": "BROCOLIS",
            "final_weight": "350g",
            "manufacturing_date": datetime.now().strftime("%d/%m/%Y")
        }

        file_id = uuid.uuid4().hex
        output_file = ETIQUETAS_DIR / f"{file_id}.jpg"

        render(etiqueta_data, output_file)

        return jsonify({
            "status": "ok",
            "message": "Etiqueta de teste gerada.",
            "image_url": f"{PUBLIC_BASE_URL}/etiqueta/{file_id}.jpg"
        })

    except Exception as e:
        return jsonify({
            "erro": "Erro ao gerar etiqueta de teste.",
            "detalhes": str(e)
        }), 500


@app.get("/etiqueta/<filename>")
def servir_etiqueta(filename):
    try:
        # Segurança: impedir acesso a caminhos fora do diretório de etiquetas
        if "/" in filename or "\\" in filename or ".." in filename:
            return jsonify({
                "erro": "Arquivo inválido."
            }), 400

        file_path = ETIQUETAS_DIR / filename

        if not file_path.exists():
            return jsonify({
                "erro": "Etiqueta não encontrada."
            }), 404

        return send_file(
            file_path,
            mimetype="image/jpeg",
            as_attachment=False,
            download_name="etiqueta.jpg"
        )

    except Exception as e:
        return jsonify({
            "erro": "Erro ao entregar etiqueta.",
            "detalhes": str(e)
        }), 500


@app.post("/gerar-etiqueta")
def gerar_etiqueta():
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "erro": "JSON não enviado."
            }), 400

        protein_title = str(
            data.get("protein_title", "")
        ).strip()

        if not protein_title:
            return jsonify({
                "erro": "protein_title é obrigatório."
            }), 400

        etiqueta_data = {
            "protein_title": protein_title,
            "ingredient_1": str(
                data.get("ingredient_1", "")
            ).strip(),
            "ingredient_2": str(
                data.get("ingredient_2", "")
            ).strip(),
            "ingredient_3": str(
                data.get("ingredient_3", "")
            ).strip(),
            "final_weight": str(
                data.get("final_weight", "")
            ).strip(),
            "manufacturing_date": str(
                data.get(
                    "manufacturing_date",
                    datetime.now().strftime("%d/%m/%Y")
                )
            ).strip()
        }

        # Cada chamada gera UMA etiqueta física
        file_id = uuid.uuid4().hex
        output_file = ETIQUETAS_DIR / f"{file_id}.jpg"

        # Usa exatamente o renderer e o template oficial existentes
        render(etiqueta_data, output_file)

        image_url = f"{PUBLIC_BASE_URL}/etiqueta/{file_id}.jpg"

        return jsonify({
            "status": "ok",
            "message": "Etiqueta gerada com sucesso.",
            "image_url": image_url,
            "filename": "etiqueta.jpg",
            "data": etiqueta_data
        })

    except Exception as e:
        return jsonify({
            "erro": "Erro ao gerar etiqueta.",
            "detalhes": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port
    )
