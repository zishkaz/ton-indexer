import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, status, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.exceptions import HTTPException as StarletteHTTPException

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

from indexer.api.api_v1.main import router as router_v1
# from indexer.api.api_old.main import router as router_old
# from indexer.api.api_wordy.main import router as router_wordy

from indexer.core import exceptions
from indexer.core.settings import Settings
from indexer.api.deps.apikey import api_key_dep


logging.basicConfig(format='%(asctime)s %(module)-15s %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


settings = Settings()

@asynccontextmanager
async def lifespan_func(app: FastAPI):
    if settings.cache_endpoint:
        redis = aioredis.from_url(settings.cache_endpoint)
        FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    logger.info('Setup complete')
    yield
    logger.info('Cleanup complete')


description = 'TON Index collects data from a full node to PostgreSQL database and provides convenient API to an indexed blockchain.'
app = FastAPI(title="TON Index" if not settings.api_title else settings.api_title,
              description=description,
              version='1.0.0',
              docs_url=None,
              redoc_url=None,
              lifespan=lifespan_func,
              openapi_url=settings.api_root_path + '/openapi.json',
              dependencies=[Depends(api_key_dep)])


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse({'error' : str(exc.detail)}, status_code=exc.status_code)


@app.exception_handler(exceptions.DataNotFound)
async def tonlib_wront_result_exception_handler(request, exc):
    return JSONResponse({'error' : str(exc)}, status_code=status.HTTP_404_NOT_FOUND)


@app.exception_handler(exceptions.MultipleDataFound)
async def tonlib_multiple_result_exception_handler(request, exc):
    return JSONResponse({'error' : str(exc)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse({'error' : str(exc)}, status_code=status.HTTP_400_BAD_REQUEST)


@app.exception_handler(Exception)
def generic_exception_handler(request, exc):
    return JSONResponse({'error' : str(exc)}, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


app.include_router(router_v1, prefix=settings.api_root_path, include_in_schema=True, deprecated=False)
# app.include_router(router_old, prefix='/old', include_in_schema=False, deprecated=False, tags=['old'])
# app.include_router(router_wordy, prefix='/wordy', include_in_schema=False, deprecated=False, tags=['wordy'])

app.mount(settings.api_root_path + "/static", StaticFiles(directory="indexer/api/static"), name="static")

@app.get(settings.api_root_path + "/", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url=settings.api_root_path + "/static/swagger-ui-bundle.js",
        swagger_css_url=settings.api_root_path+ "/static/swagger-ui.css",
        swagger_favicon_url=''
    )
