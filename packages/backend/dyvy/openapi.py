from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute

from dyvy.conf import settings


def configure_openapi(app: FastAPI):
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Dyvy.AI",
        version=settings.VERSION,
        summary="Dyvy.AI OpenAPI schema",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    if settings.ENV == "prod":
        app.openapi_url = ""
        app.redoc_url = ""

    return app.openapi_schema


def generate_unique_id_function(route: APIRoute) -> str:
    return f"{route.tags[0]}:{route.name}" if len(route.tags) else str(route.name)
