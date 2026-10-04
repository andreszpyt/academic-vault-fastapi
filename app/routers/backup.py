import zipfile
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app import storage
from app.config import DIR_BACKUPS, METADATA_FILE
from app.models import ItemBackup
from app.logger import logger

router = APIRouter(tags=["Backup"])


# F14 — Criar backup compactado
@router.post("/backup", status_code=201)
def criar_backup():
    nome_zip    = f"backup_{datetime.now().strftime('%Y-%m-%d_%H%M')}.zip"
    caminho_zip = DIR_BACKUPS / nome_zip

    # Evita sobrescrever um backup já existente
    if caminho_zip.exists():
        raise HTTPException(
            status_code=409,
            detail=f"Já existe um backup com o nome {nome_zip}. Aguarde um minuto e tente novamente.",
        )

    docs = storage.listar_documentos()

    try:
        with zipfile.ZipFile(caminho_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            # Adiciona cada arquivo físico
            for d in docs:
                caminho_doc = storage.caminho_fisico(d)
                if caminho_doc.exists():
                    zf.write(caminho_doc, arcname=f"documentos/{d.nome_armazenado}")

            # Adiciona o JSON de metadados
            if METADATA_FILE.exists():
                zf.write(METADATA_FILE, arcname="metadata/documentos.json")

    except Exception as e:
        logger.error(f"BACKUP_FALHOU erro={e}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar backup: {e}")

    tamanho = caminho_zip.stat().st_size
    logger.info(f"BACKUP_CRIADO arquivo={nome_zip} tamanho={tamanho} docs={len(docs)}")

    return {
        "mensagem": "Backup criado com sucesso.",
        "arquivo":  nome_zip,
        "tamanho":  tamanho,
        "total_documentos": len(docs),
    }


# F15 — Listar backups disponíveis
@router.get("/backups")
def listar_backups():
    backups = []
    for f in sorted(DIR_BACKUPS.glob("*.zip"), key=lambda x: x.stat().st_mtime, reverse=True):
        backups.append({
            "arquivo":   f.name,
            "tamanho":   f.stat().st_size,
            "criado_em": datetime.fromtimestamp(f.stat().st_mtime).isoformat(timespec="seconds"),
        })
    logger.info(f"LISTAGEM_BACKUPS total={len(backups)}")
    return backups


# Download de um backup específico
@router.get("/backups/{nome}")
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