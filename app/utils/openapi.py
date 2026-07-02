from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def patch_openapi(app: FastAPI):
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
        
        def fix_media_types(d):
            if isinstance(d, dict):
                if d.get("contentMediaType") == "application/octet-stream":
                    del d["contentMediaType"]
                    d["format"] = "binary"
                for v in d.values():
                    fix_media_types(v)
            elif isinstance(d, list):
                for v in d:
                    fix_media_types(v)

        fix_media_types(schema)
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi