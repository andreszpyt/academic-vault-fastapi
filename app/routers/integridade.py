from fastapi import APIRouter

from app import storage
from app.models import IntegridadeGlobal
from app.logger import logger

router = APIRouter(tags=["Integridade"])


@router.get("/integridade", response_model=IntegridadeGlobal)
@router.get("/integridade/", response_model=IntegridadeGlobal, include_in_schema=False)
def verificar_integridade_global():
    resultado = storage.verificar_integridade_global()
    return resultado
