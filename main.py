from fastapi import FastAPI
from app.routers import documentos, integridade, exportacoes, backup
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

logger.info("INICIALIZACAO sistema iniciado")


@app.get("/")
def root():
    return {
        "sistema": "Cofre de Documentos Acadêmicos",
        "versao": "1.0.0",
        "docs": "/docs",
    }