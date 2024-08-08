import logging
from contextlib import asynccontextmanager

from authlib.integrations.starlette_client import OAuth
from jose import jwt

from javazone.core.config import settings

SUPPORTED_ALGS_KEY = "id_token_signing_alg_values_supported"
GOOGLE_WELL_KNOWN = "https://accounts.google.com/.well-known/openid-configuration"
LOG = logging.getLogger(__name__)

oauth = OAuth()


@asynccontextmanager
async def init_jwt(app):
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
    jwk_set = await client.fetch_jwk_set()
    LOG.debug("Decoding a token, using these supported algorithms: %r", metadata[SUPPORTED_ALGS_KEY])
    return jwt.decode(
        token,
        jwk_set,
        algorithms=metadata[SUPPORTED_ALGS_KEY][0],
        audience=settings.oauth.client_id,
        options={
            "verify_at_hash": False,
        },
    )
