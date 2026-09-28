# 📚 ESPECIFICAÇÃO TÉCNICA E ARQUITETURAL
## Cofre Digital de Documentos Acadêmicos (FastAPI & Persistência em Arquivos)

> **Disciplina:** QXD0099 - Desenvolvimento de Software para Persistência — UFC Quixadá  
> **Professor:** Francisco Victor da Silva Pinheiro  
> **Tema Escolhido:** Documentos Acadêmicos (Artigos, TCCs, Dissertações, Teses, Projetos de Pesquisa, Relatórios Técnicos)  
> **Stack:** Python 3.11+ | FastAPI | Pydantic v2 | YAML | JSON/CSV/XML/ZIP Persistence  

---

## 📑 Sumário

1. [Visão Geral e Objetivo do Sistema](#1-visão-geral-e-objetivo-do-sistema)
2. [Guia de Transição: Spring Boot (Java) ➔ FastAPI (Python)](#2-guia-de-transição-spring-boot-java--fastapi-python)
3. [Arquitetura de Software e Estrutura do Projeto](#3-arquitetura-de-software-e-estrutura-do-projeto)
4. [Estrutura de Armazenamento e Diretórios Físicos](#4-estrutura-de-armazenamento-e-diretórios-físicos)
5. [Modelagem de Dados e Schemas (Pydantic)](#5-modelagem-de-dados-e-schemas-pydantic)
6. [Mecanismo de Persistência Sem Banco de Dados](#6-mecanismo-de-persistência-sem-banco-de-dados)
7. [Catálogo Completo de Endpoints da API REST](#7-catálogo-completo-de-endpoints-da-api-rest)
8. [Detalhamento das Funcionalidades Obrigatórias (F1 a F17)](#8-detalhamento-das-funcionalidades-obrigatórias-f1-a-f17)
9. [Funcionalidades Específicas do Domínio Acadêmico (F16)](#9-funcionalidades-específicas-do-domínio-acadêmico-f16)
10. [Sistema de Configuração Externa (YAML)](#10-sistema-de-configuração-externa-yaml)
11. [Sistema de Logs e Auditoria](#11-sistema-de-logs-e-auditoria)
12. [Mecanismos de Integridade (SHA-256) e Backup](#12-mecanismos-de-integridade-sha-256-e-backup)
13. [Tratamento Global de Erros e Códigos HTTP](#13-tratamento-global-de-erros-e-códigos-http)
14. [Plano de Seed (15 Arquivos para Apresentação)](#14-plano-de-seed-15-arquivos-para-apresentação)
15. [Checklist de Desenvolvimento](#15-checklist-de-desenvolvimento)

---

## 1. Visão Geral e Objetivo do Sistema

O **Cofre Digital de Documentos Acadêmicos** é uma aplicação web desenvolvida com **FastAPI** voltada para o armazenamento seguro, categorização, catalogação, verificação de integridade e exportação de produções científicas e acadêmicas (TCCs, dissertações, teses, artigos de periódicos, relatórios de pesquisa e projetos acadêmicos).

### Restrições Rígidas do Projeto:
- ❌ **É estritamente proibido o uso de bancos de dados** (relacionais como PostgreSQL/MySQL/SQLite ou NoSQL como MongoDB).
- ✅ **A persistência dos metadados deve ser feita em arquivo JSON** (`storage/metadata/documentos.json`).
- ✅ **Formatos manipulados:** JSON (metadados), YAML (configurações), CSV e XML (exportações), ZIP (backups compactados), `.log` (auditoria e logs) e arquivos binários/texto (PDF, DOCX, TeX, TXT, MD, CSV, etc.).
- ✅ Os dados devem persistir entre reinicializações da aplicação.
- ✅ O sistema deve possuir tolerância a concorrência básica e atomicidade na escrita de arquivos.

---

## 2. Guia de Transição: Spring Boot (Java) ➔ FastAPI (Python)

Para desenvolvedores acostumados com o ecossistema Spring Boot, a tabela abaixo mapeia cada conceito e padrão arquitetural do Spring para o equivalente idiomático no FastAPI/Python:

| Conceito / Camada | Spring Boot (Java) | FastAPI (Python) | Observações & Boas Práticas |
| :--- | :--- | :--- | :--- |
| **Controlador Web** | `@RestController` / `@RequestMapping` | `APIRouter` (em `routers/`) | Módulos com rotas agrupadas por domínio e incluídas na app principal via `app.include_router()`. |
| **Mapeamento de Rotas** | `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping` | `@router.get()`, `@router.post()`, `@router.put()`, `@router.delete()` | Decoradores diretos nos métodos/funções de rota. |
| **Injeção de Dependências** | `@Autowired` / Construtor / Spring IoC Container | `Depends()` (`fastapi.Depends`) | O FastAPI usa um sistema de injeção de dependência baseado em funções geradoras (`yield` ou `return`), ideal para injetar serviços e repositórios. |
| **Camada de Serviço** | `@Service` (ex: `DocumentoService.java`) | Classes Service normais (ex: `DocumentoService`) injetadas via `Depends()` | Contém a regra de negócio, cálculos de hash, coordenação de backup e validações. |
| **Camada de Acesso a Dados** | `@Repository` / `JpaRepository<T, ID>` | `DocumentoRepository` / `JsonMetadataRepository` | Responsável pela leitura/escrita no `documentos.json` com trava de arquivo (*file lock* / escrita atômica). |
| **Entidades e DTOs** | `@Entity`, `record`, DTOs com Lombok e Jakarta Validation (`@NotNull`, `@Size`) | Classes herdando de `pydantic.BaseModel` com `Field(...)` | Validação automática de tipos, serialização/deserialização JSON e documentação Swagger/OpenAPI nativa. |
| **Upload de Arquivos** | `MultipartFile file` | `UploadFile = File(...)` | `UploadFile` provê interface assíncrona/streaming para arquivos sem carregar tudo em memória de uma só vez. |
| **Respostas HTTP** | `ResponseEntity<T>`, `Resource` | `JSONResponse`, `FileResponse`, `StreamingResponse` | `FileResponse` é perfeito para o download de binários com `Content-Disposition`. |
| **Tratamento de Exceções** | `@ControllerAdvice` + `@ExceptionHandler` | `@app.exception_handler(CustomException)` | Manipuladores globais que capturam exceções de domínio e retornam JSON padronizado com status adequado. |
| **Configurações da Aplicação** | `application.yml` + `@ConfigurationProperties` | `config.yaml` + `pydantic-settings` ou `PyYAML` | Carregamento tipado e centralizado das configurações em um Singleton `Settings`. |
| **Logging** | SLF4J + Logback (`LoggerFactory.getLogger()`) | `import logging` configurado com `logging.FileHandler` | Formatação padronizada gravando no `storage/logs/sistema.log`. |
| **Ciclo de Vida da App** | `@PostConstruct`, `@PreDestroy`, `ApplicationListener` | `@asynccontextmanager` com `lifespan(app: FastAPI)` | Inicializa diretórios de armazenamento e configurações no startup e faz cleanup no shutdown. |

---

## 3. Arquitetura de Software e Estrutura do Projeto

Adotaremos a **Arquitetura em Camadas (Layered Architecture)** aderente aos padrões de mercado do Python e compatível com a separação clássica do Spring (Controller ➔ Service ➔ Repository):

```
trabalho1-persistencia/
├── config.yaml                     # Arquivo de configuração externo (YAML)
├── requirements.txt                # Dependências do projeto
├── README.md                       # Documentação exigida para entrega
├── seed.py                         # Script para pré-popular 15 documentos acadêmicos
├── app/
│   ├── __init__.py
│   ├── main.py                     # Entrypoint da aplicação FastAPI & Lifespan
│   ├── core/                       # Configurações globais, segurança e logging
│   │   ├── __init__.py
│   │   ├── config.py               # Leitor e validação do config.yaml
│   │   ├── logging_config.py       # Configuração do Logger Python (storage/logs/sistema.log)
│   │   └── exceptions.py          # Exceções customizadas de negócio
│   ├── models/                     # Entidades Pydantic (Domínio e Persistência)
│   │   ├── __init__.py
│   │   ├── documento.py            # Modelo principal do Documento + Metadados Acadêmicos
│   │   └── integridade.py          # Modelos de resposta de integridade
│   ├── schemas/                    # DTOs (Request / Response / Filtros)
│   │   ├── __init__.py
│   │   ├── documento_schema.py     # Schemas de criação, atualização e listagem
│   │   ├── estatisticas_schema.py  # DTO para F8 (Estatísticas)
│   │   └── backup_schema.py        # DTO para listagem de backups
│   ├── repositories/               # Camada de Persistência em Arquivos (DAO)
│   │   ├── __init__.py
│   │   ├── json_repository.py      # CRUD no storage/metadata/documentos.json com lock
│   │   └── file_storage.py         # Armazenamento e deleção de binários em storage/documents/
│   ├── services/                   # Camada de Regras de Negócio (Services)
│   │   ├── __init__.py
│   │   ├── documento_service.py    # Regras de upload, SHA-256, consulta, atualização
│   │   ├── integridade_service.py  # Recálculo de hash e auditoria de integridade
│   │   ├── export_service.py       # Gerador de CSV e XML Acadêmico
│   │   ├── backup_service.py       # Criação e listagem de backups ZIP
│   │   └── academico_service.py    # Funcionalidade do tema (ABNT, BibTeX, Produção)
│   └── routers/                    # Camada de Controladores (FastAPI APIRouter)
│       ├── __init__.py
│       ├── documentos_router.py    # Endpoints F1, F2, F3, F4, F5, F6, F7, F8
│       ├── integridade_router.py   # Endpoints F9, F10
│       ├── export_router.py        # Endpoints F13 e Exportação XML
│       ├── backup_router.py        # Endpoints F14, F15
│       └── academico_router.py     # Endpoints F16 (Citações ABNT/BibTeX, Relatório de Produção)
└── storage/                        # Diretório isolado de dados persistidos
    ├── documents/                  # Arquivos físicos armazenados (ex: 1_tcc_ia.pdf)
    ├── metadata/                   # Metadados principais (documentos.json)
    ├── logs/                       # Logs do sistema (sistema.log)
    ├── exports/                    # Arquivos exportados temporários/permanentes (CSV/XML)
    └── backups/                    # Arquivos de backup compactados (.zip)
```

---

## 4. Estrutura de Armazenamento e Diretórios Físicos

O sistema gerenciará pastas específicas para manter estrita separação de responsabilidades:

| Diretório | Finalidade | Formato dos Arquivos |
| :--- | :--- | :--- |
| `storage/documents/` | Guarda os arquivos originais físicos enviados via upload. O nome segue o padrão `{id}_{nome_sanitizado}` para evitar colisões. | Binário / Texto (`.pdf`, `.docx`, `.tex`, `.txt`, `.md`, `.csv`) |
| `storage/metadata/` | Armazena a base central de metadados dos documentos cadastrados (`documentos.json`). | JSON estruturado |
| `storage/logs/` | Guarda o log unificado de operações da aplicação (`sistema.log`). | Texto estruturado (`.log`) |
| `storage/exports/` | Armazena catálogos e relatórios gerados para download do usuário. | CSV, XML |
| `storage/backups/` | Armazena os pacotes de backup compactados com carimbo de data/hora (ex: `backup_2026-09-10_1430.zip`). | ZIP |

---

## 5. Modelagem de Dados e Schemas (Pydantic)

### 5.1. Entidade Principal (`Documento` e `DocumentoAcademico`)

O modelo integra os campos gerais exigidos pelo professor e os metadados específicos do domínio de **Documentos Acadêmicos**:

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class CategoriaAcademica(str, Enum):
    ARTIGO = "artigo"
    TCC = "tcc"
    DISSERTACAO = "dissertacao"
    TESE = "tese"
    PROJETO_PESQUISA = "projeto_pesquisa"
    RELATORIO_TECNICO = "relatorio_tecnico"
    OUTROS = "outros"

class Documento(BaseModel):
    # --- Metadados Gerais Obrigatórios (Requisito Seção 4) ---
    id: int = Field(..., description="Identificador único sequencial do documento")
    nome_original: str = Field(..., description="Nome original do arquivo no momento do upload")
    nome_armazenado: str = Field(..., description="Nome do arquivo físico salvo no disco ({id}_{nome_original})")
    extensao: str = Field(..., description="Extensão do arquivo incluindo o ponto (ex: .pdf, .docx)")
    tipo_mime: str = Field(..., description="Tipo MIME detectado (ex: application/pdf, text/plain)")
    tamanho: int = Field(..., description="Tamanho do arquivo em bytes")
    categoria: CategoriaAcademica = Field(..., description="Categoria do documento acadêmico")
    descricao: str = Field(..., description="Breve resumo ou descrição do conteúdo")
    data_upload: str = Field(..., description="Data e hora do upload no formato ISO 8601")
    sha256: str = Field(..., description="Hash SHA-256 calculado no momento do upload")

    # --- Metadados Específicos do Domínio (Documentos Acadêmicos) ---
    titulo: str = Field(..., description="Título oficial do trabalho acadêmico")
    autores: List[str] = Field(..., min_length=1, description="Lista com os nomes completos dos autores")
    orientador: Optional[str] = Field(None, description="Nome do professor orientador (se aplicável)")
    instituicao: str = Field(default="UFC - Universidade Federal do Ceará", description="Instituição de ensino/pesquisa")
    curso: str = Field(..., description="Curso ou programa de pós-graduação (ex: Engenharia de Software, Ciência da Computação)")
    ano_publicacao: int = Field(..., ge=1900, le=2100, description="Ano de publicação ou defesa do documento")
    palavras_chave: List[str] = Field(default_factory=list, description="Palavras-chave do trabalho")
    area_conhecimento: str = Field(..., description="Área do conhecimento CNPq (ex: Ciência da Computação / Engenharia de Software)")
    doi_ou_identificador: Optional[str] = Field(None, description="Código DOI, ISBN ou identificador de registro acadêmico")
```

### 5.2. Exemplo de Registro no `storage/metadata/documentos.json`:

```json
[
  {
    "id": 1,
    "nome_original": "analise_arquiteturas_microservicos.pdf",
    "nome_armazenado": "1_analise_arquiteturas_microservicos.pdf",
    "extensao": ".pdf",
    "tipo_mime": "application/pdf",
    "tamanho": 1245890,
    "categoria": "tcc",
    "descricao": "Trabalho de conclusão de curso sobre persistência e microserviços.",
    "data_upload": "2026-09-10T14:32:18",
    "sha256": "34ab72f10b892a348bca612e4f58c70129bc98ef1a72635418b761092a48cd89",
    "titulo": "Análise Comparativa de Padrões de Persistência em Microsserviços",
    "autores": ["Lucas Martins de Alencar", "Ana Beatriz Silva"],
    "orientador": "Prof. Dr. Francisco Victor da Silva Pinheiro",
    "instituicao": "Universidade Federal do Ceará - Campus Quixadá",
    "curso": "Engenharia de Software",
    "ano_publicacao": 2026,
    "palavras_chave": ["persistencia", "microsservicos", "fastapi", "spring boot"],
    "area_conhecimento": "Ciência da Computação / Engenharia de Software",
    "doi_ou_identificador": "UFC-QXD-ES-2026-001"
  }
]
```

### 5.3. Schemas de Request / Response (DTOs)

- **`DocumentoCreateForm`**: Dados recebidos via `Form(...)` no endpoint de Upload (Multipart).
- **`DocumentoUpdateDTO`**: Campos opcionais editáveis via `PUT /documentos/{id}` (não permite alterar o arquivo físico ou o hash, apenas metadados).
- **`DocumentoResponseDTO`**: Retorno completo com todos os dados sanitizados.
- **`EstatisticasResponseDTO`**: Totais gerais, distribuições e métricas acadêmicas.
- **`IntegridadeIndividualResponseDTO`**: `{ id, nome, hash_original, hash_atual, integro: bool }`.
- **`IntegridadeGlobalResponseDTO`**: `{ total_verificados, total_integros, total_alterados, total_inexistentes, detalhes: [...] }`.
- **`CitacaoResponseDTO`**: Citações formatadas em **ABNT (NBR 6023)** e **BibTeX**.

---

## 6. Mecanismo de Persistência Sem Banco de Dados

### 6.1. O Repositório JSON (`JsonMetadataRepository`)
No Spring Boot, um `@Repository` delega para o JPA/Hibernate. Aqui, o `JsonMetadataRepository` lê e escreve diretamente no `storage/metadata/documentos.json`.

#### Garantias de Confiabilidade:
1. **Atomicidade na Escrita (Atomic Write Pattern):**
   Ao salvar os dados, gravamos primeiro em um arquivo temporário (`documentos.json.tmp`) no mesmo sistema de arquivos e depois realizamos um `os.replace(temp_path, final_path)`. Isso garante que uma falha de energia ou interrupção no meio do salvamento não corrompa o arquivo JSON original.
2. **Controle de Concorrência (Thread-Safety):**
   Utilização de `threading.RLock()` dentro do repositório para evitar que requisições simultâneas causem *race condition* na leitura/escrita do arquivo.
3. **Geração de ID Sequencial Seguro:**
   O ID é calculado como `max([doc.id for doc in docs], default=0) + 1`.

```python
# Exemplo conceitual do Repositório
import json
import os
import tempfile
from threading import RLock
from typing import List, Optional
from app.models.documento import Documento

class JsonMetadataRepository:
    def __init__(self, metadata_file_path: str):
        self.file_path = metadata_file_path
        self._lock = RLock()
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def find_all(self) -> List[Documento]:
        with self._lock:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Documento(**item) for item in data]

    def save_all(self, documentos: List[Documento]) -> None:
        with self._lock:
            dir_name = os.path.dirname(self.file_path)
            # Escrita atômica via arquivo temporário
            with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
                json.dump([d.model_dump() for d in documentos], tf, indent=2, ensure_ascii=False)
                temp_name = tf.name
            os.replace(temp_name, self.file_path)
```

---

## 7. Catálogo Completo de Endpoints da API REST

Abaixo está a matriz completa de rotas, métodos, parâmetros, status HTTP e códigos de retorno:

| # | Método | Endpoint | Parâmetros / Body | Status Sucesso | Descrição |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **F1** | `POST` | `/documentos` | `file: UploadFile` + `Form(...)` com metadados | `201 Created` | Realiza upload, salva binário, calcula SHA-256 e persiste metadados no JSON. |
| **F2** | `GET` | `/documentos` | Nenhum (ou filtros combinados de F7) | `200 OK` | Retorna lista de todos os documentos persistidos. |
| **F3** | `GET` | `/documentos/{id}` | Path: `id: int` | `200 OK` / `404` | Consulta os metadados de um documento específico por ID. |
| **F4** | `GET` | `/documentos/{id}/download` | Path: `id: int` | `200 OK` / `404` | Baixa o arquivo binário original intacto (`FileResponse`). |
| **F5** | `PUT` | `/documentos/{id}` | Path: `id: int`, Body: `DocumentoUpdateDTO` | `200 OK` / `404` | Atualiza metadados no JSON sem modificar o arquivo físico. |
| **F6** | `DELETE`| `/documentos/{id}` | Path: `id: int` | `200 OK` / `404` | Remove metadados do JSON e apaga o arquivo físico correspondente. |
| **F7** | `GET` | `/documentos` (Filtros) | Query: `categoria`, `extensao`, `autor`, `orientador`, `ano`, `curso`, `palavra_chave` | `200 OK` | Filtra documentos por atributos gerais e específicos acadêmicos. |
| **F8** | `GET` | `/documentos/estatisticas` | Nenhum | `200 OK` | Calcula estatísticas agregadas (tamanho total, por extensão, por categoria, por orientador, etc.). |
| **F9** | `GET` | `/documentos/{id}/integridade` | Path: `id: int` | `200 OK` / `404` | Recalcula SHA-256 do arquivo físico e compara com o valor original salvo. |
| **F10**| `GET` | `/integridade` | Nenhum | `200 OK` | Executa varredura global de integridade em todos os arquivos cadastrados. |
| **F13**| `GET` | `/exportar/csv` | Nenhum | `200 OK` | Gera e retorna download de catálogo consolidado em formato CSV. |
| **F13.2**| `GET`| `/exportar/xml` | Nenhum | `200 OK` | Gera e retorna catálogo estruturado em formato XML acadêmico. |
| **F14**| `POST`| `/backup` | Query opcional: `categoria`, `ano`, `curso` | `201 Created` | Cria pacote compactado ZIP com documentos e metadados. Suporta backup geral ou seletivo. |
| **F15**| `GET` | `/backups` | Nenhum | `200 OK` | Lista todos os arquivos de backup `.zip` disponíveis com data e tamanho. |
| **F16.1**| `GET`| `/documentos/{id}/citacao` | Path: `id: int`, Query: `formato=abnt\|bibtex` | `200 OK` / `404` | Gera citação bibliográfica formatada (ABNT NBR 6023 ou BibTeX). |
| **F16.2**| `GET`| `/academicos/relatorio-producao` | Query opcional: `ano`, `curso`, `orientador` | `200 OK` | Gera relatório consolidado de produção científica e métricas por orientador/curso. |
| **F16.3**| `GET`| `/documentos/exportar/bibtex` | Nenhum | `200 OK` | Exporta arquivo `.bib` contendo todas as referências acadêmicas do cofre. |

---

## 8. Detalhamento das Funcionalidades Obrigatórias (F1 a F17)

### F1 — Upload e Armazenamento de Arquivos
- **Endpoint:** `POST /documentos`
- **Funcionamento:**
  1. O arquivo binário é lido em blocos (chunks) via `UploadFile`.
  2. Gera ID sequencial único.
  3. Preserva o `nome_original` e define `nome_armazenado` como `{id}_{nome_original_sanitizado}`.
  4. Salva o arquivo em `storage/documents/`.
  5. Identifica extensão (`.pdf`, `.docx`, etc.) e tipo MIME (`python-magic` ou `mimetypes`).
  6. Calcula o tamanho em bytes e o hash **SHA-256** do conteúdo.
  7. Instancia o modelo `Documento` com os metadados acadêmicos fornecidos no formulário.
  8. Adiciona ao `documentos.json` atomicamente.
  9. Registra no log: `YYYY-MM-DD HH:MM:SS INFO UPLOAD id={id} arquivo={nome_original}`.
  10. Retorna `201 Created` com o objeto completo.

### F2 — Listagem de Documentos
- **Endpoint:** `GET /documentos`
- **Funcionamento:** Lê todos os registros de `storage/metadata/documentos.json` e retorna lista de documentos. Registra log `INFO CONSULTA total={n}`.

### F3 — Consulta de Documento por Identificador
- **Endpoint:** `GET /documentos/{id}`
- **Funcionamento:** Busca o documento no JSON pelo `id`.
  - Se encontrado: retorna `200 OK` com os metadados.
  - Se não encontrado: registra `ERROR DOCUMENTO_NAO_ENCONTRADO id={id}` e lança `404 Not Found`.

### F4 — Download do Arquivo
- **Endpoint:** `GET /documentos/{id}/download`
- **Funcionamento:**
  1. Localiza metadados do documento no JSON.
  2. Verifica se o arquivo físico existe em `storage/documents/{nome_armazenado}`.
  3. Se o arquivo físico não for encontrado (embora esteja no JSON), retorna `404 Not Found` com mensagem específica "Arquivo físico não encontrado no armazenamento".
  4. Retorna `FileResponse` definindo `filename=documento.nome_original` e `media_type=documento.tipo_mime`.
  5. Garante integridade binária total (streaming sem reencodificação de bytes).
  6. Registra log: `INFO DOWNLOAD id={id} arquivo={nome_original}`.

### F5 — Atualização de Metadados
- **Endpoint:** `PUT /documentos/{id}`
- **Funcionamento:**
  1. Permite atualizar: `titulo`, `descricao`, `categoria`, `autores`, `orientador`, `curso`, `ano_publicacao`, `palavras_chave`, `area_conhecimento`, `doi_ou_identificador`.
  2. **Não permite alterar:** `id`, `nome_original`, `nome_armazenado`, `extensao`, `tipo_mime`, `tamanho`, `data_upload` e `sha256` (garante consistência com o arquivo físico).
  3. Atualiza o JSON e grava no log: `INFO ATUALIZACAO id={id}`.

### F6 — Exclusão de Documentos
- **Endpoint:** `DELETE /documentos/{id}`
- **Funcionamento:**
  1. Localiza o registro no JSON.
  2. Remove o arquivo físico de `storage/documents/{nome_armazenado}` (se existir).
  3. Remove o registro do `storage/metadata/documentos.json`.
  4. Registra no log: `INFO EXCLUSAO id={id} arquivo={nome_original}`.
  5. Retorna `200 OK` com mensagem de confirmação: `{"mensagem": "Documento e arquivo físico removidos com sucesso", "id": id}`.

### F7 — Filtragem de Documentos
- **Endpoint:** `GET /documentos?categoria=tcc&ano_publicacao=2026&orientador=Pinheiro`
- **Critérios Suportados (Gerais + Acadêmicos):**
  - Geral 1: `categoria` (ex: `tcc`, `artigo`, `dissertacao`)
  - Geral 2: `extensao` (ex: `.pdf`, `.docx`)
  - Específico 1: `autor` (busca parcial por nome do autor)
  - Específico 2: `orientador` (busca parcial por nome do orientador)
  - Específico 3: `ano_publicacao` (ano exato ou intervalo)
  - Específico 4: `curso` (ex: `Engenharia de Software`)
  - Específico 5: `palavra_chave` (busca dentro da lista de tags)
- Os filtros podem ser combinados livremente com lógica AND.

### F8 — Estatísticas do Cofre Digital
- **Endpoint:** `GET /documentos/estatisticas`
- **Retorno Obrigatório Calculado em Tempo Real:**
  ```json
  {
    "total_documentos": 20,
    "espaco_utilizado_bytes": 15489020,
    "espaco_utilizado_formatado": "14.77 MB",
    "por_extensao": {
      ".pdf": 12,
      ".docx": 4,
      ".tex": 2,
      ".txt": 2
    },
    "por_categoria": {
      "tcc": 8,
      "artigo": 7,
      "dissertacao": 3,
      "projeto_pesquisa": 2
    },
    "estatisticas_academicas": {
      "total_autores_unicos": 35,
      "total_orientadores_unicos": 8,
      "por_curso": {
        "Engenharia de Software": 12,
        "Ciência da Computação": 6,
        "Design Digital": 2
      },
      "por_ano": {
        "2026": 10,
        "2025": 7,
        "2024": 3
      }
    }
  }
  ```

### F9 — Verificação de Integridade Individual
- **Endpoint:** `GET /documentos/{id}/integridade`
- **Funcionamento:**
  1. Carrega metadados do documento pelo `id`.
  2. Abre o arquivo físico `storage/documents/{nome_armazenado}` e calcula o hash SHA-256 atual em streaming.
  3. Compara `hash_atual` com `hash_original` (salvo no JSON).
  4. Se forem iguais: `integro = true`. Registra `INFO INTEGRIDADE_OK id={id}`.
  5. Se forem diferentes: `integro = false`. Registra `WARNING INTEGRIDADE_FALHOU id={id} hash_esperado={...} hash_encontrado={...}`.
  6. Resposta:
     ```json
     {
       "id": 1,
       "nome_original": "tcc_arquitetura.pdf",
       "hash_original": "34ab72...",
       "hash_atual": "34ab72...",
       "integro": true
     }
     ```

### F10 — Verificação Global de Integridade
- **Endpoint:** `GET /integridade`
- **Funcionamento:**
  Itera por todos os documentos cadastrados no JSON e verifica a integridade de cada um contra o disco.
- **Resposta:**
  ```json
  {
    "total_verificados": 20,
    "total_integros": 19,
    "total_alterados": 1,
    "arquivos_nao_localizados": 0,
    "detalhes": [
      {
        "id": 5,
        "nome_original": "artigo_violado.pdf",
        "status": "ALTERADO",
        "hash_original": "aa123...",
        "hash_atual": "ff999..."
      }
    ]
  }
  ```

### F11 — Sistema de Logging
- Arquivo: `storage/logs/sistema.log`
- Padrão da Linha de Log:  
  `YYYY-MM-DD HH:MM:SS LEVEL OPERACAO informacoes...`
- Exemplo:
  ```text
  2026-09-10 14:32:18 INFO UPLOAD id=10 arquivo=tcc_ia.pdf tamanho=1048576 sha256=34ab72...
  2026-09-10 14:35:09 INFO DOWNLOAD id=10 arquivo=tcc_ia.pdf
  2026-09-10 14:38:41 WARNING INTEGRIDADE_FALHOU id=10 arquivo=tcc_ia.pdf
  2026-09-10 14:42:15 ERROR DOCUMENTO_NAO_ENCONTRADO id=50
  2026-09-10 14:45:00 INFO BACKUP_CRIADO arquivo=backup_2026-09-10_1445.zip total_arquivos=15
  ```

### F12 — Arquivo de Configuração Externa (`config.yaml`)
A aplicação lê ativamente o arquivo `config.yaml` na inicialização e reflete alterações nos diretórios, limites de upload, algoritmo de hash e níveis de log. (Ver Seção 10).

### F13 — Exportação para CSV e XML
- **CSV (`GET /exportar/csv`):** Gera um arquivo `.csv` formatado com cabeçalho contendo todos os documentos e metadados acadêmicos (separador vírgula ou ponto-e-vírgula com escape correto de campos).
- **XML (`GET /exportar/xml`):** Gera um arquivo XML estruturado (padrão repositório institucional) contendo a árvore de trabalhos e autores.

### F14 — Backup Compactado (Geral e Seletivo)
- **Endpoint:** `POST /backup` (Parâmetros opcionais: `categoria`, `ano`, `curso`)
- **Funcionamento:**
  1. Cria um arquivo `.zip` dentro de `storage/backups/`.
  2. Nome: `backup_YYYY-MM-DD_HHMM.zip` (se já existir no mesmo minuto, adiciona sufixo `_1`, `_2` para evitar sobrescrita indevida).
  3. O ZIP contém:
     - Os arquivos físicos selecionados (`documents/`)
     - O JSON de metadados correspondente aos arquivos incluídos (`metadata/documentos.json`)
     - O arquivo de configuração atual (`config.yaml`)
     - O log atual da aplicação (`logs/sistema.log`)
  4. Registra no log: `INFO BACKUP_CRIADO arquivo={nome_zip} total_arquivos={n}`.
  5. Retorna `201 Created` com o nome do arquivo, tamanho e lista de documentos incluídos.

### F15 — Listagem de Backups
- **Endpoint:** `GET /backups`
- **Funcionamento:** Lê os arquivos `.zip` em `storage/backups/` e retorna nome, tamanho em bytes e data de criação.

---

## 9. Funcionalidades Específicas do Domínio Acadêmico (F16)

Para enriquecer o trabalho e atender com excelência o requisito **F16 (Funcionalidade Específica do Tema)**, implementaremos um conjunto de operações nativas do ecossistema acadêmico:

### F16.1 — Gerador de Citação Bibliográfica (ABNT NBR 6023 & BibTeX)
- **Endpoint:** `GET /documentos/{id}/citacao?formato=abnt` ou `formato=bibtex`
- **Regra ABNT:** Converte os autores para `SOBRENOME, Nome`, formata o título em negrito/itálico, inclui instituição, curso, ano e DOI.
  - *Exemplo ABNT:* `ALENCAR, Lucas Martins de; SILVA, Ana Beatriz. Análise Comparativa de Padrões de Persistência em Microsserviços. Trabalho de Conclusão de Curso (Graduação em Engenharia de Software) - Universidade Federal do Ceará, Quixadá, 2026.`
- **Regra BibTeX:** Gera a entrada `@misc{...}`, `@mastersthesis{...}` ou `@article{...}` pronta para ser importada no LaTeX.
  - *Exemplo BibTeX:*
    ```bibtex
    @mastersthesis{alencar2026analise,
      author = {Lucas Martins de Alencar and Ana Beatriz Silva},
      title = {Análise Comparativa de Padrões de Persistência em Microsserviços},
      school = {Universidade Federal do Ceará},
      year = {2026},
      type = {Trabalho de Conclusão de Curso},
      address = {Quixadá}
    }
    ```

### F16.2 — Relatório Consolidado de Produção Acadêmica
- **Endpoint:** `GET /academicos/relatorio-producao?orientador=Pinheiro&ano=2026`
- **Funcionamento:** Agrupa os trabalhos por orientador, curso e área de conhecimento, calculando métricas de produtividade acadêmica, volume de páginas/bytes e distribuição por categoria.

### F16.3 — Exportação Global BibTeX
- **Endpoint:** `GET /documentos/exportar/bibtex`
- **Funcionamento:** Gera um arquivo `.bib` para download contendo o banco de referências completo de todos os documentos do cofre.

---

## 10. Sistema de Configuração Externa (YAML)

O arquivo `config.yaml` deve residir na raiz do projeto e controlar o comportamento do sistema sem necessidade de alterar o código-fonte:

```yaml
app:
  nome: "Cofre Digital de Documentos Acadêmicos"
  versao: "1.0.0"
  ambiente: "desenvolvimento"

storage:
  diretorio_base: "./storage"
  diretorio_documentos: "./storage/documents"
  diretorio_metadados: "./storage/metadata"
  arquivo_metadados: "./storage/metadata/documentos.json"
  diretorio_logs: "./storage/logs"
  diretorio_exports: "./storage/exports"
  diretorio_backups: "./storage/backups"

upload:
  tamanho_maximo_mb: 50
  extensoes_permitidas:
    - ".pdf"
    - ".docx"
    - ".tex"
    - ".txt"
    - ".md"
    - ".csv"
    - ".xml"
    - ".json"

hash:
  algoritmo: "sha256"
  buffer_size_bytes: 65536  # 64 KB para leitura em streaming

logging:
  arquivo: "./storage/logs/sistema.log"
  nivel: "INFO"             # DEBUG, INFO, WARNING, ERROR, CRITICAL
  formato: "%(asctime)s %(levelname)s %(message)s"
  formato_data: "%Y-%m-%d %H:%M:%S"

backup:
  formato: "zip"
  compressao_nivel: 6
```

### Carregador de Configuração em Python (`app/core/config.py`):
Equivalente ao `@ConfigurationProperties` do Spring:

```python
import yaml
from pathlib import Path
from pydantic import BaseModel

class AppSettings(BaseModel):
    # Modelagem espelhada do config.yaml
    ...

def load_settings(config_path: str = "config.yaml") -> AppSettings:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de configuracao {config_path} nao encontrado.")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return AppSettings(**data)
```

---

## 11. Sistema de Logs e Auditoria

### Configuração do Logger Python (`app/core/logging_config.py`):
Equivalente ao `logback-spring.xml`:

```python
import logging
import os
from app.core.config import AppSettings

def setup_logging(settings: AppSettings) -> logging.Logger:
    log_file = settings.storage.diretorio_logs / "sistema.log"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger("cofre_digital")
    logger.setLevel(getattr(logging, settings.logging.nivel.upper(), logging.INFO))
    
    # Evita handlers duplicados ao reiniciar
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # File Handler (Persistência em storage/logs/sistema.log)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console Handler (Para visualização no terminal)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
```

---

## 12. Mecanismos de Integridade (SHA-256) e Backup

### 12.1. Cálculo de Hash SHA-256 em Streaming (Memory-Safe)
Para evitar carregar arquivos gigantes (ex: PDFs de 50MB) inteiramente na memória RAM, o cálculo do hash deve ser feito em pedaços de 64KB:

```python
import hashlib
from typing import BinaryIO

def calcular_sha256_stream(file_obj: BinaryIO, buffer_size: int = 65536) -> str:
    sha256_hash = hashlib.sha256()
    file_obj.seek(0)
    while chunk := file_obj.read(buffer_size):
        sha256_hash.update(chunk)
    file_obj.seek(0)  # Restaura o ponteiro para o início
    return sha256_hash.hexdigest()
```

### 12.2. Empacotamento de Backup ZIP
Utiliza a biblioteca padrão `zipfile` do Python para criar o arquivo compactado contendo arquivos físicos, metadados e logs, prevenindo qualquer sobrescrita acidental com verificação prévia de nomes existentes.

---

## 13. Tratamento Global de Erros e Códigos HTTP

No Spring Boot utilizamos `@ControllerAdvice` e `@ExceptionHandler`. No FastAPI, usamos manipuladores globais via `app.add_exception_handler()`:

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse

class DocumentoNaoEncontradoException(Exception):
    def __init__(self, doc_id: int):
        self.doc_id = doc_id
        self.message = f"Documento com identificador {doc_id} não foi encontrado."

async def documento_nao_encontrado_handler(request: Request, exc: DocumentoNaoEncontradoException):
    logger.error(f"DOCUMENTO_NAO_ENCONTRADO id={exc.doc_id}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "status": 404,
            "erro": "Not Found",
            "mensagem": exc.message,
            "caminho": request.url.path
        }
    )
```

### Mapeamento Padronizado de Códigos HTTP:
- `200 OK`: Consulta, listagem, atualização, exclusão, integridade e exportação concluídas com êxito.
- `201 Created`: Upload de documento ou criação de backup concluído com sucesso.
- `400 Bad Request`: Requisição malformada, formato de arquivo não suportado ou erro de validação sintática.
- `404 Not Found`: Documento não encontrado no JSON ou arquivo físico ausente no disco.
- `409 Conflict`: Tentativa de criar backup com nome já existente ou conflito de integridade.
- `422 Unprocessable Entity`: Erro de validação nos campos do Pydantic (ex: ano fora da faixa válida).
- `500 Internal Server Error`: Falha de I/O em disco, erro de permissão ou falha inesperada.

---

## 14. Plano de Seed (15 Arquivos para Apresentação)

Conforme a **Seção 7 (Dados para Apresentação)** da especificação do professor, o sistema deve possuir antes da apresentação:
- **No mínimo 15 arquivos armazenados**
- **Pelo menos 4 extensões diferentes** (`.pdf`, `.docx`, `.tex`, `.txt`, `.md`, `.csv`)
- **Pelo menos 3 categorias diferentes** (`artigo`, `tcc`, `dissertacao`, `tese`, `projeto_pesquisa`, `relatorio_tecnico`)
- Arquivos de texto e pelo menos um arquivo binário real
- Metadados adequadamente persistidos no `storage/metadata/documentos.json`

### Tabela de Pré-Carga (Seed de Dados Acadêmicos):

| ID | Título do Trabalho | Categoria | Extensão | Autor(es) | Orientador | Curso | Ano |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | Análise Comparativa de Persistência em Microsserviços | `tcc` | `.pdf` | Lucas Martins de Alencar | Prof. Dr. Francisco Victor | Eng. Software | 2026 |
| **2** | Otimização de Consultas em Bancos NoSQL Distribuídos | `artigo` | `.pdf` | Beatriz Lima, Carlos Eduardo | Prof. Dr. João Paulo | Ciênc. Computação | 2025 |
| **3** | Algoritmos de Machine Learning para Detecção de Fraudes | `dissertacao`| `.docx`| Marcelo Silveira | Profa. Dra. Maria Clara | Ciênc. Computação | 2024 |
| **4** | Arquitetura Segura para Internet das Coisas (IoT) | `tese` | `.pdf` | Juliana Ribeiro | Prof. Dr. Francisco Victor | Eng. Software | 2025 |
| **5** | Template LaTeX para Trabalhos Acadêmicos da UFC | `relatorio_tecnico` | `.tex` | Comissão de Graduação | Prof. Dr. Alexandre Silva | Eng. Software | 2026 |
| **6** | Estudo sobre Usabilidade em Interfaces Médicas | `artigo` | `.docx`| Rafael Costa | Profa. Dra. Camila Nogueira | Design Digital | 2025 |
| **7** | Implementação de Cofre Digital com FastAPI | `tcc` | `.pdf` | André Pinheiro | Prof. Dr. Francisco Victor | Eng. Software | 2026 |
| **8** | Notas de Aula: Estruturas de Dados Avançadas | `outros` | `.txt` | Gabriel Mendonça | Prof. Dr. João Paulo | Ciênc. Computação | 2024 |
| **9** | Dataset de Desempenho de Criptografia SHA-256 | `projeto_pesquisa`| `.csv` | Laboratório de Redes | Prof. Dr. Roberto Dias | Eng. Software | 2026 |
| **10**| Guia de Normas ABNT NBR 6023 para Monografias | `relatorio_tecnico` | `.md` | Biblioteca Universitária | Profa. Dra. Helena Souza | Geral UFC | 2025 |
| **11**| Análise de Vulnerabilidades em Contratos Inteligentes | `artigo` | `.pdf` | Diego Fernandes | Prof. Dr. Francisco Victor | Eng. Software | 2025 |
| **12**| Proposta de Framework para Computação em Borda | `projeto_pesquisa`| `.docx`| Larissa Carvalho | Prof. Dr. João Paulo | Ciênc. Computação | 2026 |
| **13**| Avaliação de Acessibilidade em Sistemas Web Públicos | `tcc` | `.pdf` | Fernanda Prado | Profa. Dra. Camila Nogueira | Design Digital | 2024 |
| **14**| Monografia sobre Compiladores Just-in-Time | `dissertacao`| `.pdf` | Thiago Rocha | Prof. Dr. Alexandre Silva | Ciênc. Computação | 2025 |
| **15**| Especificação de Protocolo de Comunicação Confiável | `relatorio_tecnico` | `.tex` | Grupo de Pesquisa em Redes | Prof. Dr. Roberto Dias | Eng. Software | 2026 |

O script `seed.py` será responsável por gerar os arquivos físicos em `storage/documents/` com conteúdos válidos e gravar a lista inicial no `storage/metadata/documentos.json`.

---

## 15. Checklist de Desenvolvimento

- [ ] **Configuração do Ambiente:** `requirements.txt` com `fastapi`, `uvicorn`, `pydantic`, `pyyaml`, `python-multipart`, `python-magic` (ou `mimetypes`).
- [ ] **Configuração Externa:** Criação do `config.yaml` e parser tipado `AppSettings`.
- [ ] **Sistema de Logging:** Setup do Logger gravando em `storage/logs/sistema.log` com padrão exigido.
- [ ] **Modelos Pydantic:** Definição de `Documento`, metadados acadêmicos e DTOs de request/response.
- [ ] **Camada de Repositório:** Implementação do `JsonMetadataRepository` com atomic write e lock de concorrência.
- [ ] **Camada de File Storage:** Salvar e deletar binários em `storage/documents/`.
- [ ] **Endpoints CRUD e Download:** F1 (Upload), F2 (List), F3 (Get ID), F4 (Download), F5 (Update), F6 (Delete).
- [ ] **Filtros e Estatísticas:** F7 (Filtros combinados) e F8 (Estatísticas gerais e acadêmicas).
- [ ] **Integridade:** F9 (Verificação individual SHA-256) e F10 (Varredura global de integridade).
- [ ] **Exportações e Backup:** F13 (Exportação CSV e XML), F14 (Criação de Backup ZIP geral e seletivo), F15 (Listagem de backups).
- [ ] **Funcionalidade do Domínio (F16):** Gerador de Citação ABNT e BibTeX, Relatório de Produção Acadêmica.
- [ ] **Tratamento de Exceções:** Custom Exceptions + Handlers globais no FastAPI.
- [ ] **Script de Seed:** `seed.py` criando 15 arquivos com 4+ extensões e 3+ categorias.
- [ ] **Documentação:** Criação do `README.md` completo conforme Seção 8 do documento do professor.
