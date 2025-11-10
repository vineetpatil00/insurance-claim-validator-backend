from fastapi.openapi.utils import get_openapi
from app.config.ProtectedRoutes import enabled_routes

def generate_swagger(app):
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Add x-api-key header for specific routes
        for route in enabled_routes:
            path = route["path"]
            if path in openapi_schema["paths"]:
                for method in openapi_schema["paths"][path].values():
                    method.setdefault("parameters", []).append(
                        {
                            "name": "x-api-key",
                            "in": "header",
                            "required": True,
                            "description": "API key for authentication",
                            "schema": {"type": "string"},
                        }
                    )

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    return custom_openapi
