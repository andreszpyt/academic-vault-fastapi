from fastapi import APIRouter

from app import storage
from app.models import IntegridadeGlobal
from app.logger import logger

router = APIRouter(tags=["Integridade"])


# F10 — Verificação Global de Integridade
@router.get("/integridade", response_model=IntegridadeGlobal)
def verificar_integridade_global():
    resultado = storage.verificar_integridade_global()
    return resultado
