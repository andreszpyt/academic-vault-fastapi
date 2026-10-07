import hashlib
import io
import json
import mimetypes
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).parent
DIR_DOCUMENTOS = BASE_DIR / "storage" / "documentos"
DIR_METADATA = BASE_DIR / "storage" / "metadata"
METADATA_FILE = DIR_METADATA / "documentos.json"


def calcular_sha256(conteudo: bytes) -> str:
    h = hashlib.sha256()
    h.update(conteudo)
    return h.hexdigest()


def gerar_pdf(titulo: str, subtitulo: str, autor: str, instituicao: str = "UFC - Campus Quixada") -> bytes:
    stream_content = (
        f"BT\n"
        f"/F1 16 Tf\n"
        f"50 740 Td\n"
        f"({titulo}) Tj\n"
        f"/F1 12 Tf\n"
        f"0 -25 Td\n"
        f"({subtitulo}) Tj\n"
        f"0 -20 Td\n"
        f"(Autor: {autor}) Tj\n"
        f"0 -20 Td\n"
        f"(Instituicao: {instituicao}) Tj\n"
        f"ET\n"
    )
    stream_bytes = stream_content.encode("latin-1", errors="replace")

    body = [
        b"%PDF-1.4\n",
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n",
        f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("latin-1") + stream_bytes + b"\nendstream\nendobj\n",
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]

    offsets = []
    current_offset = 0
    full_content = b""
    for part in body:
        if part.startswith(b"%PDF"):
            current_offset += len(part)
            full_content += part
        else:
            offsets.append(current_offset)
            current_offset += len(part)
            full_content += part

    xref_offset = current_offset
    xref = "xref\n0 6\n0000000000 65535 f \n"
    for off in offsets:
        xref += f"{off:010d} 00000 n \n"
    trailer = f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"

    full_content += xref.encode("latin-1") + trailer.encode("latin-1")
    return full_content


def gerar_docx(titulo: str, autor: str, conteudo_texto: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
        rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
        doc_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>{titulo}</w:t></w:r></w:p>
    <w:p><w:r><w:rPr><w:i/></w:rPr><w:t>Autor: {autor}</w:t></w:r></w:p>
    <w:p><w:r><w:t>{conteudo_texto}</w:t></w:r></w:p>
  </w:body>
</w:document>"""
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", doc_xml)
    return buf.getvalue()


def gerar_jpg() -> bytes:
    return bytes([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
        0x01, 0x01, 0x00, 0x48, 0x00, 0x48, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
        0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
        0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
        0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
        0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
        0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
        0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
        0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
        0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
        0x09, 0x0A, 0x0B, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F,
        0x00, 0x7F, 0x00, 0xFF, 0xD9
    ])


DOCUMENTOS_SEED = [
    {
        "id": 1,
        "nome_original": "historico_escolar_ian.pdf",
        "categoria": "academico",
        "descricao": "Histórico escolar completo com IRA e disciplinas cursadas",
        "data_upload": "2026-09-23T21:13:15",
        "aluno": "Ian de Freitas Silva",
        "matricula": "536147",
        "curso": "Sistemas de Informação",
        "semestre": "2026.1",
        "tipo_documento": "historico",
        "gerador": lambda: gerar_pdf("Historico Escolar Oficial", "Curso: Sistemas de Informacao", "Ian de Freitas Silva"),
    },
    {
        "id": 2,
        "nome_original": "artigo_persistencia_microsservicos.pdf",
        "categoria": "academico",
        "descricao": "Artigo científico sobre estratégias de persistência em arquivos no ecossistema FastAPI",
        "data_upload": "2026-09-24T09:30:00",
        "aluno": "Lucas Martins de Alencar",
        "matricula": "512345",
        "curso": "Engenharia de Software",
        "semestre": "2026.1",
        "tipo_documento": "trabalho",
        "gerador": lambda: gerar_pdf("Artigo Cientifico: Persistencia em Microsservicos", "FastAPI e Padroes de Armazenamento", "Lucas Martins de Alencar"),
    },
    {
        "id": 3,
        "nome_original": "certificado_monitoria_ed.pdf",
        "categoria": "extensao",
        "descricao": "Certificado de monitoria de 64h em Estruturas de Dados Avançadas",
        "data_upload": "2026-09-24T11:45:20",
        "aluno": "Beatriz Lima Costa",
        "matricula": "541289",
        "curso": "Ciência da Computação",
        "semestre": "2025.2",
        "tipo_documento": "certificado",
        "gerador": lambda: gerar_pdf("Certificado de Monitoria Academica", "Disciplina: Estruturas de Dados Avancadas (64 horas)", "Beatriz Lima Costa"),
    },
    {
        "id": 4,
        "nome_original": "declaracao_matricula_ativa.pdf",
        "categoria": "administrativo",
        "descricao": "Declaração comprobatória de vínculo institucional e matrícula ativa",
        "data_upload": "2026-09-25T14:10:05",
        "aluno": "Marcelo Silveira Santos",
        "matricula": "498721",
        "curso": "Engenharia de Computação",
        "semestre": "2026.1",
        "tipo_documento": "declaracao",
        "gerador": lambda: gerar_pdf("Declaracao de Matricula Ativa", "Vinculo Institucional - Semestre 2026.1", "Marcelo Silveira Santos"),
    },
    {
        "id": 5,
        "nome_original": "comprovante_estagio_software.pdf",
        "categoria": "administrativo",
        "descricao": "Comprovante de estágio obrigatório de desenvolvimento backend",
        "data_upload": "2026-09-25T16:22:40",
        "aluno": "Juliana Ribeiro Lima",
        "matricula": "519834",
        "curso": "Engenharia de Software",
        "semestre": "2025.2",
        "tipo_documento": "comprovante",
        "gerador": lambda: gerar_pdf("Comprovante de Estagio Supervisionado", "Area: Engenharia de Software e Desenvolvimento Backend", "Juliana Ribeiro Lima"),
    },
    {
        "id": 6,
        "nome_original": "monografia_tcc_arquitetura_segura.docx",
        "categoria": "academico",
        "descricao": "Versão preliminar da monografia de TCC sobre arquiteturas seguras em nuvem",
        "data_upload": "2026-09-26T10:05:30",
        "aluno": "Rafael Costa Ferreira",
        "matricula": "527319",
        "curso": "Redes de Computadores",
        "semestre": "2025.1",
        "tipo_documento": "trabalho",
        "gerador": lambda: gerar_docx(
            "Monografia de TCC: Arquitetura Segura para Aplicacoes Distribuidas",
            "Rafael Costa Ferreira",
            "Este trabalho apresenta uma proposta de arquitetura resiliente e segura para sistemas em nuvem utilizando controles de integridade criptográfica e isolamento de recursos."
        ),
    },
    {
        "id": 7,
        "nome_original": "carteira_estudantil_frente.jpg",
        "categoria": "administrativo",
        "descricao": "Digitalização da carteira de identificação estudantil universitária",
        "data_upload": "2026-09-26T15:40:12",
        "aluno": "André Pinheiro de Sousa",
        "matricula": "538912",
        "curso": "Engenharia de Software",
        "semestre": "2026.1",
        "tipo_documento": "comprovante",
        "gerador": gerar_jpg,
    },
    {
        "id": 8,
        "nome_original": "resumo_usabilidade_interfaces.txt",
        "categoria": "academico",
        "descricao": "Resumo analítico sobre critérios de acessibilidade WCAG e heurísticas de Nielsen",
        "data_upload": "2026-09-27T08:20:00",
        "aluno": "Gabriel Mendonça Alves",
        "matricula": "504192",
        "curso": "Design Digital",
        "semestre": "2024.2",
        "tipo_documento": "trabalho",
        "gerador": lambda: """Resumo Analítico de Pesquisa em Usabilidade e Experiência do Usuário (UX)
Aluno: Gabriel Mendonça Alves
Matrícula: 504192
Curso: Design Digital - UFC Quixadá

1. Avaliação Heurística de Jakob Nielsen:
- Visibilidade do status do sistema;
- Correspondência entre o sistema e o mundo real;
- Controle e liberdade para o usuário;
- Consistência e padrões;
- Prevenção de erros;
- Reconhecimento em vez de memorização;
- Flexibilidade e eficiência de uso;
- Estética e design minimalista;
- Suporte para os usuários reconhecerem, diagnosticarem e recuperarem-se de erros;
- Ajuda e documentação.

2. Diretrizes de Acessibilidade Web (WCAG 2.1):
- Perceptível, Operável, Compreensível e Robusto.
""".encode("utf-8"),
    },
    {
        "id": 9,
        "nome_original": "comprovante_vacinacao_campanha.jpg",
        "categoria": "administrativo",
        "descricao": "Registro fotográfico do cartão de vacinação para cadastro institucional",
        "data_upload": "2026-09-27T13:55:18",
        "aluno": "Diego Fernandes Rocha",
        "matricula": "513820",
        "curso": "Ciência da Computação",
        "semestre": "2026.1",
        "tipo_documento": "comprovante",
        "gerador": gerar_jpg,
    },
    {
        "id": 10,
        "nome_original": "manual_normas_abnt_nbr6023.txt",
        "categoria": "academico",
        "descricao": "Guia de referência rápida para elaboração de referências e citações acadêmicas",
        "data_upload": "2026-09-28T09:12:44",
        "aluno": "Larissa Carvalho Moreira",
        "matricula": "542019",
        "curso": "Sistemas de Informação",
        "semestre": "2025.1",
        "tipo_documento": "outro",
        "gerador": lambda: """Manual Prático de Normas ABNT NBR 6023:2018

Autora: Larissa Carvalho Moreira
Curso: Sistemas de Informação - UFC Quixadá

1. Estrutura de Citação de Artigo em Periódico:
SOBRENOME, Nome do Autor. Título do artigo. Nome da Revista, Local, v. volume, n. número, p. páginas, ano.

2. Estrutura de Citação de Monografia e TCC:
SOBRENOME, Nome. Título do trabalho: subtítulo. Ano. Número de folhas f. Trabalho de Conclusão de Curso - Universidade Federal do Ceará, Quixadá, ano.
""".encode("utf-8"),
    },
    {
        "id": 11,
        "nome_original": "comprovante_matricula_2026_2.pdf",
        "categoria": "administrativo",
        "descricao": "Comprovante de confirmação de matrícula curricular e turmas inscritas",
        "data_upload": "2026-09-28T14:30:50",
        "aluno": "Fernanda Prado Nogueira",
        "matricula": "529401",
        "curso": "Design Digital",
        "semestre": "2026.2",
        "tipo_documento": "matricula",
        "gerador": lambda: gerar_pdf("Comprovante Oficial de Matricula 2026.2", "Aluno: Fernanda Prado Nogueira | Matricula: 529401", "Fernanda Prado Nogueira"),
    },
    {
        "id": 12,
        "nome_original": "relatorio_iniciacao_cientifica.docx",
        "categoria": "pesquisa",
        "descricao": "Relatório técnico semestral de pesquisa financiada pelo CNPq sobre redes definidas por software",
        "data_upload": "2026-09-29T10:15:00",
        "aluno": "Thiago Rocha Vasconcelos",
        "matricula": "489102",
        "curso": "Redes de Computadores",
        "semestre": "2025.2",
        "tipo_documento": "trabalho",
        "gerador": lambda: gerar_docx(
            "Relatorio Semestral de Iniciacao Cientifica - Redes Definidas por Software",
            "Thiago Rocha Vasconcelos",
            "Relatório de atividades de pesquisa desenvolvidas no laboratório de redes de computadores, contendo simulações em Mininet e controladores OpenFlow."
        ),
    },
    {
        "id": 13,
        "nome_original": "projeto_extensao_programacao_escolas.pdf",
        "categoria": "extensao",
        "descricao": "Proposta de ação extensionista para ensino de pensamento computacional no ensino básico",
        "data_upload": "2026-09-29T16:40:22",
        "aluno": "Camila Vasconcelos Rios",
        "matricula": "531849",
        "curso": "Sistemas de Informação",
        "semestre": "2026.1",
        "tipo_documento": "trabalho",
        "gerador": lambda: gerar_pdf("Projeto de Extensao: Programacao para Escolas Publicas", "Coordenacao de Extensao Universitaria", "Camila Vasconcelos Rios"),
    },
    {
        "id": 14,
        "nome_original": "foto_documento_rg.jpg",
        "categoria": "administrativo",
        "descricao": "Cópia digitalizada do documento de identidade civil para arquivo acadêmico",
        "data_upload": "2026-09-30T11:05:15",
        "aluno": "Mateus Holanda Bezerra",
        "matricula": "514930",
        "curso": "Engenharia de Computação",
        "semestre": "2025.1",
        "tipo_documento": "comprovante",
        "gerador": gerar_jpg,
    },
    {
        "id": 15,
        "nome_original": "certificado_apresentacao_workshop.pdf",
        "categoria": "extensao",
        "descricao": "Certificado de apresentação oral de artigo em workshop de engenharia de requisitos",
        "data_upload": "2026-09-30T17:50:00",
        "aluno": "Sofia Menezes Duarte",
        "matricula": "520481",
        "curso": "Engenharia de Software",
        "semestre": "2024.2",
        "tipo_documento": "certificado",
        "gerador": lambda: gerar_pdf("Certificado de Apresentacao em Workshop", "Semana Universitaria de Informatica - WER 2024", "Sofia Menezes Duarte"),
    },
    {
        "id": 16,
        "nome_original": "declaracao_horas_atividades_extensao.pdf",
        "categoria": "administrativo",
        "descricao": "Declaração de 120 horas computadas em projetos e cursos de extensão universitária",
        "data_upload": "2026-10-01T08:15:30",
        "aluno": "Victor Hugo Silveira",
        "matricula": "537204",
        "curso": "Ciência da Computação",
        "semestre": "2026.1",
        "tipo_documento": "declaracao",
        "gerador": lambda: gerar_pdf("Declaracao de Atividades Complementares", "Total de Horas Integralizadas: 120h de Extensao", "Victor Hugo Silveira"),
    },
]


def popular():
    DIR_DOCUMENTOS.mkdir(parents=True, exist_ok=True)
    DIR_METADATA.mkdir(parents=True, exist_ok=True)

    for item in DIR_DOCUMENTOS.iterdir():
        if item.is_file():
            item.unlink()

    documentos_metadados = []

    for item in DOCUMENTOS_SEED:
        doc_id = item["id"]
        nome_original = item["nome_original"]
        sufixo = Path(nome_original).suffix
        stem = Path(nome_original).stem
        nome_armazenado = f"{doc_id}_{stem}{sufixo}"

        conteudo = item["gerador"]()
        caminho_arquivo = DIR_DOCUMENTOS / nome_armazenado

        with open(caminho_arquivo, "wb") as f:
            f.write(conteudo)

        tamanho = len(conteudo)
        extensao = sufixo.lower()
        tipo_mime = mimetypes.guess_type(nome_original)[0] or "application/octet-stream"
        sha256 = calcular_sha256(conteudo)

        doc_registro = {
            "id": doc_id,
            "nome_original": nome_original,
            "nome_armazenado": nome_armazenado,
            "extensao": extensao,
            "tipo_mime": tipo_mime,
            "tamanho": tamanho,
            "categoria": item["categoria"],
            "descricao": item["descricao"],
            "data_upload": item["data_upload"],
            "sha256": sha256,
            "aluno": item["aluno"],
            "matricula": item["matricula"],
            "curso": item["curso"],
            "semestre": item["semestre"],
            "tipo_documento": item["tipo_documento"],
        }
        documentos_metadados.append(doc_registro)

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(documentos_metadados, f, ensure_ascii=False, indent=2)

    print(f"Sucesso! {len(documentos_metadados)} documentos criados em '{DIR_DOCUMENTOS}'")
    print(f"Catalogo atualizado em '{METADATA_FILE}'")


if __name__ == "__main__":
    popular()
