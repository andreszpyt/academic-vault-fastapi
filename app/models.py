from pydantic import BaseModel
from typing import Optional
from enum import Enum


class TipoDocumento(str, Enum):
    historico   = "historico"
    certificado = "certificado"
    declaracao  = "declaracao"
    comprovante = "comprovante"
    trabalho    = "trabalho"
    matricula   = "matricula"
    outro       = "outro"


class Documento(BaseModel):
    # Campos gerais
    id:              int
    nome_original:   str
    nome_armazenado: str
    extensao:        str
    tipo_mime:       str
    tamanho:         int
    categoria:       str
    descricao:       Optional[str] = None
    data_upload:     str
    sha256:          str

    # Campos específicos do domínio acadêmico
    aluno:          str
    matricula:      str
    curso:          str
    semestre:       str
    tipo_documento: TipoDocumento


class DocumentoUpdate(BaseModel):
    categoria:      Optional[str]           = None
    descricao:      Optional[str]           = None
    aluno:          Optional[str]           = None
    matricula:      Optional[str]           = None
    curso:          Optional[str]           = None
    semestre:       Optional[str]           = None
    tipo_documento: Optional[TipoDocumento] = None


class Estatisticas(BaseModel):
    total_documentos:           int
    espaco_utilizado_bytes:     int
    espaco_utilizado_formatado: str
    por_extensao:               dict[str, int]
    por_categoria:              dict[str, int]
    por_tipo_documento:         dict[str, int]
    por_curso:                  dict[str, int]
    por_semestre:               dict[str, int]


class IntegridadeIndividual(BaseModel):
    id:            int
    nome_original: str
    hash_original: str
    hash_atual:    Optional[str] = None
    integro:       bool
    status:        str


class DetalheIntegridade(BaseModel):
    id:            int
    nome_original: str
    status:        str
    hash_original: str
    hash_atual:    Optional[str] = None


class IntegridadeGlobal(BaseModel):
    total_verificados:        int
    total_integros:           int
    total_alterados:          int
    arquivos_nao_localizados: int
    detalhes:                 list[DetalheIntegridade]