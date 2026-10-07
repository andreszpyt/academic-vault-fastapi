import csv
import io
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app import storage
from app.config import DIR_EXPORTS
from app.logger import logger

router = APIRouter(tags=["Exportações"])


@router.get("/exportar/csv")
@router.get("/exportar/csv/", include_in_schema=False)
def exportar_csv():
    docs = storage.listar_documentos()

    campos = [
        "id", "nome_original", "nome_armazenado", "extensao", "tipo_mime", "tamanho",
        "categoria", "descricao", "data_upload", "sha256",
        "aluno", "matricula", "curso", "semestre", "tipo_documento",
    ]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=campos, extrasaction="ignore")
    writer.writeheader()
    for d in docs:
        writer.writerow(d.model_dump())

    nome_arquivo = f"catalogo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    try:
        DIR_EXPORTS.mkdir(parents=True, exist_ok=True)
        (DIR_EXPORTS / nome_arquivo).write_text(output.getvalue(), encoding="utf-8")
    except OSError as e:
        logger.error(f"FALHA_DISCO_EXPORT_CSV erro={e}")
        raise HTTPException(status_code=500, detail=f"Falha de disco ao salvar arquivo de exportação: {e}")

    logger.info(f"EXPORTACAO_CSV arquivo={nome_arquivo} total={len(docs)}")

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
    )

