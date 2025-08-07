from . import api, probes

def include_routers(app):
    app.include_router(api.router, prefix="/api")
    app.include_router(probes.router, prefix="/_")
