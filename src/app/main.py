from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schema import (
    BadRequestResponse,
    DebugRequest,
    DebugResponse,
    ServiceExceptionResponse,
    TestsRequest,
    TestsResponse,
    format_validation_errors,
)
from app.service.exceptions import ServiceException
from app.service.main import PrologDService

APP_DIR = Path(__file__).parent
TEMPLATES_DIR = APP_DIR / 'templates'
STATIC_DIR = APP_DIR / 'static'

API_RESPONSES = {
    400: {'model': BadRequestResponse, 'description': 'Ошибка валидации. Тело запроса не соответствует спецификации.'},
    500: {'model': ServiceExceptionResponse, 'description': 'Внутренняя ошибка сервиса.'},
}


def create_app() -> FastAPI:
    app = FastAPI(
        title='Prolog-D Sandbox API',
        description='API для выполнения кода на Пролог-Д через HTTP.',
        version='0.1.0',
        docs_url='/docs',
        redoc_url='/redoc',
        openapi_url='/openapi.json',
    )
    templates = Jinja2Templates(directory=TEMPLATES_DIR)
    if STATIC_DIR.is_dir():
        app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        return JSONResponse(
            status_code=400,
            content=BadRequestResponse(
                details=format_validation_errors(exc.errors()),
            ).model_dump(),
        )

    @app.exception_handler(ServiceException)
    async def service_exception_handler(
        request: Request,
        exc: ServiceException,
    ):
        return JSONResponse(
            status_code=500,
            content=ServiceExceptionResponse(
                error=exc.message,
                details=exc.details,
            ).model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ):
        if exc.status_code == 400 and isinstance(exc.detail, list):
            return JSONResponse(
                status_code=400,
                content=BadRequestResponse(
                    details=format_validation_errors(exc.detail),
                ).model_dump(),
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={'error': str(exc.detail)},
        )

    @app.get('/', response_class=HTMLResponse, include_in_schema=False)
    async def index(request: Request):
        return templates.TemplateResponse(request, 'index.html')

    @app.post(
        '/debug/',
        response_model=DebugResponse,
        tags=['debug'],
        summary='Выполнение программы',
        description='Выполняет программу на Пролог-Д и возвращает результат её работы.',
        responses=API_RESPONSES,
    )
    def debug(data: DebugRequest):
        result = PrologDService.debug(data.to_entity())
        return DebugResponse.from_entity(result)

    @app.post(
        '/testing/',
        response_model=TestsResponse,
        tags=['testing'],
        summary='Прогон программы на тестах',
        description='Выполняет программу на наборе тестов с checker-функцией.',
        responses=API_RESPONSES,
    )
    def testing(data: TestsRequest):
        result = PrologDService.testing(data.to_entity())
        return TestsResponse.from_entity(result)

    return app


app = create_app()
