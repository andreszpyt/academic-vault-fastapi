from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from typing import Optional

from app import storage
from app.models import Documento
from app.logger import logger

router = APIRouter(prefix="/documentos", tags=["Documentos"])


# F1 — Upload
@router.post("/", response_model=Documento, status_code=201)
async def upload_documento(
    arquivo:        UploadFile = File(...),
    categoria:      str        = Form(...),
    aluno:          str        = Form(...),
    matricula:      str        = Form(...),
    curso:          str        = Form(...),
    semestre:       str        = Form(...),
    tipo_documento: str        = Form(...),
    descricao:      Optional[str] = Form(None),
):
    conteudo = await arquivo.read()
    try:
        doc = storage.salvar_arquivo(
            conteudo=conteudo,
            nome_original=arquivo.filename,
            categoria=categoria,
            descricao=descricao,
            aluno=aluno,
            matricula=matricula,
            curso=curso,
            semestre=semestre,
            tipo_documento=tipo_documento,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return doc


# F2 — Listagem
@router.get("/", response_model=list[Documento])
def listar_documentos():
    docs = storage.listar_documentos()
    logger.info(f"LISTAGEM total={len(docs)}")
    return docs