from fastapi import APIRouter
import json
import os

router = APIRouter(
    prefix="/estatisticas",
    tags=["Estatísticas"]
)

@router.get("/")
def resumo_sistema():
    caminho_arquivo = "storage/metadata/documentos.json"
    
    
    if not os.path.exists(caminho_arquivo):
        return {"total_documentos": 0, "mensagem": "Nenhum documento guardado ainda."}
        
    try:
        
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            documentos = json.load(f)
            
        return {
            "total_documentos": len(documentos),
            "status": "sucesso"
        }
    except Exception as e:
        return {"erro": f"Falha ao ler estatísticas: {str(e)}"}