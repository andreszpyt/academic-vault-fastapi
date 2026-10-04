import csv
import io
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional

from app import storage
from app.config import DIR_EXPORTS
from app.logger import logger

router = APIRouter(tags=["Exportações"])


# F13 — Exportação CSV
@router.get("/exportar/csv")
def exportar_csv():
    docs = storage.listar_documentos()

    campos = [
        "id", "nome_original", "extensao", "tipo_mime", "tamanho",
        "categoria", "descricao", "data_upload", "sha256",
        "aluno", "matricula", "curso", "semestre", "tipo_documento",
    ]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=campos, extrasaction="ignore")
    writer.writeheader()
    for d in docs:
        writer.writerow(d.model_dump())

    nome_arquivo = f"catalogo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    (DIR_EXPORTS / nome_arquivo).write_text(output.getvalue(), encoding="utf-8")
    logger.info(f"EXPORTACAO_CSV arquivo={nome_arquivo} total={len(docs)}")

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
    )


# Requisito do Tema 2 — Exportação XML por aluno ou semestre
@router.get("/exportar/xml")
def exportar_xml(
    aluno:    Optional[str] = Query(None, description="Filtrar por nome do aluno"),
    semestre: Optional[str] = Query(None, description="Filtrar por semestre (ex: 2026.1)"),
):
    if not aluno and not semestre:
        raise HTTPException(
            status_code=400,
            detail="Informe ao menos um filtro: aluno ou semestre.",
        )

    docs = storage.listar_documentos(aluno=aluno, semestre=semestre)

    if not docs:
        raise HTTPException(
            status_code=404,
            detail="Nenhum documento encontrado com os filtros informados.",
        )

    # Monta a árvore XML
    raiz = Element("cofre_academico")
    raiz.set("exportado_em", datetime.now().isoformat(timespec="seconds"))
    if aluno:
        raiz.set("filtro_aluno", aluno)
    if semestre:
        raiz.set("filtro_semestre", semestre)

    for d in docs:
        doc_el = SubElement(raiz, "documento")
        for campo, valor in d.model_dump().items():
            el = SubElement(doc_el, campo)
            el.text = str(valor) if valor is not None else ""

    # Formata o XML com indentação
    xml_bruto  = tostring(raiz, encoding="unicode")
    xml_bonito = minidom.parseString(xml_bruto).toprettyxml(indent="  ")

    # Remove a linha <?xml ...?> duplicada que o minidom adiciona
    linhas     = xml_bonito.split("\n")
    xml_final  = "\n".join(linhas[1:]) if linhas[0].startswith("<?xml") else xml_bonito

    nome_arquivo = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
    (DIR_EXPORTS / nome_arquivo).write_text(xml_final, encoding="utf-8")
    logger.info(f"EXPORTACAO_XML arquivo={nome_arquivo} aluno={aluno} semestre={semestre} total={len(docs)}")

    return StreamingResponse(
        io.BytesIO(xml_final.encode("utf-8")),
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
    )