import logging

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from indexer.api.index.api import app as index_app
from indexer.core.settings import Settings
from indexer.core import crud


logging.basicConfig(format='%(asctime)s %(module)-15s %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

settings = Settings()

description = ''
app = FastAPI()

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse({'error' : str(exc.detail)}, status_code=exc.status_code)

@app.exception_handler(crud.DataNotFound)
async def tonlib_wront_result_exception_handler(request, exc):
    return JSONResponse({'error' : str(exc)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@app.exception_handler(Exception)
def generic_exception_handler(request, exc):
    return JSONResponse({'error' : str(exc)}, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

@app.on_event("startup")
def startup():
    logger.info('Service started successfully')

app.mount('/api/index', index_app)
