from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Response
from fastapi.responses import FileResponse
from typing import Optional

from app import storage
from app.models import Documento, DocumentoUpdate, Estatisticas, IntegridadeIndividual
from app.logger import logger

router = APIRouter(prefix="/documentos", tags=["Documentos"])


@router.post("", response_model=Documento, status_code=201)
@router.post("/", response_model=Documento, status_code=201, include_in_schema=False)
async def upload_documento(
    arquivo: UploadFile = File(...),
    categoria: str = Form(...),
    aluno: str = Form(...),
    matricula: str = Form(...),
    curso: str = Form(...),
    semestre: str = Form(...),
    tipo_documento: str = Form(...),
    descricao: Optional[str] = Form(None),
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


@router.get("", response_model=list[Documento])
@router.get("/", response_model=list[Documento], include_in_schema=False)
def listar_documentos(
    categoria: Optional[str] = Query(None, description="Filtra por categoria"),
    extensao: Optional[str] = Query(None, description="Filtra por extensão (ex: .pdf, .txt)"),
    aluno: Optional[str] = Query(None, description="Busca parcial por nome do aluno"),
    autor: Optional[str] = Query(None, description="Alias para busca por autor/aluno"),
    matricula: Optional[str] = Query(None, description="Filtra por matrícula"),
    semestre: Optional[str] = Query(None, description="Filtra por semestre (ex: 2026.1)"),
    ano: Optional[str] = Query(None, description="Filtra por ano (ex: 2026)"),
    ano_publicacao: Optional[str] = Query(None, description="Alias para busca por ano"),
    tipo_documento: Optional[str] = Query(None, description="Filtra por tipo de documento"),
    curso: Optional[str] = Query(None, description="Busca parcial por curso"),
    palavra_chave: Optional[str] = Query(None, description="Busca textual em nome, descrição e tags"),
    termo: Optional[str] = Query(None, description="Busca textual geral"),
    descricao: Optional[str] = Query(None, description="Busca por descrição"),
    nome_original: Optional[str] = Query(None, description="Busca por nome original"),
    titulo: Optional[str] = Query(None, description="Alias para nome original"),
    tipo_mime: Optional[str] = Query(None, description="Filtra por tipo MIME"),
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
        descricao=descricao,
        nome_original=nome_original,
        titulo=titulo,
        tipo_mime=tipo_mime,
    )
    logger.info(f"LISTAGEM total={len(docs)}")
    return docs


@router.get("/pesquisar", response_model=list[Documento])
@router.get("/pesquisar/", response_model=list[Documento], include_in_schema=False)
def pesquisar_documentos(
    extensao: Optional[str] = Query(None, description="Filtra por extensão"),
    categoria: Optional[str] = Query(None, description="Filtra por categoria"),
    tipo_mime: Optional[str] = Query(None, description="Filtra por tipo MIME"),
    descricao: Optional[str] = Query(None, description="Filtra por descrição"),
    nome_original: Optional[str] = Query(None, description="Filtra por nome original"),
    aluno: Optional[str] = Query(None, description="Filtra por aluno"),
    matricula: Optional[str] = Query(None, description="Filtra por matrícula"),
    curso: Optional[str] = Query(None, description="Filtra por curso"),
    semestre: Optional[str] = Query(None, description="Filtra por semestre"),
    tipo_documento: Optional[str] = Query(None, description="Filtra por tipo de documento"),
):
    gerais_presentes = []
    if extensao and extensao.strip():
        gerais_presentes.append("extensao")
    if categoria and categoria.strip():
        gerais_presentes.append("categoria")
    if tipo_mime and tipo_mime.strip():
        gerais_presentes.append("tipo_mime")
    if descricao and descricao.strip():
        gerais_presentes.append("descricao")
    if nome_original and nome_original.strip():
        gerais_presentes.append("nome_original")

    especificos_presentes = []
    if aluno and aluno.strip():
        especificos_presentes.append("aluno")
    if matricula and matricula.strip():
        especificos_presentes.append("matricula")
    if curso and curso.strip():
        especificos_presentes.append("curso")
    if semestre and semestre.strip():
        especificos_presentes.append("semestre")
    if tipo_documento and tipo_documento.strip():
        especificos_presentes.append("tipo_documento")

    if len(gerais_presentes) < 1 or len(especificos_presentes) < 2:
        raise HTTPException(
            status_code=400,
            detail="A pesquisa exige pelo menos 1 atributo geral (extensao, categoria, descricao, tipo_mime, nome_original) e pelo menos 2 atributos específicos (aluno, matricula, curso, semestre, tipo_documento).",
        )

    docs = storage.listar_documentos(
        categoria=categoria,
        extensao=extensao,
        aluno=aluno,
        matricula=matricula,
        semestre=semestre,
        tipo_documento=tipo_documento,
        curso=curso,
        descricao=descricao,
        nome_original=nome_original,
        tipo_mime=tipo_mime,
    )
    logger.info(f"PESQUISA total={len(docs)} gerais={gerais_presentes} especificos={especificos_presentes}")
    return docs


@router.get("/estatisticas", response_model=Estatisticas)
@router.get("/estatisticas/", response_model=Estatisticas, include_in_schema=False)
def obter_estatisticas():
    stats = storage.obter_estatisticas()
    logger.info(f"ESTATISTICAS total_documentos={stats['total_documentos']}")
    return stats


@router.get("/exportar/xml")
@router.get("/exportar/xml/", include_in_schema=False)
def exportar_xml(
    aluno: Optional[str] = Query(None, description="Filtra por nome do aluno"),
    semestre: Optional[str] = Query(None, description="Filtra por semestre"),
):
    docs = storage.listar_documentos(aluno=aluno, semestre=semestre)

    raiz = Element("documentos")
    for doc in docs:
        doc_el = SubElement(raiz, "documento")
        for campo, valor in doc.model_dump(mode="json").items():
            el = SubElement(doc_el, campo)
            el.text = str(valor) if valor is not None else ""

    xml_bruto = tostring(raiz, encoding="utf-8")
    xml_bonito = minidom.parseString(xml_bruto).toprettyxml(indent="  ", encoding="utf-8")

    logger.info(f"EXPORTACAO_XML aluno={aluno} semestre={semestre} total={len(docs)}")
    return Response(
        content=xml_bonito,
        media_type="application/xml",
        headers={"Content-Disposition": 'attachment; filename="documentos.xml"'},
    )


@router.get("/{id}/integridade", response_model=IntegridadeIndividual)
@router.get("/{id}/integridade/", response_model=IntegridadeIndividual, include_in_schema=False)
def verificar_integridade(id: int):
    resultado = storage.verificar_integridade_documento(id)
    if not resultado:
        logger.warning(f"DOCUMENTO_NAO_ENCONTRADO id={id}")
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    return resultado


@router.get("/{id}", response_model=Documento)
@router.get("/{id}/", response_model=Documento, include_in_schema=False)
def consultar_documento(id: int):
    doc = storage.buscar_por_id(id)
    if not doc:
        logger.warning(f"DOCUMENTO_NAO_ENCONTRADO id={id}")
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    logger.info(f"CONSULTA id={id}")
    return doc


@router.get("/{id}/download")
@router.get("/{id}/download/", include_in_schema=False)
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


@router.put("/{id}", response_model=Documento)
@router.put("/{id}/", response_model=Documento, include_in_schema=False)
def atualizar_documento(id: int, body: DocumentoUpdate):
    doc = storage.atualizar_documento(id, body.model_dump(exclude_none=True))
    if not doc:
        logger.warning(f"DOCUMENTO_NAO_ENCONTRADO id={id}")
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    return doc


@router.delete("/{id}", status_code=200)
@router.delete("/{id}/", status_code=200, include_in_schema=False)
def excluir_documento(id: int):
    ok = storage.excluir_documento(id)
    if not ok:
        logger.warning(f"DOCUMENTO_NAO_ENCONTRADO id={id}")
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    return {"mensagem": f"Documento {id} excluído com sucesso."}
