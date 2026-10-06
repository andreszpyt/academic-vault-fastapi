from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse
from typing import Optional

from app import storage
from app.models import Documento, DocumentoUpdate, Estatisticas, IntegridadeIndividual
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


# F2 e F7 — Listagem e Filtragem
@router.get("/", response_model=list[Documento])
def listar_documentos(
    categoria:      Optional[str] = Query(None, description="Filtra por categoria"),
    extensao:       Optional[str] = Query(None, description="Filtra por extensão (ex: .pdf, .txt)"),
    aluno:          Optional[str] = Query(None, description="Busca parcial por nome do aluno"),
    autor:          Optional[str] = Query(None, description="Alias para busca por autor/aluno"),
    matricula:      Optional[str] = Query(None, description="Filtra por matrícula"),
    semestre:       Optional[str] = Query(None, description="Filtra por semestre (ex: 2026.1)"),
    ano:            Optional[str] = Query(None, description="Filtra por ano (ex: 2026)"),
    ano_publicacao: Optional[str] = Query(None, description="Alias para busca por ano"),
    tipo_documento: Optional[str] = Query(None, description="Filtra por tipo de documento"),
    curso:          Optional[str] = Query(None, description="Busca parcial por curso"),
    palavra_chave:  Optional[str] = Query(None, description="Busca textual em nome, descrição e tags"),
    termo:          Optional[str] = Query(None, description="Busca textual geral"),
):
    docs = storage.listar_documentos(
        categoria=categoria,
        extensao=extensao,
        aluno=aluno,
        autor=autor,
        matricula=matricula,
        semestre=semestre,
        ano=ano,
        ano_publicacao=ano_publicacao,
        tipo_documento=tipo_documento,
        curso=curso,
        palavra_chave=palavra_chave,
        termo=termo,
    )
    logger.info(f"LISTAGEM total={len(docs)}")
    return docs


# F8 — Estatísticas do Cofre
@router.get("/estatisticas", response_model=Estatisticas)
def obter_estatisticas():
    stats = storage.obter_estatisticas()
    logger.info(f"ESTATISTICAS total_documentos={stats['total_documentos']}")
    return stats


# F9 — Verificação de Integridade Individual
@router.get("/{id}/integridade", response_model=IntegridadeIndividual)
def verificar_integridade(id: int):
    resultado = storage.verificar_integridade_documento(id)
    if not resultado:
        logger.warning(f"DOCUMENTO_NAO_ENCONTRADO id={id}")
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    return resultado


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