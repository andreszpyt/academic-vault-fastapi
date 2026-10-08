# Cofre Digital - Documentos Acadêmicos

Sistema de API REST desenvolvido em FastAPI para armazenamento seguro, catalogação, pesquisa avançada, verificação de integridade criptográfica, exportação e backup de documentos acadêmicos, utilizando persistência em arquivos planos (flat-file JSON) sem dependência de bancos de dados relacionais ou ORMs.

---

## Sumário

- [Objetivo](#objetivo)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Requisitos para Execução](#requisitos-para-execução)
- [Instalação](#instalação)
- [Como Iniciar a Aplicação](#como-iniciar-a-aplicação)
- [Estrutura Básica de Diretórios](#estrutura-básica-de-diretórios)
- [Localização dos Dados](#localização-dos-dados)
- [Configuração (`config.yaml`)](#configuração-configyaml)
- [Povoamento Inicial (`seed.py`)](#povoamento-inicial-seedpy)
- [Documentação dos Endpoints](#documentação-dos-endpoints)
- [Exemplos de Requisições](#exemplos-de-requisições)
- [Funcionalidades Específicas](#funcionalidades-específicas)
  - [Exportação XML (F16)](#exportação-xml-f16)
  - [Integridade Criptográfica SHA-256 (F9 e F10)](#integridade-criptográfica-sha-256-f9-e-f10)
  - [Backup e Restauração (F14 e F15)](#backup-e-restauração-f14-e-f15)
  - [Exportação CSV (F13)](#exportação-csv-f13)
  - [Sistema de Logs (F11)](#sistema-de-logs-f11)

---

## Objetivo

Fornecer uma solução simples, robusta e aderente aos requisitos de cofre digital acadêmico para gerenciar arquivos de trabalhos, relatórios, projetos e certificados de estudantes, garantindo:
1. Armazenamento e catalogação de metadados gerais e acadêmicos;
2. Pesquisa flexível com validação em duas camadas;
3. Verificação de integridade física e lógica via hash SHA-256;
4. Exportação estruturada de acervo em XML e CSV;
5. Criação e recuperação de backups compactados em ZIP;
6. Segurança na persistência com escrita atômica e controle de concorrência (`threading.RLock`).

---

## Tecnologias Utilizadas

* **Linguagem:** Python 3.10+
* **Framework Web:** FastAPI
* **Servidor ASGI:** Uvicorn
* **Validação e Tipagem:** Pydantic v2
* **Configuração:** PyYAML
* **Manipulação de Arquivos e Hash:** Bibliotecas padrão `hashlib`, `tempfile`, `threading`, `zipfile`, `csv`, `xml.etree.ElementTree`, `minidom` e `pathlib`

---

## Requisitos para Execução

* Python 3.10 ou superior instalado no sistema operacional;
* Gerenciador de pacotes `pip` e suporte a ambientes virtuais (`venv`).

---

## Instalação

1. Clone ou acerte o diretório do repositório:
   ```bash
   cd FastAPIProject
   ```

2. Crie e ative um ambiente virtual:
   ```bash
   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate

   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

---

## Como Iniciar a Aplicação

Inicie o servidor Uvicorn com hot-reload habilitado:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

* **API Base:** `http://127.0.0.1:8000`
* **Swagger UI (Documentação Interativa):** `http://127.0.0.1:8000/docs`
* **ReDoc:** `http://127.0.0.1:8000/redoc`

---

## Estrutura Básica de Diretórios

```text
.
├── app/
│   ├── config.py             # Leitura do config.yaml e instanciação de constantes
│   ├── logger.py             # Configuração centralizada de logs
│   ├── models.py             # Modelos Pydantic para validação e serialização
│   ├── storage.py            # Persistência flat-file, escrita atômica, RLock e CRUD
│   └── routers/
│       ├── backup.py         # Endpoints de criação, listagem e download de backups
│       ├── documentos.py     # Endpoints de upload, listagem, busca, consulta, update, delete e XML
│       ├── estatisticas.py   # Endpoint de métricas consolidadas (/estatisticas)
│       ├── exportacoes.py    # Endpoint de exportação CSV (/exportar/csv)
│       └── integridade.py    # Endpoint de verificação de integridade global (/integridade)
├── storage/
│   ├── backups/              # Arquivos compactados (.zip) gerados
│   ├── documentos/           # Arquivos físicos armazenados no cofre
│   ├── exports/              # Arquivos CSV exportados
│   ├── logs/                 # Arquivo de log do sistema (sistema.log)
│   └── metadata/             # Metadados em formato JSON (documentos.json)
├── config.yaml               # Arquivo de configuração central do sistema
├── main.py                   # Ponto de entrada FastAPI e handlers de exceção globais
├── requirements.txt          # Dependências do projeto
├── seed.py                   # Script para geração de dados acadêmicos iniciais
├── test_main.http            # Requisições HTTP para testes manuais no IDE
└── README.md                 # Documentação do projeto
```

---

## Localização dos Dados

* **Metadados JSON:** `storage/metadata/documentos.json` — contém a lista de documentos cadastrados com metadados gerais e acadêmicos. As operações de escrita são atômicas (usam arquivo temporário e `os.replace`) e protegidas por `threading.RLock`.
* **Arquivos Físicos:** `storage/documentos/` — armazena os arquivos binários nomeados no padrão `{id}_{nome_limpo}` com prevenção automática de colisões.

---

## Configuração (`config.yaml`)

O arquivo `config.yaml` é carregado no boot do sistema por `app/config.py` e centraliza as diretivas:

```yaml
storage:
  diretorio_documentos: "./storage/documentos"
  diretorio_metadata: "./storage/metadata"
  diretorio_backups: "./storage/backups"
  diretorio_exports: "./storage/exports"

upload:
  tamanho_maximo_mb: 20

hash:
  algoritmo: "sha256"

logging:
  arquivo: "./storage/logs/sistema.log"
  nivel: "INFO"

backup:
  formato: "zip"

servidor:
  host: "0.0.0.0"
  port: 8000
```

---

## Povoamento Inicial (`seed.py`)

O script `seed.py` gera 16 documentos acadêmicos completos distribuídos em 4 extensões distintas (`.pdf`, `.docx`, `.jpg`, `.txt`), criando tanto os registros estruturados no `documentos.json` quanto os arquivos binários correspondentes em `storage/documentos/`.

Para executar o seed:

```bash
python seed.py
```

---

## Documentação dos Endpoints

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/` | Retorna informações básicas e versão da API |
| `POST` | `/documentos` | Realiza upload de documento (`multipart/form-data`) e gera metadados |
| `GET` | `/documentos` | Lista documentos com suporte a filtros opcionais por query parameters |
| `GET` | `/documentos/pesquisar` | Pesquisa avançada exigindo ≥1 atributo geral e ≥2 atributos acadêmicos |
| `GET` | `/documentos/estatisticas` | Retorna totais, espaço em disco e distribuições por categoria, curso, etc. |
| `GET` | `/estatisticas` | Rota alternativa para estatísticas consolidadas do repositório |
| `GET` | `/documentos/{id}` | Consulta metadados de um documento específico |
| `GET` | `/documentos/{id}/download` | Realiza download do arquivo físico armazenado |
| `PUT` | `/documentos/{id}` | Atualiza metadados permitidos (`categoria`, `descricao`, `aluno`, `matricula`, `curso`, `semestre`, `tipo_documento`) |
| `DELETE` | `/documentos/{id}` | Remove documento do `documentos.json` e exclui o arquivo físico correspondente |
| `GET` | `/documentos/{id}/integridade` | Verifica a integridade do arquivo individual comparando hash atual com o original |
| `GET` | `/integridade` | Executa varredura de integridade global em todos os documentos cadastrados |
| `GET` | `/documentos/exportar/xml` | Exporta documentos em formato XML com filtros opcionais por `aluno` e `semestre` |
| `GET` | `/exportar/csv` | Exporta o catálogo completo de metadados em formato CSV |
| `POST` | `/backup` | Cria arquivo ZIP de backup com documentos, metadados, configurações e logs |
| `GET` | `/backups` | Lista os arquivos de backup disponíveis para download |
| `GET` | `/backups/{nome}` | Faz o download de um arquivo de backup compactado específico |

---

## Exemplos de Requisições

### 1. Upload de Documento (`POST /documentos`)
```bash
curl -X POST "http://127.0.0.1:8000/documentos" \
  -F "arquivo=@artigo.pdf" \
  -F "categoria=academico" \
  -F "aluno=Lucas Martins" \
  -F "matricula=512345" \
  -F "curso=Engenharia de Software" \
  -F "semestre=2026.1" \
  -F "tipo_documento=artigo" \
  -F "descricao=Artigo sobre persistência em arquivos JSON"
```

### 2. Pesquisa Avançada (`GET /documentos/pesquisar`)
Exige no mínimo 1 metadado geral (`extensao`, `categoria`, `descricao`, `tipo_mime`, `nome_original`) e no mínimo 2 metadados acadêmicos (`aluno`, `matricula`, `curso`, `semestre`, `tipo_documento`):
```bash
curl -X GET "http://127.0.0.1:8000/documentos/pesquisar?extensao=pdf&aluno=Lucas&curso=Engenharia"
```

### 3. Consulta de Documento por ID (`GET /documentos/{id}`)
```bash
curl -X GET "http://127.0.0.1:8000/documentos/1"
```

### 4. Download de Arquivo (`GET /documentos/{id}/download`)
```bash
curl -O -J "http://127.0.0.1:8000/documentos/1/download"
```

### 5. Atualização de Metadados (`PUT /documentos/{id}`)
```bash
curl -X PUT "http://127.0.0.1:8000/documentos/1" \
  -H "Content-Type: application/json" \
  -d '{
    "descricao": "Descrição revisada",
    "semestre": "2026.2"
  }'
```

### 6. Verificação de Integridade Individual (`GET /documentos/{id}/integridade`)
```bash
curl -X GET "http://127.0.0.1:8000/documentos/1/integridade"
```

### 7. Verificação de Integridade Global (`GET /integridade`)
```bash
curl -X GET "http://127.0.0.1:8000/integridade"
```

### 8. Exportação XML (`GET /documentos/exportar/xml`)
```bash
curl -o exportacao.xml "http://127.0.0.1:8000/documentos/exportar/xml?aluno=Lucas&semestre=2026.1"
```

### 9. Exportação CSV (`GET /exportar/csv`)
```bash
curl -o catalogo.csv "http://127.0.0.1:8000/exportar/csv"
```

### 10. Criação de Backup (`POST /backup`)
```bash
# Backup geral
curl -X POST "http://127.0.0.1:8000/backup"

# Backup filtrado por curso
curl -X POST "http://127.0.0.1:8000/backup?curso=Engenharia"
```

### 11. Exclusão de Documento (`DELETE /documentos/{id}`)
```bash
curl -X DELETE "http://127.0.0.1:8000/documentos/1"
```

---

## Funcionalidades Específicas

### Exportação XML (F16)
O endpoint `GET /documentos/exportar/xml` permite filtrar documentos em memória pelos parâmetros `aluno` e/ou `semestre`. A resposta é formatada hierarquicamente em XML com indentação, header `Content-Disposition: attachment; filename="documentos.xml"` e `Content-Type: application/xml`.

### Integridade Criptográfica SHA-256 (F9 e F10)
* No momento do upload, o hash SHA-256 do arquivo físico é calculado e gravado nos metadados;
* O endpoint individual `GET /documentos/{id}/integridade` recalcula o hash do arquivo em disco e compara com o valor original, retornando o status `INTEGRO`, `ALTERADO` ou `AUSENTE`;
* O endpoint global `GET /integridade` executa a checagem em lote em todos os documentos cadastrados.

### Backup e Restauração (F14 e F15)
* O endpoint `POST /backup` gera um arquivo ZIP em `storage/backups/` contendo os arquivos físicos selecionados, o arquivo `documentos.json`, `config.yaml` e o histórico de logs `sistema.log`;
* Suporta filtros por `categoria`, `curso`, `semestre`, `ano`, `tipo_documento` e `aluno`;
* Os backups gerados podem ser listados em `GET /backups` e baixados via `GET /backups/{nome}`.

### Exportação CSV (F13)
O endpoint `GET /exportar/csv` gera um arquivo CSV contendo todos os campos de metadados do acervo, gravando uma cópia em `storage/exports/catalogo_YYYYMMDD_HHMMSS.csv` e transmitindo o conteúdo como anexo com tipo MIME `text/csv`.

### Sistema de Logs (F11)
Todos os eventos operacionais são registrados em `storage/logs/sistema.log` e no terminal nos níveis `INFO`, `WARNING` e `ERROR`:
* **Inicialização:** Registro do startup da aplicação (`INFO`);
* **Uploads:** Inclusão de novos arquivos e metadados (`INFO`);
* **Downloads:** Download de documentos físicos e backups (`INFO`);
* **Consultas:** Listagens e buscas executadas (`INFO`);
* **Alterações e Exclusões:** Atualizações de metadados e remoções (`INFO`);
* **Falhas de Integridade:** Divergência de hash (`WARNING`) ou arquivo não encontrado (`ERROR`);
* **Tentativas de Acesso a Recursos Inexistentes:** Requisição de documentos ou backups não localizados (`WARNING`).
