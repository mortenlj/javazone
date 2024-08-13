import logging
from contextlib import asynccontextmanager

from authlib.integrations.starlette_client import OAuth
from authlib.jose import JsonWebToken

from javazone.core.config import settings

SUPPORTED_ALGS_KEY = "id_token_signing_alg_values_supported"
GOOGLE_WELL_KNOWN = "https://accounts.google.com/.well-known/openid-configuration"
LOG = logging.getLogger(__name__)

oauth = OAuth()


@asynccontextmanager
async def init_jwt(app):
    if settings.debug:
        LOG.warning("Running in debug mode, using dummy login")
        yield
        return
    oauth.register(
        "google",
        client_id=settings.oauth.client_id,
        client_secret=settings.oauth.client_secret.get_secret_value(),
        server_metadata_url=GOOGLE_WELL_KNOWN,
    )
    yield


async def decode_token(token):
    client = oauth.create_client("google")
    metadata = await client.load_server_metadata()
    jwt = JsonWebToken(metadata[SUPPORTED_ALGS_KEY])
    jwk_set = await client.fetch_jwk_set()
    LOG.debug("Decoding a token, using these supported algorithms: %r", metadata[SUPPORTED_ALGS_KEY])
    return jwt.decode(
        token,
        jwk_set,
    )
