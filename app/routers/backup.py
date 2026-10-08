import json
import zipfile
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app import storage
from app.config import CONFIG_PATH, DIR_BACKUPS, LOG_ARQUIVO
from app.models import ItemBackup
from app.logger import logger

router = APIRouter(tags=["Backup"])


@router.post("/backup", status_code=201)
@router.post("/backup/", status_code=201, include_in_schema=False)
def criar_backup(
    categoria: Optional[str] = Query(None, description="Filtrar por categoria"),
    curso: Optional[str] = Query(None, description="Filtrar por curso"),
    semestre: Optional[str] = Query(None, description="Filtrar por semestre"),
    ano: Optional[str] = Query(None, description="Filtrar por ano"),
    tipo_documento: Optional[str] = Query(None, description="Filtrar por tipo de documento"),
    aluno: Optional[str] = Query(None, description="Filtrar por aluno"),
):
    docs = storage.listar_documentos(
        categoria=categoria,
        curso=curso,
        semestre=semestre,
        tipo_documento=tipo_documento,
        aluno=aluno,
    )

    if ano:
        docs = [d for d in docs if ano in (d.semestre or "") or str(d.data_upload).startswith(ano)]

    if not docs and any([categoria, curso, semestre, ano, tipo_documento, aluno]):
        raise HTTPException(
            status_code=404,
            detail="Nenhum documento encontrado com os filtros informados.",
        )

    nome_base = f"backup_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}"
    nome_zip = f"{nome_base}.zip"
    caminho_zip = DIR_BACKUPS / nome_zip

    contador = 1
    while caminho_zip.exists():
        nome_zip = f"{nome_base}_{contador}.zip"
        caminho_zip = DIR_BACKUPS / nome_zip
        contador += 1

    try:
        with zipfile.ZipFile(caminho_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for d in docs:
                caminho_doc = storage.caminho_fisico(d)
                if caminho_doc.exists():
                    zf.write(caminho_doc, arcname=f"documentos/{d.nome_armazenado}")
                    zf.write(caminho_doc, arcname=d.nome_armazenado)

            metadados_json = json.dumps([d.model_dump(mode="json") for d in docs], ensure_ascii=False, indent=2)
            zf.writestr("documentos.json", metadados_json)
            zf.writestr("metadata/documentos.json", metadados_json)

            if CONFIG_PATH.exists():
                zf.write(CONFIG_PATH, arcname="config.yaml")

            if LOG_ARQUIVO.exists():
                zf.write(LOG_ARQUIVO, arcname="logs/sistema.log")

    except Exception as e:
        logger.error(f"BACKUP_FALHOU erro={e}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar backup: {e}")

    tamanho = caminho_zip.stat().st_size
    logger.info(f"BACKUP_CRIADO arquivo={nome_zip} total_arquivos={len(docs)}")

    return {
        "mensagem": "Backup criado com sucesso.",
        "nome": nome_zip,
        "arquivo": nome_zip,
        "tamanho": tamanho,
        "total_documentos": len(docs),
        "documentos_incluidos": [d.nome_armazenado for d in docs],
    }


@router.get("/backups", response_model=list[ItemBackup])
@router.get("/backups/", response_model=list[ItemBackup], include_in_schema=False)
def listar_backups():
    backups = []
    for f in sorted(DIR_BACKUPS.glob("*.zip"), key=lambda x: x.stat().st_mtime, reverse=True):
        backups.append({
            "nome": f.name,
            "arquivo": f.name,
            "tamanho": f.stat().st_size,
            "criado_em": datetime.fromtimestamp(f.stat().st_mtime).isoformat(timespec="seconds"),
        })

    logger.info(f"LISTAGEM_BACKUPS total={len(backups)}")
    return backups


@router.get("/backups/{nome}")
@router.get("/backups/{nome}/", include_in_schema=False)
def download_backup(nome: str):
    caminho = DIR_BACKUPS / nome

    if not caminho.exists():
        logger.warning(f"BACKUP_NAO_ENCONTRADO arquivo={nome}")
        raise HTTPException(status_code=404, detail="Backup não encontrado.")

    logger.info(f"DOWNLOAD_BACKUP arquivo={nome}")
    return FileResponse(
        path=str(caminho),
        filename=nome,
        media_type="application/zip",
    )
