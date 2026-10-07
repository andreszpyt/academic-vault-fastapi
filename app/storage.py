import json
import hashlib
import mimetypes
from pathlib import Path
from datetime import datetime

from fastapi import HTTPException

from app.config import DIR_DOCUMENTOS, DIR_METADATA, METADATA_FILE, UPLOAD_MAX_MB
from app.models import Documento
from app.logger import logger


def _ler_documentos() -> list[dict]:
    if not METADATA_FILE.exists():
        return []
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            conteudo = f.read().strip()
            if not conteudo:
                return []
            return json.loads(conteudo)
    except json.JSONDecodeError as e:
        logger.error(f"JSON_INVALIDO erro={e}")
        raise HTTPException(
            status_code=500,
            detail=f"Arquivo de metadados corrompido ou JSON inválido: {e}",
        )
    except OSError as e:
        logger.error(f"FALHA_DISCO_LEITURA erro={e}")
        raise HTTPException(
            status_code=500,
            detail=f"Falha de disco ao ler arquivo de metadados: {e}",
        )


def _salvar_documentos(docs: list[dict]) -> None:
    try:
        DIR_METADATA.mkdir(parents=True, exist_ok=True)
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(docs, f, ensure_ascii=False, indent=2, default=str)
    except OSError as e:
        logger.error(f"FALHA_DISCO_ESCRITA erro={e}")
        raise HTTPException(
            status_code=500,
            detail=f"Falha de disco ao salvar arquivo de metadados: {e}",
        )


def _proximo_id(docs: list[dict]) -> int:
    if not docs:
        return 1
    return max(d["id"] for d in docs) + 1


def calcular_sha256(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError as e:
        logger.error(f"FALHA_CALCULO_SHA256 path={path} erro={e}")
        raise HTTPException(
            status_code=500,
            detail=f"Falha de disco ao calcular hash do arquivo: {e}",
        )


CAMPOS_ATUALIZAVEIS = {
    "categoria",
    "descricao",
    "aluno",
    "matricula",
    "curso",
    "semestre",
    "tipo_documento",
}


def _nome_armazenamento(id_: int, nome_original: str) -> str:
    path_obj = Path(Path(nome_original).name)
    sufixo = path_obj.suffix
    stem = path_obj.stem
    nome = f"{id_}_{stem}{sufixo}"
    caminho = DIR_DOCUMENTOS / nome
    contador = 1
    while caminho.exists():
        nome = f"{id_}_{stem}_{contador}{sufixo}"
        caminho = DIR_DOCUMENTOS / nome
        contador += 1
    return nome


def salvar_arquivo(
    conteudo: bytes,
    nome_original: str,
    categoria: str,
    descricao: str | None,
    aluno: str,
    matricula: str,
    curso: str,
    semestre: str,
    tipo_documento: str,
) -> Documento:
    if not nome_original or not nome_original.strip():
        raise HTTPException(status_code=400, detail="Nome do arquivo inválido ou ausente.")

    tamanho_mb = len(conteudo) / (1024 * 1024)
    if tamanho_mb > UPLOAD_MAX_MB:
        raise HTTPException(
            status_code=400,
            detail=f"Arquivo excede o limite de {UPLOAD_MAX_MB} MB ({tamanho_mb:.2f} MB enviados).",
        )

    try:
        DIR_DOCUMENTOS.mkdir(parents=True, exist_ok=True)
        DIR_METADATA.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"FALHA_CRIAR_DIR erro={e}")
        raise HTTPException(status_code=500, detail=f"Falha ao criar diretórios de armazenamento: {e}")

    docs = _ler_documentos()
    novo_id = _proximo_id(docs)

    nome_limpo = Path(nome_original).name
    nome_armazenado = _nome_armazenamento(novo_id, nome_limpo)
    caminho_fisico = DIR_DOCUMENTOS / nome_armazenado

    try:
        with open(caminho_fisico, "wb") as f:
            f.write(conteudo)
    except OSError as e:
        logger.error(f"FALHA_SALVAR_ARQUIVO_FISICO erro={e}")
        raise HTTPException(status_code=500, detail=f"Falha de disco ao salvar arquivo físico: {e}")

    extensao = Path(nome_limpo).suffix.lower()
    tipo_mime = mimetypes.guess_type(nome_limpo)[0] or "application/octet-stream"
    sha256 = calcular_sha256(caminho_fisico)

    doc = Documento(
        id=novo_id,
        nome_original=nome_limpo,
        nome_armazenado=nome_armazenado,
        extensao=extensao,
        tipo_mime=tipo_mime,
        tamanho=len(conteudo),
        categoria=categoria,
        descricao=descricao,
        data_upload=datetime.now(),
        sha256=sha256,
        aluno=aluno,
        matricula=matricula,
        curso=curso,
        semestre=semestre,
        tipo_documento=tipo_documento,
    )

    docs.append(doc.model_dump(mode="json"))
    _salvar_documentos(docs)
    logger.info(f"UPLOAD id={novo_id} arquivo={nome_limpo} aluno={aluno}")
    return doc


def listar_documentos(
    categoria: str | None = None,
    extensao: str | None = None,
    aluno: str | None = None,
    autor: str | None = None,
    matricula: str | None = None,
    semestre: str | None = None,
    ano: str | None = None,
    ano_publicacao: str | None = None,
    tipo_documento: str | None = None,
    curso: str | None = None,
    palavra_chave: str | None = None,
    termo: str | None = None,
    descricao: str | None = None,
    nome_original: str | None = None,
    titulo: str | None = None,
    tipo_mime: str | None = None,
) -> list[Documento]:
    docs = _ler_documentos()
    resultado = []

    busca_aluno = aluno or autor
    busca_ano = ano or ano_publicacao
    busca_termo = palavra_chave or termo
    busca_nome = nome_original or titulo

    for d in docs:
        if categoria and d.get("categoria", "").lower() != categoria.lower():
            continue
        if extensao:
            ext_buscada = f".{extensao.lstrip('.').lower()}"
            if d.get("extensao", "").lower() != ext_buscada:
                continue
        if busca_aluno and busca_aluno.lower() not in d.get("aluno", "").lower():
            continue
        if matricula and d.get("matricula", "").lower() != matricula.lower():
            continue
        if semestre and d.get("semestre", "").lower() != semestre.lower():
            continue
        if busca_ano:
            ano_str = str(busca_ano)
            sem = d.get("semestre", "")
            data_up = d.get("data_upload", "")
            if ano_str not in sem and not data_up.startswith(ano_str):
                continue
        if tipo_documento and str(d.get("tipo_documento", "")).lower() != tipo_documento.lower():
            continue
        if curso and curso.lower() not in d.get("curso", "").lower():
            continue
        if descricao and descricao.lower() not in (d.get("descricao") or "").lower():
            continue
        if busca_nome and busca_nome.lower() not in d.get("nome_original", "").lower():
            continue
        if tipo_mime and d.get("tipo_mime", "").lower() != tipo_mime.lower():
            continue
        if busca_termo:
            termo_lower = busca_termo.lower()
            campos_texto = [
                d.get("nome_original", ""),
                d.get("descricao", "") or "",
                d.get("aluno", ""),
                d.get("curso", ""),
                d.get("categoria", ""),
            ]
            if not any(termo_lower in campo.lower() for campo in campos_texto):
                continue

        resultado.append(Documento(**d))
    return resultado


def buscar_por_id(id_: int) -> Documento | None:
    for d in _ler_documentos():
        if d["id"] == id_:
            return Documento(**d)
    return None


def atualizar_documento(id_: int, campos: dict) -> Documento | None:
    docs = _ler_documentos()
    for i, d in enumerate(docs):
        if d["id"] == id_:
            campos_filtrados = {k: v for k, v in campos.items() if k in CAMPOS_ATUALIZAVEIS}
            for k, v in campos_filtrados.items():
                docs[i][k] = v
            _salvar_documentos(docs)
            logger.info(f"UPDATE id={id_} campos={list(campos_filtrados.keys())}")
            return Documento(**docs[i])
    return None


def excluir_documento(id_: int) -> bool:
    docs = _ler_documentos()
    for i, d in enumerate(docs):
        if d["id"] == id_:
            caminho = DIR_DOCUMENTOS / d["nome_armazenado"]
            if caminho.exists():
                try:
                    caminho.unlink()
                except OSError as e:
                    logger.error(f"FALHA_REMOVER_ARQUIVO id={id_} erro={e}")
                    raise HTTPException(status_code=500, detail=f"Falha ao remover arquivo físico: {e}")
            docs.pop(i)
            _salvar_documentos(docs)
            logger.info(f"DELETE id={id_} arquivo={d['nome_armazenado']}")
            return True
    return False


def caminho_fisico(doc: Documento) -> Path:
    return DIR_DOCUMENTOS / doc.nome_armazenado


def _formatar_tamanho(bytes_: int) -> str:
    if bytes_ < 1024:
        return f"{bytes_} B"
    elif bytes_ < 1024 * 1024:
        return f"{bytes_ / 1024:.2f} KB"
    elif bytes_ < 1024 * 1024 * 1024:
        return f"{bytes_ / (1024 * 1024):.2f} MB"
    return f"{bytes_ / (1024 * 1024 * 1024):.2f} GB"


def obter_estatisticas() -> dict:
    docs = _ler_documentos()

    total_documentos = len(docs)
    espaco_utilizado_bytes = 0

    por_extensao: dict[str, int] = {}
    por_categoria: dict[str, int] = {}
    por_tipo_documento: dict[str, int] = {}
    por_curso: dict[str, int] = {}
    por_semestre: dict[str, int] = {}

    for d in docs:
        tam = d.get("tamanho")
        if tam is None or tam <= 0:
            nome_arm = d.get("nome_armazenado")
            if nome_arm:
                caminho = DIR_DOCUMENTOS / nome_arm
                if caminho.exists():
                    tam = caminho.stat().st_size
                else:
                    tam = 0
            else:
                tam = 0
        espaco_utilizado_bytes += tam

        ext = d.get("extensao", "")
        cat = d.get("categoria", "")
        tipo = d.get("tipo_documento", "")
        curso = d.get("curso", "")
        sem = d.get("semestre", "")

        if ext:
            por_extensao[ext] = por_extensao.get(ext, 0) + 1
        if cat:
            por_categoria[cat] = por_categoria.get(cat, 0) + 1
        if tipo:
            por_tipo_documento[tipo] = por_tipo_documento.get(tipo, 0) + 1
        if curso:
            por_curso[curso] = por_curso.get(curso, 0) + 1
        if sem:
            por_semestre[sem] = por_semestre.get(sem, 0) + 1

    return {
        "total_documentos": total_documentos,
        "espaco_utilizado_bytes": espaco_utilizado_bytes,
        "espaco_utilizado_formatado": _formatar_tamanho(espaco_utilizado_bytes),
        "por_extensao": por_extensao,
        "por_categoria": por_categoria,
        "por_tipo_documento": por_tipo_documento,
        "por_curso": por_curso,
        "por_semestre": por_semestre,
    }


def verificar_integridade_documento(id_: int) -> dict | None:
    doc = buscar_por_id(id_)
    if not doc:
        return None

    caminho = caminho_fisico(doc)
    if not caminho.exists():
        logger.error(f"INTEGRIDADE_ARQUIVO_AUSENTE id={id_} arquivo={doc.nome_armazenado}")
        return {
            "id": doc.id,
            "nome_original": doc.nome_original,
            "hash_original": doc.sha256,
            "hash_atual": None,
            "integro": False,
            "status": "AUSENTE",
        }

    hash_atual = calcular_sha256(caminho)
    integro = (hash_atual == doc.sha256)

    if integro:
        logger.info(f"INTEGRIDADE_OK id={id_} arquivo={doc.nome_original}")
    else:
        logger.warning(
            f"INTEGRIDADE_FALHOU id={id_} arquivo={doc.nome_original} "
            f"hash_esperado={doc.sha256} hash_encontrado={hash_atual}"
        )

    return {
        "id": doc.id,
        "nome_original": doc.nome_original,
        "hash_original": doc.sha256,
        "hash_atual": hash_atual,
        "integro": integro,
        "status": "INTEGRO" if integro else "ALTERADO",
    }


def verificar_integridade_global() -> dict:
    docs = _ler_documentos()

    total_verificados = len(docs)
    total_integros = 0
    total_alterados = 0
    arquivos_nao_localizados = 0
    detalhes = []

    for d in docs:
        doc_id = d["id"]
        res = verificar_integridade_documento(doc_id)
        if not res:
            continue

        detalhes.append({
            "id": res["id"],
            "nome_original": res["nome_original"],
            "status": res["status"],
            "hash_original": res["hash_original"],
            "hash_atual": res["hash_atual"],
        })

        if res["status"] == "INTEGRO":
            total_integros += 1
        elif res["status"] == "ALTERADO":
            total_alterados += 1
        elif res["status"] == "AUSENTE":
            arquivos_nao_localizados += 1

    logger.info(
        f"INTEGRIDADE_GLOBAL total={total_verificados} integros={total_integros} "
        f"alterados={total_alterados} ausentes={arquivos_nao_localizados}"
    )

    return {
        "total_verificados": total_verificados,
        "total_integros": total_integros,
        "total_alterados": total_alterados,
        "arquivos_nao_localizados": arquivos_nao_localizados,
        "detalhes": detalhes,
    }
