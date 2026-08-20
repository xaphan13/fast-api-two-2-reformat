# 02. Архитектура и паттерны

> Опорные факты собраны чтением исходников и графа знаний (`codebase-memory-mcp`, generation `2026-08-20T11:37:31Z`).
> Все пути — относительно корня репозитория.

---

## 1. Высокоуровневая архитектура

Проект — **не микросервисы и не единый монолит, а два независимых монолита в одном репозитории, объединённых общей инфраструктурой**. Правильная формулировка: *shared-infrastructure multi-app monorepo*.

```
                          ┌──────────────── Внешний мир (HTTPS) ────────────────┐
                          │                                                     │
                    ┌─────▼──────────────────────────────────────────────┐
                    │  nginx  172.20.0.8  :443                           │
                    │  location /app11/ → 172.20.0.11:8000               │
                    │  location /app22/ → 172.20.0.22:9000               │
                    │  location /pgadmin, /flower_first                  │
                    └─────┬───────────────────────────┬──────────────────┘
                          │                           │
              ┌───────────▼──────────┐     ┌──────────▼───────────┐
              │  app11 (SYNC)        │     │  app22 (ASYNC)       │
              │  uvicorn :8000       │     │  uvicorn :9000       │
              │  root_path=/app11    │     │  root_path=/app22    │
              │                      │     │                      │
              │  psycopg2 (блокир.)  │     │  aiosqlite / asyncpg  │
              │  sessionmaker        │     │  async_sessionmaker   │
              │  CRUDBase            │     │  AsyncBaseCRUD        │
              └──┬────────────┬──────┘     └──────────┬───────────┘
                 │            │                       │
                 │            │ .delay()              │
                 │            ▼                       │
                 │   ┌──────────────────┐             │
                 │   │ Redis 172.20.0.4 │             │
                 │   │ брокер + backend │             │
                 │   └────────┬─────────┘             │
                 │            ▼                       │
                 │   ┌──────────────────┐             │
                 │   │ celery_worker    │             │
                 │   │ 172.20.0.31      │             │
                 │   └────────┬─────────┘             │
                 │            │                       │
                 ▼            ▼                       ▼
        ┌────────────────────────────┐   ┌────────────────────────┐
        │ PostgreSQL 172.20.0.2:5432 │   │ SQLite (файл в томе)   │
        │   (8 таблиц app11)         │   │  app22/test_fast_api.db│
        └────────────────────────────┘   │   (15 таблиц app22)    │
                                          └────────────────────────┘
```

Ключевые свойства связности:

- **Между `app11` и `app22` нет ни одного вызова.** Они не знают друг о друге: ни HTTP-запросов, ни общей очереди, ни общих таблиц. Единственное, что их связывает, — nginx как общая точка входа и (по замыслу) один экземпляр PostgreSQL. Граф подтверждает: пакеты `app11.*` и `app22.*` не имеют взаимных рёбер `CALLS`/`IMPORTS`.
- **Celery принадлежит только `app11`.** `CELERY_BROKER_URL` и `CELERY_RESULT_BACKEND` читаются исключительно в `app11/core/config.py`. В `app22` асинхронность решается через `async`/`await` внутри процесса, а не выносом в воркер.
- **Дублирование инфраструктурного кода вместо общего пакета.** `base_dir_path.py`, `config_log.py`, `core/config.py`, `core/__init__.py`, `db_core/base.py` существуют в двух почти идентичных копиях. Общего пакета уровня репозитория нет — это осознанная цена изоляции двух примеров.

### 1.1. Слои внутри приложения

Каждое приложение — классическая четырёхслойная схема, но границы соблюдаются неравномерно.

| Слой | `app11` | `app22` | Строгость |
|---|---|---|---|
| **Точка входа** | `app11/main.py` | `app22/main.py` | Только сборка `app` + `include_router` |
| **Транспорт** | `example_*/router_*.py`, `run_task/router_*.py` | `async_*/router_*.py`, `http_request_routers/` | Роутеры часто содержат SQL напрямую |
| **Доступ к данным** | `example_many_db/crud_base.py`, `crud_many.py` | `db_core/async_crud_base.py`, `async_crud_*.py` | Обходится в половине роутеров |
| **Модели** | `example_*/model_*.py`, `run_task/model_task.py` | `async_*/model_*.py` | Соблюдается |
| **Инфраструктура** | `db_core/db_conf.py`, `config_log.py` | `db_core/db_async.py`, `config_log.py` | Соблюдается |

**Слой CRUD не является обязательным.** Это главная архитектурная особенность: в `app22/async_many_sql/` один и тот же домен реализован дважды — `router_many_async_*.py` пишет SQL прямо в обработчике, `router_many_aCrud_*.py` работает через `AsyncBaseCRUD`. Оба варианта подключены в `main.py` одновременно. Это сделано намеренно как сравнительная демонстрация, но означает, что «слой» здесь — рекомендация, а не инвариант.

---

## 2. Паттерны проектирования

### 2.1. Generic Repository — центральный паттерн проекта

Реализован трижды, в трёх поколениях:

| Класс | Файл | Стиль SQLAlchemy | Pydantic API |
|---|---|---|---|
| `AsyncBaseCRUD` | `app22/db_core/async_crud_base.py` | 2.0 (`select()`, `await db.execute()`) | v2 (`model_dump()`) |
| `CRUDBase` | `app11/example_many_db/crud_base.py` | legacy (`db.query()`) | v1 (`.dict()`) |
| `NewCRUDBase` | `app22/not_async_examples/not_async_crud_base.py` | legacy (`db.query()`) | v1 (`.dict()`) |

Все три параметризованы **пятью** `TypeVar` — по одному на операцию, а не одним «схема сущности»:

```python
class AsyncBaseCRUD(Generic[SqlType, CreateType, ReaderType, UpdateType, DeleteType]):
    def __init__(self, model: Type[SqlType]):
        self.model: Type[SqlType] = model
```

Конкретизация — через наследование с явной подстановкой типов и создание синглтона рядом с классом:

```python
# app22/async_many_sql/async_crud_order.py
class AsyncOrderCRUD(AsyncBaseCRUD[Order, OrderCreateBody, OrderGetQuery, OrderUpdateBody, OrderGetQuery]): ...
order_async = AsyncOrderCRUD(Order)
```

Наследников `AsyncBaseCRUD` — 11 (граф: 47 рёбер `INHERITS`). Большинство добавляет только `get_model()`; содержательные расширения — `UserAsyncCRUD.get_user_posts_one`, `PostAsyncCRUD.add_post_user`, `BookAsyncCRUD.add_book_to_list`, `ReaderAsyncCRUD.get_reader_bookL_one`.

**Приём расширения без переопределения.** Базовые методы принимают необязательный параметр `query_n: Executable | None`; если он передан, готовый запрос используется вместо построенного по умолчанию. Наследник собирает свой `select(...)` с `selectinload(...)` и передаёт его в базовый метод:

```python
query = select(self.model).where(...).options(selectinload(self.model.posts))
return await self.get_record_one(schema, db, query_n=query)
```

Это делает базовый класс расширяемым без наследования логики выполнения — единственная точка `await db.execute()` остаётся в базе. Во всём графе только **одно** ребро `OVERRIDE` (`AsyncOrderCRUD.delete_record_many`), что подтверждает: приём работает.

### 2.2. Динамическое построение фильтров из Pydantic-схемы

Связующее звено между HTTP-слоем и SQL. Схема запроса превращается в список условий SQLAlchemy:

```python
def _get_filter_attr(self, schema_filter_attr):
    schema_dump = schema_filter_attr.model_dump(exclude_none=True).items()
    filter_attr = [getattr(self.model, k) == v for k, v in schema_dump]
    return filter_attr
```

`exclude_none=True` даёт эффект «частичного фильтра»: незаполненные поля запроса просто не попадают в `WHERE`. Дальше — `select(self.model).where(*filter_attr)`.

Цена приёма — **потеря типовой безопасности**: `getattr(self.model, k)` падает с `AttributeError`, если имя поля схемы не совпадает с именем колонки модели. Это не теоретический риск, а реально присутствующий дефект (см. §6).

Синхронный аналог использует другой механизм — распаковку в `filter_by`:

```python
query_dict = {key: value for key, value in query.dict().items() if value is not None}
read = db.query(self.model).filter_by(**query_dict).first()
```

### 2.3. Dependency Injection

Единственный механизм — штатный `Depends` FastAPI. Контейнера IoC нет.

| Зависимость | Провайдер | Использование |
|---|---|---|
| Асинхронная сессия | `AsyncSessionDB.get_db()` — `AsyncGenerator` с `try/finally: await session.close()` | `db: AsyncSession = Depends(async_db.get_db)` |
| Сессия, привязанная к задаче | `AsyncSessionDB.scop_db()` — через `async_scoped_session(scopefunc=current_task)` | Объявлена, в роутерах не применяется |
| Синхронная сессия | `SessionDB.get_db()` — `@staticmethod`-генератор | `db: Session = Depends(SessionDB.get_db)` |
| Синхронная сессия в `app22` | `SessionDB_not_async.get_db_not_async()` | `app22/not_async_examples/` |
| Экземпляр Celery | `depends_celery() -> Celery` | `celery: Celery = Depends(depends_celery)` |
| Группировка query-параметров | Pydantic-модель как `Depends()` без аргументов | `params: OrderGetQuery = Depends()` |

Последний приём стоит отметить: `params: OrderGetQuery = Depends()` заставляет FastAPI собрать модель из **query-параметров**, а не из тела запроса. Это способ типизировать группу параметров GET-запроса одной схемой.

### 2.4. Singleton и Factory

Оба приложения строят `FastAPI` через модуль-синглтон:

```python
# app22/core/__init__.py
app_fastapi = FastAPI(root_path=OPEN_API_PREFIX)

def get_app_fastapi():
    """получение экземпляра FastAPI"""
    return app_fastapi
```

Экземпляр создаётся при импорте модуля, фабрика лишь возвращает готовый объект. Это **не** фабрика в смысле создания по запросу — переиспользуется единственный объект уровня модуля. Тот же приём применён к `async_db = AsyncSessionDB(...)`, `celery = Celery(...)` и ко всем CRUD-объектам (`order_async`, `userDB`, `readerDB`, …). Следствие: состояние инициализируется на этапе импорта, побочные эффекты неизбежны (см. `03_execution_flow.md`).

### 2.5. Кастомный класс маршрута — перехват ошибок на уровне транспорта

`app11/example_many_db/except_many_db.py` и `app11/example_db/except_ex_db.py` расширяют `APIRoute`, подменяя обработчик запроса:

```python
class MyApiRouterMany(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                return await original_route_handler(request)
            except NotSupportedError as exc:
                ...
                raise HTTPException(status_code=422, detail=detail)

        return custom_route_handler
```

Это композиция **Decorator** (обёртка вокруг исходного обработчика) и **Template Method** (переопределение хука `get_route_handler`). Подключается через `APIRouter(route_class=MyApiRouterMany)`. Альтернатива — глобальный `@app.exception_handler` — в проекте не используется; обработка ошибок остаётся локальной для роутера.

### 2.6. Result Object вместо исключений

`AsyncBaseCRUD` предлагает две стратегии добавления записи. Обычная (`add_record`) пропускает `IntegrityError` наружу. Альтернативная (`add_record_try`) конвертирует его в объект-результат:

```python
class AddResult:
    def __init__(self, model: SqlType, result: bool = True, reason: str = "OK"):
        self.result: bool = result
        self.model: SqlType = model
        self.reason: str = reason

    def str_detail(self) -> str:
        begin_D = self.reason.find("DETAIL: ")
        end_D = self.reason.find(".", begin_D)
        return self.reason[begin_D:end_D]
```

`str_detail()` вытаскивает человекочитаемую часть из текста ошибки PostgreSQL поиском подстроки `"DETAIL: "`. Приём хрупкий (зависит от формата сообщения драйвера и от локали), но избавляет вызывающий код от `try/except`.

### 2.7. Association Object и двойной путь M:N

Ключевой демонстрируемый паттерн SQLAlchemy. Связь «многие-ко-многим» с полезной нагрузкой объявлена **одновременно двумя способами**:

```python
class Order(Base):
    # путь 1: через association object — даёт доступ к count/unit_price
    products_details = relationship("OrderProductAssociation", back_populates="order",
                                    cascade="all, delete", overlaps="orders")
    # путь 2: прямой M:N — удобен, но скрывает поля ассоциации
    products = relationship("Product", secondary="order_product_association",
                            back_populates="orders", cascade="all, delete",
                            overlaps="products_details")
```

Два `relationship`, пишущих в одни и те же колонки, SQLAlchemy считает конфликтом и предупреждает; конфликт погашен параметром `overlaps=...`. Обратите внимание: использован именно `overlaps`, а не `viewonly=True` — то есть оба пути остаются записываемыми, и ответственность за непротиворечивость лежит на прикладном коде.

Таблица ассоциации несёт данные и уникальный ключ пары:

```python
__table_args__ = (UniqueConstraint("order_id", "product_id", name="idx_unique_order_product"),)
count      = Column(Integer(), default=1, server_default="1")
unit_price = Column(Integer(), default=0, server_default="0")
```

Каталог связей по проекту:

| Пара | Тип связи | Где |
|---|---|---|
| `User` → `Post` | 1:N | `app11/example_db/`, `app22/async_join_tables/model_new_ex_db.py` |
| `Admin_list` → `Admin_work` | 1:N, современный `Mapped[List[...]]` | `app22/async_join_tables/model_admin.py` |
| `Reader` → `ListBook` | 1:N | `app22/async_reader_project/model_reader_book.py` |
| `Order` ↔ `Product` | M:N через association object **и** `secondary` | `app11/example_many_db/`, `app22/async_many_sql/` |
| `ListBook` ↔ `Book` | M:N через association object (`time_add`) **и** `secondary` | `app22/async_reader_project/` |
| `Book` ↔ `Category` | чистый M:N через `secondary`, без ORM-объекта ассоциации | `app22/async_reader_project/` |
| `JoinPerson` / `JoinAddress` | **связи нет вообще** — JOIN по неключевому полю в SQL роутера | `app22/async_join_tables/model_join.py` |

Последний случай — отдельный дидактический приём: `JoinPerson.link_addr` и `JoinAddress.addr_index` соединяются условием в запросе, без `ForeignKey` и `relationship`. Демонстрируется JOIN «в обход ORM».

### 2.8. Аннотированные типы как декларативные миксины

`app22/db_core/type_for_models.py` выносит повторяющиеся определения колонок в переиспользуемые `Annotated`-типы:

```python
int_primary_key = Annotated[int, mapped_column(primary_key=True, index=True)]
str_len_100     = Annotated[str, mapped_column(String(100))]
time_stamp_utc  = Annotated[datetime, mapped_column(DateTime(timezone=True),
                            default=lambda: datetime.now(timezone.utc),
                            server_default=func.now())]
```

Применение — `created_at: Mapped[time_stamp_utc]`. Это идиома SQLAlchemy 2.0, доступная только в `app22`; модели `app11` целиком на legacy-стиле `Column(...)`. По этому признаку удобно определять «поколение» модуля.

**В проекте одновременно живут три стиля объявления моделей:** legacy `Column()` (`app11` полностью), гибрид `Column()` + `Mapped[time_stamp_utc]` (`app22/async_many_sql`, `async_join_tables/model_new_ex_db.py`), и полный 2.0 `Mapped[...]` + `mapped_column()` (`async_join_tables/model_admin.py`, `async_reader_project/*`). Это видимая шкала миграции кодовой базы.

### 2.9. Три уровня API у HTTP-клиента

`app22/http_request_routers/Class_client_https.py` (и его копия `app11/celery_tasks/Class_client_https.py`) построены на `aiohttp.ClientSession` и предлагают три уровня вызова одного и того же запроса:

| Уровень | Методы | Семантика |
|---|---|---|
| Низкий | `get_req_send`, `post_req_send` | Немедленное выполнение, новая `ClientSession` на каждый запрос |
| Задача | `get_req_create`, `post_req_create` | Возврат `asyncio.Task[RespServer]` + необязательный `add_done_callback` |
| Ожидание | `get_req_await`, `post_req_await` | Прямой `await` |

Ответ нормализуется в Pydantic-модель `RespServer` (`response`, `url`, `headers`, `body`) с методами `get_resp`, `get_url_resp`, `log_str`. Два эндпоинта `router_api_request.py` существуют именно чтобы показать разницу между «через `create_task`» и «через прямой `await`».

---

## 3. Поток данных

### 3.1. Синхронный путь чтения — `app11`

```
Клиент
  │  GET https://xaphan.ru/app11/example_many/get_order_first?id=5
  ▼
nginx :443
  │  location /app11/ → proxy_pass http://172.20.0.11:8000  (БЕЗ URI-части)
  │  → префикс /app11 НЕ срезается, uvicorn получает исходный путь
  ▼
uvicorn → FastAPI(root_path="/app11")
  │  root_path компенсирует префикс при матчинге и в openapi.json
  ▼
APIRouter(prefix=..., tags=[...], route_class=MyApiRouterMany)
  │  Depends(SessionDB.get_db) → sessionLocal() → yield Session
  │  params: OrderGetQuery = Depends()   ← сборка схемы из query-параметров
  ▼
Обработчик
  │  order_db.get_record_schema_raise(params, db)
  ▼
CRUDBase
  │  query.dict() → отбросить None → db.query(Order).filter_by(**d).first()
  │  если None → HTTPException(422)
  ▼
SQLAlchemy (psycopg2, БЛОКИРУЮЩИЙ вызов) → PostgreSQL
  │  ORM-объект Order
  ▼
Обработчик → response_model=OrderResp
  │  Pydantic валидирует и сериализует; jsonable_encoder для «сырых» dict
  ▼
finally: db.close()   ← закрытие сессии в генераторе зависимости
  ▼
JSON ответ
```

### 3.2. Асинхронный путь записи — `app22`

```
Клиент → POST /app22/new_many_aCrud_one/add_order   {promocode: "SALE"}
  ▼
nginx → uvicorn :9000 → FastAPI(root_path="/app22")
  ▼
Depends(async_db.get_db) → async_session() → yield AsyncSession
  ▼
Обработчик: await order_async.add_record(body, db)
  ▼
AsyncBaseCRUD.add_record
  │  new_record = self.model(**schema.model_dump())
  │  db.add(new_record)
  │  await db.commit()      ← возможен IntegrityError
  │  await db.refresh(new_record)
  ▼
SQLAlchemy async → aiosqlite (по факту) / asyncpg (по замыслу)
  ▼
response_model → JSON;  finally: await session.close()
```

Отличие от синхронного пути только в `await` на границе ввода-вывода: слои и их обязанности идентичны. Именно это сопоставление — цель существования двух приложений.

### 3.3. Путь через очередь задач — `app11` + Celery

```
Клиент → POST /app11/temp_route/sql_celery   {title, msg}
  ▼
FastAPI-обработчик (sql_celery, СИНХРОННЫЙ def)
  │  task = sql_task.delay(body.dict())        ─── сериализация JSON ──▶ Redis (брокер, db 0)
  │
  │  task_result = task.get()   ◀── БЛОКИРУЮЩЕЕ ОЖИДАНИЕ ──┐
  │                                                          │
  │                                          celery_worker (отдельный контейнер)
  │                                            │  sql_task(body_dict)
  │                                            │  TaskOne(**...)
  │                                            │  with SessionDB.get_session() as db:
  │                                            │      db.add / commit / refresh
  │                                            │  jsonable_encoder(new_one)
  │                                            └──▶ Redis (backend результатов) ──┘
  ▼
TaskOneQuery(**task_result) → JSON
```

**Здесь заложен архитектурный анти-паттерн.** Каждый эндпоинт `run_task/` и `temp_router_task.py` после постановки задачи немедленно вызывает `task.get()`, то есть синхронно блокируется до её завершения. Смысл очереди — развязать приём запроса и его обработку — теряется: клиент ждёт столько же, сколько ждал бы при прямом вычислении, плюс накладные расходы на два обхода Redis. В `create_task` дополнительно стоит `time.sleep(a)`, а `/task_apply` ставит задачу с `eta` на 10 секунд вперёд и тут же ждёт результат — то есть гарантированно блокирует воркер uvicorn примерно на 10 секунд.

Единственная пара эндпоинтов, реализующая очередь корректно, — `GET /send_task` (возвращает `{"task_id": ...}` сразу) и `GET /check_send_task` (опрашивает статус через `AsyncResult`). Это правильный образец для подражания.

### 3.4. Исходящий HTTP

Два стиля, по одному на приложение:

- **`app22`**: `router_api_request.py` → `await main_weather_create_task(...)` → `aiohttp` → OpenWeatherMap. Полностью в event loop.
- **`app11`**: `temp_router_task.py` → `req1_task.delay(...)` → воркер → `asyncio.run(main_weather(...))`. Обратите внимание: асинхронный клиент запускается **внутри синхронной Celery-задачи** через `asyncio.run`, то есть на каждую задачу создаётся и уничтожается отдельный event loop.

---

## 4. Управление конфигурацией

### 4.1. Механизм

Единый для обоих приложений и предельно простой: `python-dotenv` + `os.environ.get` на уровне модуля.

```python
# app22/core/config.py
load_dotenv("./app22/local.env")

LOG_DIR = os.environ.get("LOG_DIR")
DB_USER = os.environ.get("DB_USER")
...
```

`pydantic-settings` **не используется**, хотя `pydantic` v2 в зависимостях есть. Следствия:

- **Нет валидации и нет значений по умолчанию.** `os.environ.get` без второго аргумента возвращает `None`, и `None` беспрепятственно распространяется дальше. Отсутствие `local.env` приводит не к понятной ошибке конфигурации, а к `TypeError` в глубине модуля логирования (разобрано в `03_execution_flow.md`).
- **Путь к env-файлу относительный** (`"./app11/local.env"`), поэтому конфигурация читается корректно только при запуске из корня репозитория.
- **Загрузка происходит при импорте**, до создания приложения; переопределить настройки в тестах или программно невозможно.

### 4.2. Полный перечень переменных

Граф знаний фиксирует 11 узлов `EnvVar`:

| Переменная | Читает | Назначение |
|---|---|---|
| `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` | оба | Сборка строки подключения |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | только `app11` | Redis как брокер и backend |
| `LOG_DIR`, `LOG_FILE` | оба | Каталог и имя лог-файла |
| `OPEN_API_PREFIX` | оба | `FastAPI(root_path=...)` — согласование с nginx |
| `FILES_DIR` | только `app22` | Каталог для upload/download |

`SECRET_KEY` присутствует во всех четырёх шаблонах env, но **не читается ни одной строкой кода** — мёртвая настройка. Аналогично `bcrypt` объявлен в зависимостях, но хеширование паролей не реализовано: поля `password` хранятся как обычные строки (`String(100)`).

### 4.3. Четыре профиля конфигурации

Реальные env-файлы в репозиторий не попадают (`.gitignore`: `*.env`). Их роль выполняют шаблоны в `app22/template_files/`:

| Шаблон | Целевой файл | Профиль | Адресация |
|---|---|---|---|
| `local.env_temp1` | `app11/local.env` | app11, локально | IP хоста: `DB_HOST=192.168.1.80:7032`, `redis://192.168.1.80:7079/0` |
| `local.env_temp2` | `app22/local.env` **и корневой `.env`** | app22, локально + подстановки для compose | `127.0.0.1:7032`; плюс `OPEN_API_PREFIX_APP11/22`, `PATH_LOG_*`, `PGADMIN_*` |
| `dock_app1.env_temp` | `app11/dock_app1.env` | app11 в Docker | DNS контейнеров: `DB_HOST=postgresql_db_new:5432`, `redis://redis_new:6379/0` |
| `dock_app2.env_temp` | `app22/dock_app2.env` | app22 в Docker | `postgresql_db_new:5432` |

Различие «локальный / докерный» профиль сводится к способу адресации сервисов: IP хоста и опубликованные порты против DNS-имён контейнеров и внутренних портов. В докерном профиле `app11` брокер и backend разведены по разным БД Redis (`/0` и `/1`), в локальном оба указывают на `/0`.

### 4.4. Связка `root_path` ↔ nginx

Единственный по-настоящему хрупкий контракт конфигурации. Три значения обязаны совпадать, и ничто в проекте это не проверяет:

```
nginx.conf:  location /app11/ { proxy_pass http://172.20.0.11:8000; }   ← без URI-части
env:         OPEN_API_PREFIX=/app11
код:         app_fastapi = FastAPI(root_path=OPEN_API_PREFIX)
```

Механика опирается на тонкость `proxy_pass`: поскольку в директиве указан только `scheme://host:port` **без** пути, nginx передаёт бэкенду исходный URI целиком, не срезая `/app11`. Приложение обязано знать про префикс — это и делает `root_path`, который влияет на матчинг маршрутов и подставляет префикс в поле `servers` сгенерированного `openapi.json`, чтобы Swagger UI по адресу `/app11/docs` обращался к `/app11/...`, а не к корню.

Рассогласование любого из трёх значений даёт 404 на всех маршрутах либо неработающий Swagger — без явного сообщения об ошибке.

---

## 5. Состояние и кэширование

### 5.1. Кэша нет

Несмотря на присутствие Redis в каждом compose-файле, **кэширование в приложениях отсутствует полностью**. Redis используется исключительно как транспорт Celery (брокер + backend результатов). Ни `redis.get/set` в прикладном коде, ни `fastapi-cache`, ни кэша HTTP-ответов, ни мемоизации запросов к БД нет. Библиотека `redis>=7.1.0` в зависимостях нужна только как драйвер для Celery.

### 5.2. Состояние в процессе приложения

Приложения близки к stateless, но не полностью. Инвентаризация:

| Состояние | Где | Риск |
|---|---|---|
| Пул соединений SQLAlchemy | `SessionDB.engine`, `AsyncSessionDB.async_engine` | Норма; `pool_pre_ping=True` в `app11` |
| Синглтон `FastAPI` | `app*/core/__init__.py` | Норма для процесса |
| Синглтоны CRUD | `order_async`, `userDB`, `readerDB`, … | Безопасны: хранят только `Type[Model]`, не сессию |
| Флаг настройки логгера | `ConfigLogger.isSetting: bool` | Классовый атрибут-защёлка, чтобы `dictConfig` вызвался один раз |
| **`task_id: Union[None, str] = None`** | `app11/run_task/router_task.py`, уровень модуля | 🔴 Разделяемое изменяемое состояние |

Последний пункт заслуживает внимания как архитектурный дефект:

```python
task_id: Union[None, str] = None

@tasks_route.get("/send_task")
def send_task(...):
    global task_id
    if task_id is not None:
        raise HTTPException(status_code=404, detail="Task started - only one task")
    ...
    task_id = task_result.id
```

Глобальная переменная уровня модуля используется как хранилище «текущей задачи». Это работает только для одного процесса uvicorn и одного пользователя одновременно: при нескольких воркерах каждый получит собственную копию, и `check_send_task` будет обращаться к чужому или пустому состоянию. Пара `send_task`/`check_send_task` фактически реализует одноместный мьютекс на уровне модуля. Для многопроцессного развёртывания состояние следует вынести в Redis.

### 5.3. Управление сессиями БД

Три стратегии, объявленные в `AsyncSessionDB`:

```python
async def get_db(self)  -> AsyncGenerator[AsyncSession, Any]   # новая сессия на запрос
def get_session(self)   -> AsyncSession                         # сессия вне DI (для скриптов, задач)
async def scop_db(self) -> AsyncGenerator[AsyncSession, Any]    # async_scoped_session(scopefunc=current_task)
```

Настройки фабрики: `autoflush=False`, `expire_on_commit=False`. Второе особенно важно для асинхронного кода — после `commit()` объекты не инвалидируются, и обращение к их атрибутам не вызывает неожиданной подгрузки (которая в async-контексте привела бы к ошибке).

`scop_db` со `scopefunc=current_task` — заготовка под привязку сессии к задаче asyncio; **в роутерах не используется**, во всех эндпоинтах применяется `get_db`. `get_session()` востребован вне HTTP-контекста: `app11/celery_tasks/temp_task.py` использует синхронный аналог `SessionDB.get_session()` внутри Celery-задачи, где механизм `Depends` недоступен.

---

## 6. Технический долг, вытекающий из архитектуры

Перечислены только проверенные по исходникам факты, влияющие на решения при доработке.

### 6.1. Безопасность

| Проблема | Место | Комментарий |
|---|---|---|
| 🔴 **Рабочий API-ключ OpenWeatherMap в коде** | `app22/http_request_routers/client_openweathermap.py:15`, `app11/run_task/schema_task.py:38` | Один и тот же ключ как значение по умолчанию Pydantic-поля `APPID`. Закоммичен в git — присутствует в истории, ротация ключа обязательна, удаления файла недостаточно |
| 🔴 **Отключена проверка TLS-сертификатов** | `Class_client_https.py:46,64` (`app22`) и `:40,48` (`app11`) | `verify_ssl=False` во всех четырёх исходящих вызовах — открывает MITM |
| 🟡 Пароли хранятся в открытом виде | `User.password = Column(String(100))` | `bcrypt` в зависимостях есть, не применяется |
| 🟡 `SECRET_KEY` в шаблонах env | все четыре `*.env_temp*` | Одинаковое значение в шаблонах; кодом не читается |
| 🟡 Аутентификации и авторизации нет | все 117 эндпоинтов | Включая `GET /drop_all_tables` и `DELETE /delete_all_or_id` |

### 6.2. Дефекты, вытекающие из динамического построения фильтров

Цена приёма из §2.2 — ошибки, которые статический анализ не ловит, а типизация не предотвращает:

- `POST /new_many_aCrud_one/get_all_orders_new` передаёт значение enum прямо в `get_order_attr`; при значении `"time"` получается `getattr(Order, "time")` → `AttributeError`, поскольку колонка называется `created_at`. В соседнем `/get_all_orders` то же enum-значение маппится вручную — то есть в одном файле два несогласованных подхода.
- `get_having_cte` и `get_subquery_count_book` (`app22/async_reader_project/router_reader_two.py`) передают схему `SchemaListBook` в `readerDB.get_filter_attr`, тогда как фильтр строится по модели `Reader`. Работает, пока заполнено только общее поле `id`; любое заданное `list_name`/`description`/`reader_id` → `AttributeError`.

### 6.3. Дублирование и мёртвый код

| Наблюдение | Детали |
|---|---|
| `get_filter_attr` и `_get_filter_attr` | Побайтово идентичны (`async_crud_base.py`, стр. 42-45 и 47-50) — публичная и «приватная» копии одного метода |
| Две функции с одинаковым именем в модуле | `get_all_orders` в `router_many_async_one.py:105` и `:125`. Оба маршрута регистрируются (`/get_all_orders`, `/get_all_test`), но имя в пространстве модуля перезаписывается вторым определением |
| Неподключённые роутеры | `router_many_first.py`, `router_many_sec.py` (`app11`) — 10 эндпоинтов не попадают в приложение |
| Неиспользуемые методы CRUD | `get_all_rel_records`, `UserAsyncCRUD.get_users_posts_list`, `get_all_users_posts`, `ReaderAsyncCRUD.get_reader_bookL_one` |
| Ошибка инстанцирования | `association_db = ProductCRUD(OrderProductAssociation)` в `not_async_crud_many.py` — подставлен не тот класс; `OrderProductAssociationCRUD` не используется нигде |
| Инфраструктура в двух копиях | `base_dir_path.py`, `config_log.py`, `core/*`, `db_core/base.py` |
| Заглушки nginx | `index.html`, `custom_50x.html` — по 18 байт, к тому же не подключены (нет `location /` и `error_page`) |

### 6.4. Нарушения модели исполнения

| Проблема | Место | Следствие |
|---|---|---|
| 🔴 Блокирующий `task.get()` после `.delay()` | все эндпоинты `run_task/`, `temp_router_task.py` | Очередь не даёт выигрыша; воркер uvicorn заблокирован на время задачи |
| 🔴 `async def` с синхронной `Session` | `app22/not_async_examples/router_not_async_many_db.py` | Блокирующие обращения к БД внутри event loop — останавливают все остальные запросы процесса |
| 🟡 Синхронный `open().write()` для upload | `router_reader_two.py`, `POST /upload_file` | Блокирует event loop на время записи файла |
| 🟡 `asyncio.run()` внутри Celery-задачи | `app11/celery_tasks/temp_task.py` | Новый event loop на каждую задачу |
| 🟡 `datetime.utcnow()` | `run_task/`, `celery_tasks/`, модели `app11` | Deprecated с Python 3.12; в `app22/db_core/type_for_models.py` уже корректный `datetime.now(timezone.utc)` |

### 6.5. Несогласованность поколений

Проект находится в середине миграции, и в нём одновременно присутствуют:

- **Pydantic v1 и v2 API**: `.dict()` в `app11` и `app22/not_async_examples`, `.model_dump()` в `app22/db_core` и наследниках.
- **SQLAlchemy legacy и 2.0**: `db.query()` против `select()` + `await db.execute()`.
- **Три стиля объявления моделей** (см. §2.8).
- **Два контура зависимостей**: `uv.lock` локально против `pip install -r requirements.txt` в Docker, причём `requirements.txt` в репозитории отсутствует.
- **Две версии Python**: `requires-python = ">=3.12"` и `.python-version` = 3.12 против `FROM python:3.11` во всех Dockerfile.

При доработке за образец следует брать `app22/db_core/` — это самый новый и наиболее связный код проекта (наибольший fan-in по графу), плюс шаблоны из `app22/template_files/`.

---

## 7. Куда смотреть дальше

- Карта файлов и внешних зависимостей — `01_project_structure.md`
- Порядок инициализации, предусловия импорта, пошаговый разбор бизнес-процессов, ошибки и логирование — `03_execution_flow.md`
