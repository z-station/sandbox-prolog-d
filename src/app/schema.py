from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.entities import DebugData, TestData, TestsData
from app.utils import clean_str


EXAMPLE_CODE = (
    'факториал(0,1):-!.\n'
    'факториал(Н,Ф):-факториал(#Н-1#,Ю),УМНОЖЕНИЕ(Ю,Н,Ф).\n'
    '?факториал(5,Р).'
)


class DebugRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            'examples': [
                {
                    'code': EXAMPLE_CODE,
                    'data_in': None,
                },
            ],
        },
    )

    data_in: Optional[str] = Field(
        default=None,
        description='Консольный ввод программы (необязательный, может быть null).',
    )
    code: str = Field(description='Код программы на Пролог-Д.')

    @field_validator('data_in', 'code', mode='before')
    @classmethod
    def clean_input(cls, value: Any) -> Any:
        return clean_str(value)

    def to_entity(self) -> DebugData:
        return DebugData(code=self.code, data_in=self.data_in)


class DebugResponse(BaseModel):
    result: Optional[str] = Field(
        default=None,
        description='Результат работы программы (null, если значения нет).',
    )
    error: Optional[str] = Field(
        default=None,
        description='Ошибки выполнения программы (null, если значения нет).',
    )

    @classmethod
    def from_entity(cls, data: DebugData) -> 'DebugResponse':
        return cls(result=data.result, error=data.error)


class TestRequest(BaseModel):
    data_in: Optional[str] = Field(
        default=None,
        description='Консольный ввод для тестируемой программы.',
    )
    data_out: str = Field(description='Правильный ответ теста.')

    @field_validator('data_in', 'data_out', mode='before')
    @classmethod
    def clean_input(cls, value: Any) -> Any:
        return clean_str(value)

    def to_entity(self) -> TestData:
        return TestData(data_in=self.data_in, data_out=self.data_out)


class TestResponse(BaseModel):
    result: Optional[str] = Field(
        default=None,
        description='Результат работы программы (null, если значения нет).',
    )
    error: Optional[str] = Field(
        default=None,
        description='Ошибка выполнения программы (null, если значения нет).',
    )
    ok: Optional[bool] = Field(
        default=None,
        description='Успешно ли завершён тест.',
    )

    @classmethod
    def from_entity(cls, data: TestData) -> 'TestResponse':
        return cls(result=data.result, error=data.error, ok=data.ok)


class TestsRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            'examples': [
                {
                    'code': EXAMPLE_CODE,
                    'checker': (
                        'def checker(right_value: str, value: str) -> bool:\n'
                        '    return right_value == value'
                    ),
                    'tests': [
                        {'data_in': None, 'data_out': 'Р=120'},
                    ],
                },
            ],
        },
    )

    tests: list[TestRequest] = Field(description='Набор тестов для проверки программы.')
    checker: str = Field(description='Python-функция, проверяющая успешность очередного теста.')
    code: str = Field(description='Код программы на Пролог-Д.')

    @field_validator('checker', 'code', mode='before')
    @classmethod
    def clean_input(cls, value: Any) -> Any:
        return clean_str(value)

    def to_entity(self) -> TestsData:
        return TestsData(
            code=self.code,
            checker=self.checker,
            tests=[test.to_entity() for test in self.tests],
        )


class TestsResponse(BaseModel):
    num: int = Field(description='Количество тестов.')
    num_ok: int = Field(description='Количество успешно пройденных тестов.')
    ok: bool = Field(description='Успешно ли завершено тестирование.')
    tests: list[TestResponse] = Field(description='Результаты каждого теста.')

    @classmethod
    def from_entity(cls, data: TestsData) -> 'TestsResponse':
        num = len(data.tests)
        num_ok = sum(1 for test in data.tests if test.ok)
        return cls(
            num=num,
            num_ok=num_ok,
            ok=num == num_ok,
            tests=[TestResponse.from_entity(test) for test in data.tests],
        )


VALIDATION_ERROR = 'Validation error'


class BadRequestResponse(BaseModel):
    error: str = Field(default=VALIDATION_ERROR, description='Текст ошибки.')
    details: dict[str, list[str]] = Field(description='Детали ошибки валидации по полям.')


class ServiceExceptionResponse(BaseModel):
    error: Optional[str] = Field(default=None, description='Текст ошибки.')
    details: Any = Field(default=None, description='Дополнительные детали ошибки.')


PYDANTIC_ERROR_MESSAGES = {
    'missing': 'Missing data for required field.',
}


def format_validation_errors(errors: list[dict[str, Any]]) -> dict[str, list[str]]:

    """ Преобразует ошибки валидации Pydantic в формат ответа API:
    {"error": "Validation error", "details": {"<поле>": ["<сообщение>", ...]}}

    Args:
        errors: Список ошибок из ``RequestValidationError.errors()``.

    """
    details: dict[str, list[str]] = {}
    for error in errors:
        loc = [str(part) for part in error['loc'] if part not in ('body', 'query', 'path')]
        field = loc[-1] if loc else 'body'
        message = PYDANTIC_ERROR_MESSAGES.get(error['type'], error['msg'])
        details.setdefault(field, []).append(message)
    return details
