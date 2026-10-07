from fastapi import APIRouter

from app import storage
from app.models import Estatisticas
from app.logger import logger

router = APIRouter(
    prefix="/estatisticas",
    tags=["Estatísticas"]
)


@router.get("", response_model=Estatisticas)
@router.get("/", response_model=Estatisticas, include_in_schema=False)
def obter_estatisticas_sistema():
    stats = storage.obter_estatisticas()
    logger.info(f"ESTATISTICAS_SISTEMA total_documentos={stats['total_documentos']}")
    return stats
