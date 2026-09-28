from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from typing import Optional

from app import storage
from app.models import Documento, DocumentoUpdate
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


# F3 — Consulta por ID
@router.get("/{id}", response_model=Documento)
def consultar_documento(id: int):
    doc = storage.buscar_por_id(id)
    if not doc:
        logger.warning(f"DOCUMENTO_NAO_ENCONTRADO id={id}")
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    logger.info(f"CONSULTA id={id}")
    return doc


# F4 — Download
@router.get("/{id}/download")
def download_documento(id: int):
    doc = storage.buscar_por_id(id)
    if not doc:
        logger.warning(f"DOCUMENTO_NAO_ENCONTRADO id={id}")
        raise HTTPException(status_code=404, detail="Documento não encontrado.")

    caminho = storage.caminho_fisico(doc)
    if not caminho.exists():
        logger.error(f"ARQUIVO_FISICO_AUSENTE id={id}")
        raise HTTPException(status_code=404, detail="Arquivo físico não encontrado no servidor.")

    logger.info(f"DOWNLOAD id={id} arquivo={doc.nome_original}")
    return FileResponse(
        path=str(caminho),
        filename=doc.nome_original,
        media_type=doc.tipo_mime,
    )


# F5 — Atualização de metadados
@router.put("/{id}", response_model=Documento)
def atualizar_documento(id: int, body: DocumentoUpdate):
    doc = storage.atualizar_documento(id, body.model_dump(exclude_none=True))
    if not doc:
        logger.warning(f"DOCUMENTO_NAO_ENCONTRADO id={id}")
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    return doc


# F6 — Exclusão
@router.delete("/{id}", status_code=200)
def excluir_documento(id: int):
    ok = storage.excluir_documento(id)
    if not ok:
        logger.warning(f"DOCUMENTO_NAO_ENCONTRADO id={id}")
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    return {"mensagem": f"Documento {id} excluído com sucesso."}