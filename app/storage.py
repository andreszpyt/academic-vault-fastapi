import json
import hashlib
import mimetypes
from pathlib import Path
from datetime import datetime

from app.config import DIR_DOCUMENTOS, METADATA_FILE, UPLOAD_MAX_MB
from app.models import Documento
from app.logger import logger


# ── Leitura e escrita do JSON ─────────────────────────────────────────────────

def _ler_documentos() -> list[dict]:
    """Lê o arquivo documentos.json e retorna uma lista de dicionários."""
    if not METADATA_FILE.exists():
        return []
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        conteudo = f.read().strip()
        if not conteudo:
            return []
        try:
            return json.loads(conteudo)
        except json.JSONDecodeError as e:
            logger.error(f"JSON_INVALIDO erro={e}")
            raise ValueError(f"Arquivo de metadados corrompido: {e}")


def _salvar_documentos(docs: list[dict]) -> None:
    """Sobrescreve o documentos.json com a lista atualizada."""
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)


def _proximo_id(docs: list[dict]) -> int:
    """Retorna o próximo ID disponível."""
    if not docs:
        return 1
    return max(d["id"] for d in docs) + 1


# ── Hash SHA-256 ──────────────────────────────────────────────────────────────

def calcular_sha256(path: Path) -> str:
    """Calcula o hash SHA-256 de um arquivo em disco."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ── Nome seguro para armazenamento ───────────────────────────────────────────

def _nome_armazenamento(id_: int, nome_original: str) -> str:
    """Prefixa o nome com o ID para evitar sobrescrita de arquivos."""
    sufixo = Path(nome_original).suffix
    stem   = Path(nome_original).stem
    return f"{id_}_{stem}{sufixo}"


# ── Operações principais ──────────────────────────────────────────────────────

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
    # Valida tamanho
    tamanho_mb = len(conteudo) / (1024 * 1024)
    if tamanho_mb > UPLOAD_MAX_MB:
        raise ValueError(
            f"Arquivo excede o limite de {UPLOAD_MAX_MB} MB "
            f"({tamanho_mb:.2f} MB enviados)."
        )

    docs    = _ler_documentos()
    novo_id = _proximo_id(docs)

    nome_armazenado = _nome_armazenamento(novo_id, nome_original)
    caminho_fisico  = DIR_DOCUMENTOS / nome_armazenado

    # Salva o arquivo físico
    with open(caminho_fisico, "wb") as f:
        f.write(conteudo)

    extensao  = Path(nome_original).suffix.lower()
    tipo_mime = mimetypes.guess_type(nome_original)[0] or "application/octet-stream"
    sha256    = calcular_sha256(caminho_fisico)

    doc = Documento(
        id=novo_id,
        nome_original=nome_original,
        nome_armazenado=nome_armazenado,
        extensao=extensao,
        tipo_mime=tipo_mime,
        tamanho=len(conteudo),
        categoria=categoria,
        descricao=descricao,
        data_upload=datetime.now().isoformat(timespec="seconds"),
        sha256=sha256,
        aluno=aluno,
        matricula=matricula,
        curso=curso,
        semestre=semestre,
        tipo_documento=tipo_documento,
    )

    docs.append(doc.model_dump())
    _salvar_documentos(docs)
    logger.info(f"UPLOAD id={novo_id} arquivo={nome_original} aluno={aluno}")
    return doc


def listar_documentos(
    categoria:      str | None = None,
    extensao:       str | None = None,
    aluno:          str | None = None,
    matricula:      str | None = None,
    semestre:       str | None = None,
    tipo_documento: str | None = None,
    curso:          str | None = None,
) -> list[Documento]:
    docs = _ler_documentos()
    resultado = []
    for d in docs:
        if categoria      and d.get("categoria")      != categoria:                        continue
        if extensao       and d.get("extensao")       != f".{extensao.lstrip('.')}":      continue
        if aluno          and aluno.lower()          not in d.get("aluno", "").lower():    continue
        if matricula      and d.get("matricula")      != matricula:                        continue
        if semestre       and d.get("semestre")       != semestre:                         continue
        if tipo_documento and d.get("tipo_documento") != tipo_documento:                   continue
        if curso          and curso.lower()          not in d.get("curso", "").lower():    continue
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
            for k, v in campos.items():
                docs[i][k] = v
            _salvar_documentos(docs)
            logger.info(f"UPDATE id={id_} campos={list(campos.keys())}")
            return Documento(**docs[i])
    return None


def excluir_documento(id_: int) -> bool:
    docs = _ler_documentos()
    for i, d in enumerate(docs):
        if d["id"] == id_:
            caminho = DIR_DOCUMENTOS / d["nome_armazenado"]
            if caminho.exists():
                caminho.unlink()
            docs.pop(i)
            _salvar_documentos(docs)
            logger.info(f"DELETE id={id_} arquivo={d['nome_armazenado']}")
            return True
    return False


def caminho_fisico(doc: Documento) -> Path:
    return DIR_DOCUMENTOS / doc.nome_armazenado