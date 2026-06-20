from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.api.v1.router import api_router

from app.core.config import settings
from app.core.http import attach_openapi_auth, register_http_stack
from app.core.logging import setup_logging
from app.infrastructure.db.db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "API event-driven para regras, atividades, testes e avaliação assistida por modelo.\n\n"
        "O serviço combina liberação gradual determinística com avaliação por machine learning, "
        "usando fallback seguro quando a pontuação do modelo não está disponível.\n\n"
        "### Fluxos principais\n"
        "- Catálogo de atividades: criar, listar, atualizar e remover via `/activities`\n"
        "- Regras: criar, listar, atualizar e remover via `/features`\n"
        "- Atividades: registro individual via `/events` e ingestão em lote via `/ingest/events`\n"
        "- Treinamento do modelo: execução síncrona via `/train`\n"
        "- Avaliação: decisão por usuário via `/evaluate`\n"
        "- Testes: configuração e resultado via `/experiments`\n"
        "- Situação do modelo: estado atual via `/model/status` e histórico via `/model/runs`\n"
        "- Métricas operacionais: snapshot em memória via `/metrics`\n\n"
        "### Princípios de design\n"
        "- Comportamento previsível com liberação gradual determinística\n"
        "- Inteligência progressiva com machine learning quando pronto\n"
        "- Resiliência com fallback antes da decisão final\n"
        "- Experimentação incremental com distribuição determinística A/B"
    ),
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
    openapi_url="/openapi.json" if settings.enable_docs else None,
    lifespan=lifespan,
)

setup_logging()
register_http_stack(app, settings)
attach_openapi_auth(app)

app.include_router(api_router)

ui_dir = Path(__file__).resolve().parent.parent / "ui"

@app.get("/", tags=["UI"], summary="Abrir interface web", description="Serve a interface web principal do produto.")
def root():
    index_file = ui_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file, headers={"Cache-Control": "no-store"})
    return {"message": settings.app_name}


@app.get("/health", tags=["Saúde"], summary="Verificar saúde", description="Verifica se a API está respondendo.")
def healthcheck():
    return {"status": "ok"}


if ui_dir.exists():
    app.mount("/", StaticFiles(directory=ui_dir, html=True), name="ui")
