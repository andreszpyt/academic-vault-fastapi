import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def carregar_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Arquivo de configuração não encontrado: {CONFIG_PATH}"
        )
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = carregar_config()

DIR_DOCUMENTOS = Path(config["storage"]["diretorio_documentos"])
DIR_METADATA   = Path(config["storage"]["diretorio_metadata"])
DIR_BACKUPS    = Path(config["storage"]["diretorio_backups"])
DIR_EXPORTS    = Path(config["storage"]["diretorio_exports"])
LOG_ARQUIVO    = Path(config["logging"]["arquivo"])

LOG_NIVEL      = config["logging"]["nivel"]
UPLOAD_MAX_MB  = config["upload"]["tamanho_maximo_mb"]
HASH_ALGORITMO = config["hash"]["algoritmo"]
BACKUP_FORMATO = config["backup"]["formato"]

for _dir in [DIR_DOCUMENTOS, DIR_METADATA, DIR_BACKUPS, DIR_EXPORTS, LOG_ARQUIVO.parent]:
    _dir.mkdir(parents=True, exist_ok=True)

METADATA_FILE = DIR_METADATA / "documentos.json"