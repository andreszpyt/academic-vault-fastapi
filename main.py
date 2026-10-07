from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.routers import documentos, integridade, exportacoes, backup, estatisticas
from app.logger import logger

app = FastAPI(
    title="Cofre de Documentos Acadêmicos",
    description="API para armazenamento e gerenciamento de documentos acadêmicos.",
    version="1.0.0",
)

app.include_router(documentos.router)
app.include_router(integridade.router)
app.include_router(exportacoes.router)
app.include_router(backup.router)
app.include_router(estatisticas.router)

logger.info("INICIALIZACAO sistema iniciado")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"ERRO_INESPERADO rota={request.url.path} erro={exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Erro interno do servidor: {exc}"},
    )


@app.get("/")
def root():
    logger.info("ACESSO: Usuario acessou a rota raiz do sistema")
    return {
        "sistema": "Cofre de Documentos Acadêmicos",
        "versao": "1.0.0",
        "docs": "/docs",
    }