from fastapi import FastAPI, status, HTTPException

from app.routers.clientes import router as clientes_router
from app.routers.unidades import router as unidades_router
from app.routers.produtos import router as produtos_router
from app.routers.pedidos import router as pedidos_router
from app.routers.item_pedido import router as item_pedido_router
from app.routers.estoque import router as estoque_router
from app.routers.pagamentos import router as pagamentos_router
from app.routers.fidelidades import router as fidelidades_router
from app.routers.movimentacao_pontos import router as movimentacao_pontos_router
from app.routers.funcionarios import router as funcionarios_router
from app.routers.auditorias import router as auditorias_router
from app.routers.alteracoes_funcao import router as alteracoes_funcao_router
from app.routers.auth import router as auth_router
from app.routers.usuarios import router as usuarios_router

app = FastAPI(
    title="Raizes do Nordeste - Backend",
    description="API do Sistema de Pedidos da Rede Raizes do Nordeste",
    version="1.0.0"
)

@app.get("/")
def root():
    return {
        "mensagem": "API Raizes do Nordeste funcionando!"
    }

app.include_router(clientes_router)
app.include_router(unidades_router)
app.include_router(produtos_router)
app.include_router(pedidos_router)
app.include_router(item_pedido_router)
app.include_router(estoque_router)
app.include_router(pagamentos_router)
app.include_router(fidelidades_router)
app.include_router(movimentacao_pontos_router)
app.include_router(funcionarios_router)
app.include_router(auditorias_router)
app.include_router(alteracoes_funcao_router)
app.include_router(auth_router)
app.include_router(usuarios_router)
