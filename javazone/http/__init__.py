from . import api, probes, www


def include_routers(app):
    app.include_router(api.router, prefix="/api")
    app.include_router(probes.router, prefix="/_")
    app.include_router(www.router)
