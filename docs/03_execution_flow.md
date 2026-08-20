# 03. Логика и работа кода

> Все утверждения проверены чтением исходников. Пути — относительно корня репозитория.
> Дополняет `01_project_structure.md` (карта файлов) и `02_architecture.md` (слои и паттерны).

---

## 1. Жизненный цикл приложения

### 1.1. Порядок инициализации и цепочка побочных эффектов при импорте

В проекте **нет** ни `lifespan`, ни `@app.on_event("startup")`, ни `@app.on_event("shutdown")` (проверено grep по всей кодовой базе). Вся инициализация выполняется **побочными эффектами на этапе импорта модулей**. Порядок строго определён порядком строк в `app22/main.py` / `app11/main.py`.

Разбор для `app22` (для `app11` идентично, отличаются только имена модулей):

```
1) from base_dir_path import DIR_CWD, BASE_DIR
   └─ app22/base_dir_path.py
      DIR_CWD  = Path.cwd()                       ← зависит от того, откуда запущен процесс
      BASE_DIR = Path(__file__).resolve().parent  ← всегда каталог app22/

2) from config_log import logFC
   └─ app22/config_log.py
      ├─ from app22.core import config
      │    └─ app22/core/config.py
      │       load_dotenv("./app22/local.env")     ← ОТНОСИТЕЛЬНЫЙ путь от CWD
      │       LOG_DIR / LOG_FILE / FILES_DIR / OPEN_API_PREFIX / DB_* = os.environ.get(...)
      │       DATABASE_URL       = "sqlite:///./app22/test_fast_api.db"        (захардкожен)
      │       DATABASE_URL_ASYNC = "sqlite+aiosqlite:///.app22/test_fast_api.db" (захардкожен)
      └─ последние строки модуля (app22/config_log.py:129):
         ConfigLogger.setting_path_logger(log_dir=config.LOG_DIR, log_file=config.LOG_FILE)
         ├─ __create_log_dir()  → BASE_DIR / log_dir → os.mkdir(), если каталога нет
         ├─ create_config_dict() → dict с 6 форматтерами, 2 хендлерами, 3 логгерами
         ├─ logging.config.dictConfig(...)
         └─ ConfigLogger.isSetting = True
         logF  = ConfigLogger.get_logger("OnlyFile")
         logFC = ConfigLogger.get_logger("FileStdout")

3) from app22.core import get_app_fastapi
   └─ app22/core/__init__.py
      app_fastapi = FastAPI(root_path=OPEN_API_PREFIX)   ← ЭКЗЕМПЛЯР СОЗДАЁТСЯ ЗДЕСЬ

4) импорты 9 роутеров (app22/main.py:11-21)
   каждый роутер тянет app22.db_core.db_async
   └─ app22/db_core/db_async.py
      ├─ star-импорт 6 модулей моделей → все mapper'ы регистрируются в Base.metadata
      └─ async_db = AsyncSessionDB(url=DATABASE_URL_ASYNC, echo=True)
         ├─ create_async_engine(...)   ← соединение НЕ устанавливается (ленивый пул)
         ├─ async_sessionmaker(autoflush=False, expire_on_commit=False)
         └─ async_scoped_session(scopefunc=current_task)
      плюс модули *_crud_*.py создают синглтоны CRUD: readerDB, bookDB, order_async, userDB, …

5) app = get_app_fastapi()          ← возвращает уже созданный объект, не создаёт новый

6) app.include_router(...) × 9      ← маршруты регистрируются в порядке вызовов
```

Практические следствия этого порядка:

| Следствие | Детали |
|---|---|
| Конфигурация читается **до** создания `FastAPI` | Переопределить настройки программно (в тестах, в скрипте) невозможно — к моменту, когда управление доходит до вашего кода, `app`, движок БД и логгеры уже созданы |
| CWD обязателен | `load_dotenv("./app22/local.env")` и `sqlite:///./app22/test_fast_api.db` — относительные пути. Запуск не из корня репозитория ⇒ env не загружается (тихо, без ошибки), БД создаётся в другом месте |
| Каталог логов создаётся раньше всего остального | `os.mkdir` (а **не** `os.makedirs`) ⇒ вложенный `LOG_DIR` вида `./log/app22` даёт `FileNotFoundError` на импорте |
| БД на импорте не нужна | Оба движка (`create_engine`, `create_async_engine`) ленивые; первое соединение — в первом запросе. Приложение стартует при выключенном PostgreSQL и падает уже на эндпоинте |

### 1.2. Предусловия запуска (без них процесс не поднимается)

**1. Каталог приложения должен быть в `sys.path`.** Первые две строки обоих `main.py` — импорты **верхнего уровня**, а не пакетные:

```python
from base_dir_path import DIR_CWD, BASE_DIR   # app22/base_dir_path.py, НЕ app22.base_dir_path
from config_log import logFC                  # app22/config_log.py
# from app22.config_log import ConfigLogger   ← закомментированная пакетная альтернатива
```

Дальше в том же файле идут пакетные импорты (`from app22.core import ...`), поэтому в `sys.path` должны присутствовать **оба** каталога: корень репозитория и `app22/`. Модуль `base_dir_path.py` существует только в двух копиях — `app11/base_dir_path.py` и `app22/base_dir_path.py`; в корне его нет.

| Способ запуска | `sys.path[0]` | Итог |
|---|---|---|
| `python app22/main.py` из корня + `PYTHONPATH=.` | `app22/` | ✅ работает: оба вида импортов разрешаются |
| `uvicorn app22.main:app` (`Makefile`, `command:` в compose) | корень репозитория | 🔴 `ModuleNotFoundError: No module named 'base_dir_path'` — нужен `PYTHONPATH=.:app22` |
| Запуск из PyCharm по script path `app22/main.py` | `app22/` + content root | ✅ работает (в репозитории лежит `.idea/`) |
| `celery -A celery_tasks.celery_worker.celery` в контейнере | `/app11` (WORKDIR) + `/` (PYTHONPATH) | ✅ работает — именно ради этого в `app11/Docker-app11-celery` заданы `WORKDIR /app11` и `ENV PYTHONPATH=/` |

Это единственный настоящий барьер «первого запуска»: команды в `Makefile` (`run_app11_lin`, `run_app22_lin`) и `command:` в compose-файлах используют форму `uvicorn app*.main:app`, которая с активными (не закомментированными) импортами не разрешается. Варианты правки: запускать с `PYTHONPATH=.:app22`, либо переключить две первые строки `main.py` на пакетную форму из комментария.

**2. Файл `app*/local.env` должен существовать.** `os.environ.get` без второго аргумента возвращает `None`, валидации нет. `None` доходит до `BASE_DIR / log_dir`:

```
TypeError: unsupported operand type(s) for /: 'PosixPath' and 'NoneType'
  app22/config_log.py:19  in ConfigLogger.__create_log_dir
```

То есть отсутствие конфигурации проявляется не сообщением о конфигурации, а `TypeError` в модуле логирования. Образцы файлов — `app22/template_files/local.env_temp1` (для `app11`) и `local.env_temp2` (для `app22` и корневого `.env`).

**3. Схема БД должна быть создана заранее.** `Base.metadata.create_all()` в проекте **не вызывается нигде** (проверено grep). Единственный способ получить таблицы — Alembic (§1.5). При этом `Base.metadata.drop_all()` вызывается из эндпоинта `GET /app11/ex_post/drop_all_tables` (`app11/example_db/router_ex_post.py:148`) — после его вызова восстановить схему можно только повторным `alembic upgrade`.

**4. Для Docker-профиля:** внешняя сеть `app_net_new` (`make create-net`), файл `requirements.txt` в корне (его нет в репозитории, требуют все три Dockerfile) и сертификаты `nginx/cert/*.pem`.

### 1.3. Точки входа и способы запуска

| Способ | Команда | Что исполняется |
|---|---|---|
| Прямой | `python app11/main.py` | Импорты → `main()` → `logFC.info(...)` → `uvicorn.run(app, host="0.0.0.0", port=8000)` |
| ASGI-сервер | `.venv/bin/uvicorn app11.main:app --host 0.0.0.0 --port 8000 --reload` (`make run_app11_lin`) | Импорты → uvicorn берёт объект `app`. **`main()` не вызывается** |
| Docker | `command: bash -c "uvicorn app11.main:app --host 0.0.0.0 --port 8000 --reload"` | То же; порт публикуется не наружу, а только внутрь сети `172.20.0.11:8000` |
| Celery-воркер | `celery -A celery_tasks.celery_worker.celery worker -l info -f log/celery11.log` | Импорт `app11/celery_tasks/celery_worker.py` → `Celery(...)` → `include=["celery_tasks.async_task", "celery_tasks.temp_task"]` → регистрация задач |
| Миграции | `alembic revision --autogenerate` / `alembic upgrade heads` | `alembic.ini` → `app22/alembic/env.py` |

Расхождение портов, о котором стоит знать: `Makefile` поднимает `app22` на `8002`, `app22/main.py` и compose — на `9000`, а `nginx.conf` проксирует на `172.20.0.22:9000`.

Важное следствие второй строки таблицы: под `uvicorn app*.main:app` функция `main()` мертва. Её `logFC.info(f"'Start' FastApi 22 = {app}")` в лог не попадает, а завершающий `logFC.warning("end ...")` недостижим в принципе — он стоит **после** `uvicorn.run(...)`, то есть выполнился бы только при штатном возврате из сервера.

### 1.4. Завершение работы

Явного завершения нет. Что это означает по пунктам:

| Ресурс | Как освобождается |
|---|---|
| Сессия БД запроса | `finally: await session.close()` в `AsyncSessionDB.get_db` (`app22/db_core/db_async.py:71`), `finally: db.close()` в `SessionDB.get_db` (`app11/db_core/db_conf.py:32`) — то есть по завершении каждого запроса |
| Пул соединений движка | `engine.dispose()` / `async_engine.dispose()` не вызывается никогда. Пул умирает вместе с процессом |
| `async_scoped_session` | `remove()` не вызывается. Не критично, т.к. `scop_db` не используется ни в одном роутере |
| `aiohttp.ClientSession` | Создаётся и закрывается через `async with` внутри каждого вызова `get_req_send` / `post_req_send` — по сессии на запрос, утечки нет, но и переиспользования соединений нет |
| Незавершённые Celery-задачи | При остановке воркера теряются: `acks_late` не включён, `task_reject_on_worker_lost` не задан |
| Буфер логов | `RotatingFileHandler` без `delay`, запись синхронная — потерь при SIGTERM практически нет |
| Глобальный `task_id` в `app11/run_task/router_task.py` | Живёт в памяти процесса. Рестарт uvicorn ⇒ «текущая задача» забыта, `check_send_task` вернёт 405 |

Практический вывод: перезапуск приложений безопасен (состояние — только в БД и Redis), но SIGTERM не даёт in-flight запросам корректно закрыть транзакции, поскольку graceful-хуков нет.

### 1.5. Жизненный цикл схемы БД (Alembic)

Один корневой `alembic.ini` (`script_location = app22/alembic`, `prepend_sys_path = .`) обслуживает **только `app22`**. Каталог `app11/alembic/` существует, но ни один `alembic.ini` на него не указывает — для его использования нужно править `script_location` или добавлять второй ini-файл.

Обе `env.py` — **синхронные**: `engine_from_config` + `pool.NullPool`, без `run_sync`/`async_engine_from_config`. URL подставляется в рантайме, значение `sqlalchemy.url` из ini игнорируется:

```python
# app22/alembic/env.py
from app22.db_core import Base            # реэкспорт Base + импорт 6 модулей моделей
target_metadata = Base.metadata
from app22.core.config import DATABASE_URL
config.set_main_option("sqlalchemy.url", DATABASE_URL)   # sqlite:///./app22/test_fast_api.db
```

То есть миграции идут через **синхронный** драйвер (`sqlite3` для `app22`, `psycopg2` для `app11`), а приложение работает через `aiosqlite`. Метаданные видит только благодаря `app22/db_core/__init__.py`, который импортирует все модули моделей ради регистрации в `Base.metadata`; функция `get_models()` там же — страховка «на глаз», в рантайме не вызывается.

Порядок работы: `alembic revision --autogenerate` → post-write hook `black -l 79` форматирует созданный файл (поэтому `black` числится в рантайм-зависимостях) → имя файла по шаблону `%(year)d-%(month).2d-%(day).2d_%(hour).2d-%(minute).2d--%(rev)s--%(slug)s` → `alembic upgrade heads` (`heads`, а не `head`, — в `Makefile` заложена работа с несколькими ветками ревизий).

⚠️ Расхождение URL внутри `app22/core/config.py`, влияющее на рантайм:

```python
DATABASE_URL       = f"sqlite:///./app22/test_fast_api.db"        # alembic + not_async_examples
DATABASE_URL_ASYNC = f"sqlite+aiosqlite:///.app22/test_fast_api.db"  # ← ".app22", не "./app22"
```

Асинхронный URL указывает на каталог `.app22/` (с точкой в имени), синхронный — на `./app22/`. Alembic и `SessionDB_not_async` работают с одним файлом, `async_db` — с другим путём. Если каталога `.app22` нет, первый же `await db.execute(...)` даёт `OperationalError: unable to open database file`; если есть — приложение читает пустую БД без таблиц. Правка — одна точка с слэшем в строке `DATABASE_URL_ASYNC`.

---

## 2. Роутинг и обработка входящего запроса

### 2.1. Полный путь запроса

```
[1] Клиент
     GET https://xaphan.ru/app22/reader_aCrud_one/get_reader?nickname=Den
      │
[2] nginx :443  (nginx/nginx.conf)
     ssl_certificate /home/cert/certificate.pem
     client_max_body_size 1000M              ← лимит тела; для /upload_file это единственный лимит
     location /app22/ { proxy_pass http://172.20.0.22:9000; }
      │  в proxy_pass НЕТ URI-части ⇒ префикс /app22 НЕ срезается
      │  добавляются Host, X-Forwarded-For; proxy_redirect off
      ▼
[3] uvicorn :9000 → ASGI-scope с path="/app22/reader_aCrud_one/get_reader"
      │
[4] FastAPI(root_path="/app22")   (app22/core/__init__.py)
     root_path учитывается при матчинге и подставляется в servers[] openapi.json
      │  Стека middleware НЕТ (см. §2.3) — Starlette применяет только свои
      │  встроенные ServerErrorMiddleware и ExceptionMiddleware
      ▼
[5] Router → перебор зарегистрированных APIRoute в порядке include_router
      │
[6] route_class (только app11): MyApiRouter / MyApiRouterMany
     custom_route_handler оборачивает штатный обработчик в try/except
      ▼
[7] Разрешение зависимостей Depends (до входа в тело функции)
     db = await anext(async_db.get_db())        → AsyncSession
     params: SchemaReader = Depends()            → сборка Pydantic-модели из QUERY-параметров
      ▼
[8] Валидация входа Pydantic. Ошибка ⇒ 422 RequestValidationError, тело функции не вызывается
      ▼
[9] Тело обработчика: CRUD-синглтон либо прямой select()/insert()
      ▼
[10] response_model → сериализация; несоответствие типа ⇒ 500 ResponseValidationError
      ▼
[11] Закрытие зависимостей в обратном порядке: finally → await session.close()
      ▼
[12] JSON / FileResponse клиенту
```

Шаги [7] и [11] важны для понимания транзакций: сессия открывается **до** тела обработчика и закрывается **после** сериализации ответа. Явного `commit`/`rollback` в генераторе зависимости нет — фиксация только там, где обработчик или CRUD-метод вызвал `await db.commit()`.

### 2.2. Реестр роутеров

`app11/main.py` — 7 подключений (`include_router`), порядок регистрации маршрутов:

| # | Роутер | Файл | Префикс | `route_class` |
|---|---|---|---|---|
| 1 | `temp_route` | `app11/run_task/temp_router_task.py` | `/temp_route` | — |
| 2 | `tasks_route` | `app11/run_task/router_task.py` | `/tasks` | — |
| 3 | `ex_simple_route` | `app11/example_simple/router_ex_simple.py` | `/ex_simple` | — |
| 4 | `ex_user_route` | `app11/example_db/router_ex_user.py` | `/ex_user` | `MyApiRouter` |
| 5 | `ex_post_route` | `app11/example_db/router_ex_post.py` | `/ex_post` | `MyApiRouter` |
| 6 | `ex_many_route` | `app11/example_many_db/router_many.py` | `/ex_many` | `MyApiRouterMany` |
| 7 | `ex_assoc_route` | `app11/example_many_db/router_assoc.py` | `/ex_assoc` | `MyApiRouterMany` |

`app22/main.py` — 9 подключений:

| # | Роутер | Файл | Префикс |
|---|---|---|---|
| 1 | `api_request` | `app22/http_request_routers/router_api_request.py` | `/api_request` |
| 2 | `not_async_order_crud` | `app22/not_async_examples/router_not_async_many_db.py` | `/not_async_crud` |
| 3 | `new_many_async_one` | `app22/async_many_sql/router_many_async_one.py` | `/new_many_async_one` |
| 4 | `new_many_async_two` | `app22/async_many_sql/router_many_async_two.py` | `/new_many_async_two` |
| 5 | `new_many_aCrud_one` | `app22/async_many_sql/router_many_aCrud_one.py` | `/new_many_aCrud_one` |
| 6 | `new_many_aCrud_two` | `app22/async_many_sql/router_many_aCrud_two.py` | `/new_many_aCrud_two` |
| 7 | `join_one_r` | `app22/async_join_tables/router_join_one.py` | `/join_one_r` |
| 8 | `reader_aCrud_one` | `app22/async_reader_project/router_reader_one.py` | `/reader_aCrud_one` |
| 9 | `reader_aCrud_two` | `app22/async_reader_project/router_reader_two.py` | `/reader_aCrud_two` |

Про дублирование путей: `POST /add_order` объявлен в четырёх файлах, но у каждого роутера свой `prefix`, поэтому реальные URL различаются (`/new_many_async_one/add_order`, `/new_many_aCrud_one/add_order`, …) и коллизии нет. Единственное настоящее пересечение — префикс `/ex_many`, объявленный тремя роутерами (`router_many.py`, `router_many_first.py`, `router_many_sec.py`); в приложение включён только первый, остальные 10 эндпоинтов недостижимы. Если подключить их все, приоритет получат маршруты, зарегистрированные раньше: Starlette берёт **первое** совпадение по пути и методу.

Не подключены и не достижимы также `app22/template_files/templates_router.py` и `templates_super_router.py` — это заготовки для копирования.

### 2.3. Middleware

**Пользовательских middleware в проекте нет.** Проверено grep по `middleware`, `exception_handler`, `on_event`, `lifespan`, `CORS` — совпадений в рабочем коде ноль (единственное упоминание — закомментированный `@app_fastapi.exception_handler(IntegrityError)` в `app11/example_db/except_ex_db.py:8`).

| Возможность | Состояние |
|---|---|
| CORS | ❌ не настроен — браузерные запросы с другого origin будут заблокированы |
| GZip | ❌ нет (и в nginx не включён) |
| `TrustedHostMiddleware` | ❌ нет |
| HTTPS-редирект | делает nginx (`return 301`), но порт 80 в compose не публикуется |
| Логирование запросов | ❌ нет своего; только access-лог uvicorn в stdout |
| Request-ID / трассировка | ❌ нет |
| Аутентификация | ❌ нет ни на одном из 117 эндпоинтов |

Роль сквозной обработки частично выполняет **кастомный класс маршрута** (`route_class`) — это единственный механизм в проекте, применяющий одну логику ко группе эндпоинтов. Он работает не глобально, а на уровне роутера, и только в `app11`:

```python
# app11/example_many_db/except_many_db.py
class MyApiRouterMany(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                return await original_route_handler(request)
            except NotSupportedError as exc:          # ← только этот тип
                ...
                raise HTTPException(status_code=422, detail=detail)

        return custom_route_handler
```

Отличие двух реализаций и его последствия разобраны в §4.2.

### 2.4. Зависимости: что исполняется на каждый запрос

| Зависимость | Файл | Что делает на каждый запрос |
|---|---|---|
| `async_db.get_db` | `app22/db_core/db_async.py:66` | `self.async_session()` → `yield` → `finally: await session.close()` |
| `SessionDB.get_db` | `app11/db_core/db_conf.py:28` | `sessionLocal()` → `yield` → `finally: db.close()` |
| `SessionDB_not_async.get_db_not_async` | `app22/not_async_examples/not_async_db_conf.py:22` | То же, но **синхронная** сессия внутри async-приложения |
| `depends_celery` | `app11/celery_tasks/celery_worker.py:17` | Возвращает модульный синглтон `celery` — без накладных расходов |
| `Depends()` на Pydantic-схеме | `params: OrderGetQuery = Depends()` | FastAPI собирает модель из **query**-параметров, а не из тела |

Ключевой нюанс третьей строки: обработчики в `app22/not_async_examples/router_not_async_many_db.py` объявлены как `async def`, а сессию получают синхронную (`psycopg2`/`sqlite3`). Блокирующий драйвер вызывается прямо в event loop и останавливает обработку **всех** остальных запросов процесса на время SQL-операции. Для сравнения: если бы обработчик был объявлен как обычный `def`, FastAPI выполнил бы его в threadpool и блокировки цикла не возникло. Это ошибка, а не демонстрация — и именно этот роутер подключён вторым в `app22/main.py`.

---

## 3. Ключевые бизнес-процессы (step-by-step)

### 3.1. Reader → ListBook → Book: наполнение читательских списков

Самый крупный сценарий проекта (`app22/async_reader_project/`, 4 таблицы + 2 ассоциативные). Роутер `reader_aCrud_one`, CRUD-синглтоны `readerDB`, `listbookDB`, `bookDB`, `categoryDB`.

**Шаг 1. `POST /reader_aCrud_one/add_reader`** — создание читателя.

```
body: CreateReader
  └─ readerDB.add_record_try(body, db)                  AsyncBaseCRUD.add_record_try
       ├─ Reader(**body.model_dump())
       ├─ db.add() → try: await db.commit(); await db.refresh()
       └─ except IntegrityError → AddResult(result=False, reason=str(e))
  └─ if not reader.result: raise HTTPException(422, f"add error {reader.str_detail()}")
  └─ return reader.model                                 response_model=SchemaReader
```

Обратите внимание: наружу отдаётся не исключение, а объект-результат; `str_detail()` вырезает из текста драйвера подстроку между `"DETAIL: "` и следующей точкой.

**Шаг 2. `POST /reader_aCrud_one/add_list_to_reader`** — список книг с привязкой к читателю. Здесь появляется характерный для проекта приём: часть данных в теле (`body: CreateListBook`), часть — в query (`params: SchemaReader = Depends()`).

```
1. reader = await readerDB.get_record_one(params, db)      select(Reader).where(<фильтр из query>)
2. if reader is None → 422
3. listbookDB.add_record_try(body.set_reader(reader.id), db)   ← FK проставляет схема, не роутер
```

**Шаг 3. `POST /reader_aCrud_one/create_add_book_to_list`** — создать книгу сразу внутри нужного списка.

```
1. sch_reader = SchemaReader(id=params.reader_id, nickname=params.reader_nickname)
2. reader = await readerDB.get_record_rel_one(sch_reader, load=[Reader.book_lists], db=db)
       └─ select(Reader).where(...).options(joinedload(Reader.book_lists))
3. Перебор reader.book_lists в Python:
       for listB in reader.book_lists:
           if (params.list_id is None or listB.id == params.list_id) and listB.list_name == params.list_name:
               return await bookDB.add_book_to_list(body, db, listB)
4. Ни один список не подошёл → 422
```

Фильтрация выполняется **в приложении**, а не в SQL, — предзагрузка `joinedload` для этого и нужна.

**Шаг 4. `PUT /reader_aCrud_one/add_exist_book_to_list`** — привязка уже существующей книги к списку (запись в M:N через `secondary`). Самый показательный обработчик: ручной запрос + двусторонняя проверка однозначности.

```
1. where_reader = readerDB.get_filter_attr(filterReader)     [Reader.nickname == ...]
   where_list   = listbookDB.get_filter_attr(filterList)     [ListBook.list_name == ...]
2. if not where_reader → 422   (пустой фильтр = выборка всего, это запрещено явно)
3. query = select(ListBook)
             .options(selectinload(ListBook.reader))
             .options(selectinload(ListBook.books))
             .join(Reader)
             .where(and_(*where_reader, *where_list))
4. listBooks = result.scalars().all()
      пусто        → 422 "Not found ListBook"
      больше одного → 422 "More than one ListBook"
5. books = await bookDB.get_records_rel_list(body_book, load=[Book.categories, Book.lists], db=db)
      те же две проверки
6. listB.books.append(book)      ← INSERT в list_book_association делает ORM
   await db.commit(); await db.refresh(listB)
7. return listB, book            response_model=Tuple[ListBookReaderBooks, SchemaBookWithCategory]
```

Шаги 4 и 5 — паттерн «ровно одна запись», повторяющийся в проекте: вместо `.one()` с исключением SQLAlchemy код сам различает «нет» и «больше одной» и отдаёт разные 422-сообщения.

### 3.2. Аналитические выборки: subquery, CTE, HAVING

`app22/async_reader_project/router_reader_two.py` — не CRUD, а демонстрация построения сложного SQL. Разбор `GET /reader_aCrud_two/get_subquery_count_book` (самый насыщенный):

```
1. where_attr = readerDB.get_filter_attr(params)     ⚠ схема SchemaListBook, модель Reader (см. §4.5)
2. Подзапрос: пары (книга, читатель) без дублей
     select(Book, ListBook.reader_id).join(Book.lists)
       .distinct(Book.id, ListBook.reader_id).order_by(...)
       .subquery(name="subQ")
3. aliased(ListBook, subquery, "listA"), aliased(Book, subquery, "bookA")
     ← ORM-модели «накладываются» на подзапрос
4. CTE со счётчиком: select(bookAliased.id, count(...).label("countB"))
       .group_by(bookAliased.id).having(count(...) > 1).cte(name="cteQ")
5. Финальный запрос: select(ctequery.c.countB, bookAliased, Reader)
       .join(subquery, listAliased.reader_id == Reader.id)
       .join(ctequery, ctequery.c.id == bookAliased.id)
       .order_by(desc(ctequery.c.countB), bookAliased.id)
6. Пост-обработка в Python: свёртка строк в dict[int, QtyBookReader]
       qty_books.setdefault(book.id, QtyBookReader(qty_all=qty).set_book(book)).append_reader(reader)
7. return qty_books.values()
```

Соседние эндпоинты того же файла показывают альтернативы: `/get_subquery_join` — `subquery()` + `aliased`, `/get_having_cte` — `cte()` + `outerjoin` + `having`, `/get_join_distinct` — тот же результат без подзапроса, `/get_unique_joinedload` — `result.unique().scalars().all()` (обязательный `unique()` после `joinedload` коллекции).

### 3.3. Order ↔ Product: четыре стиля одной операции

Один домен реализован четырьмя способами — это ядро дидактической ценности репозитория. Сравнение реализаций `add_order`:

| Файл | Код | Комментарий |
|---|---|---|
| `app22/async_many_sql/router_many_async_one.py:33` | `Order(**body.model_dump())` → `db.add` → `commit` → `refresh` | Ручной ORM-путь, объект возвращается заполненным |
| `app22/async_many_sql/router_many_async_one.py:44` | `insert(Order).values(**body.model_dump())` → `db.execute` → `commit` | Core-INSERT: сгенерированный `id` в ответ не попадает, возвращается эхо тела |
| `app22/async_many_sql/router_many_aCrud_one.py:31` | `await order_async.add_record(body, db)` | Через `AsyncBaseCRUD`; `IntegrityError` уходит наружу |
| `app11/example_many_db/router_many.py` | `order_db.add_record(body, db)` | Синхронный `CRUDBase`, `db.query()`, Pydantic v1 `.dict()` |

**Работа со связью M:N через association object** — `app11/example_many_db/router_assoc.py`. Сценарий рассчитан на последовательный вызов:

```
1. POST /ex_assoc/add_big          — очистка (delete_all_for) + вставка 3 Order и 8 Product
2. GET  /ex_assoc/products_append  — запись через ПРЯМОЙ M:N (relationship secondary):
                                       order1.products.append(...)
                                       order2.products = [...]        (полная замена)
                                       order3.products.extend([...])
                                     поля count/unit_price недоступны — их проставляет БД по default
3. GET  /ex_assoc/assoc_append     — запись через ASSOCIATION OBJECT:
                                       OrderProductAssociation(count=1, unit_price=1000, product=...)
                                       order1.products_details.append(or_pr1)
                                     полезная нагрузка задаётся явно
4. PUT  /ex_assoc/remove           — order1.products.remove(...)  ⇒ DELETE строк ассоциации
5. GET  /ex_assoc/get_big_all      — чтение с сортировкой
6. DELETE /ex_assoc/delete_big_all — удаление всего
```

Шаги 2 и 3 записывают в **одну и ту же** таблицу `order_product_association` двумя разными `relationship` (конфликт погашен `overlaps=...`, см. `02_architecture.md` §2.7), поэтому повторный вызов после шага 2 упирается в `UniqueConstraint("order_id", "product_id")` — именно на этот случай в обработчиках стоит `try/except IntegrityError` с возвратом `{"ERROR": "IntegrityError", "DB": "not commit"}`, а в `/remove` — `except ValueError` (его бросает `list.remove()`, когда элемента в коллекции нет).

### 3.4. Постановка задачи в Celery: правильный и блокирующий путь

**Правильный (единственный в проекте) — пара эндпоинтов `app11/run_task/router_task.py`:**

```
GET /tasks/send_task?a=30&b=40&work_sleep=2&delay_exec_sec=30
 1. global task_id; if task_id is not None → 404 "Task started - only one task"
 2. scheduled_time = datetime.utcnow() + timedelta(seconds=delay_exec_sec)
 3. celery.send_task("create_task", args=[work_sleep, a, b], eta=scheduled_time)
       ── JSON ──▶ Redis (брокер) ──▶ celery_worker подхватит в eta
 4. task_id = task_result.id
 5. НЕМЕДЛЕННЫЙ ответ {"task_id": "..."}          ← клиент не ждёт

GET /tasks/check_send_task
 1. if task_id is None → 405 "Task not started"
 2. task = AsyncResult(task_id)
 3. status: SUCCESS → task.get(), сброс task_id в None, вернуть результат
            PENDING / STARTED / FAILURE → вернуть только статус
```

Ограничение реализации: `task_id` — глобальная переменная уровня модуля, то есть очередь одноместная и привязана к процессу (`02_architecture.md` §5.2).

**Блокирующий (все остальные эндпоинты `run_task/`)** — `POST /temp_route/sql_celery` как типовой пример:

```
1. task = sql_task.delay(body.dict())        ── Redis (брокер) ──▶ воркер
2. task_result = task.get()                  ← СИНХРОННОЕ ОЖИДАНИЕ в обработчике FastAPI
                                                     │
   воркер: sql_task(body_dict)                       │
             TaskOneAdd(**body_dict)                 │
             TaskOne(title=..., msg=...)             │
             with SessionDB.get_session() as db:     │  ← Depends недоступен вне HTTP
                 db.add / commit / refresh           │
             jsonable_encoder(new_one) ──▶ Redis (backend) ─┘
3. TaskOneQuery(**task_result) → JSON
```

Смысл очереди здесь утрачен: клиент ждёт столько же, сколько при прямом вычислении, плюс два обхода Redis. Крайний случай — `POST /tasks/task_apply`: задача ставится с `eta` на 10 секунд вперёд и тут же ожидается через `task.get()`, то есть обработчик заведомо блокируется на ~10 секунд. Обработчики объявлены как синхронные `def`, поэтому блокируется поток из threadpool, а не сам event loop — но при 40 одновременных запросах пул исчерпывается и приложение перестаёт отвечать.

### 3.5. Исходящий HTTP: два способа и два места вызова

`app22` (в event loop), `POST /api_request/weather_create_task` и `/weather_await_response`:

```
weather_create_task   → main_weather_create_task(q, APPID)
                          ClientHTTPS.get_req_create(...)   → asyncio.create_task(...)
                          [опционально task.add_done_callback(...)] → await task
weather_await_response → main_weather_await(q, APPID)
                          ClientHTTPS.get_req_await(...)    → прямой await get_req_send
                             async with ClientSession() as session:
                                 session.get(url, headers, params, verify_ssl=False)  ⚠ TLS не проверяется
                          → RespServer(url=..., response=<json>)
if result is None → 500;  иначе response_model=RespServer
```

`app11` (через воркер), `POST /temp_route/req1_delay`:

```
req1_task.delay(sleep_sec, q, APPID) ──▶ Redis ──▶ воркер:
    result = asyncio.run(main_weather(city, appid))   ← новый event loop на каждую задачу
    time.sleep(sleep_sec)
    return result.dict()
обработчик: task.get() → RespServer(**task_result)   ← снова блокирующее ожидание
```

Полезное следствие для доработки: `ClientHTTPS` создаёт новую `ClientSession` на каждый запрос (`async with` внутри `get_req_send`/`post_req_send`), поэтому keep-alive не работает; переиспользуемая сессия — очевидная точка оптимизации.

### 3.6. Upload / download файлов

`app22/async_reader_project/router_reader_two.py`, единственная работа с файловой системой:

```
POST /reader_aCrud_two/upload_file  (multipart, python-multipart)
 1. dirF = FILES_DIR (env) или f"app22/{file_info.dir_name}"
 2. fileN = file.filename или file_info.file_name
 3. if os.path.exists(f"{dirF}/{fileN}") → 404 "File already exists"      ← код 404 для конфликта
 4. with open(..., "wb") as buffer: buffer.write(await file.read())
      ⚠ файл целиком читается в память; запись синхронная — блокирует event loop
 5. return {"name": fileN, "size": dict(file.__dict__)["size"]}

GET /reader_aCrud_two/download_file
 1. dirF аналогично
 2. if not os.path.exists(...) → 404
 3. FileResponse(path=..., filename=..., media_type="application/octet-stream")
```

Имя каталога приходит от клиента и подставляется в путь без нормализации (`f"app22/{file_info.dir_name}"`), а `FILES_DIR` может быть `None`, если env не задан. Лимит размера задаётся только nginx (`client_max_body_size 1000M`); в compose каталог монтируется как `${PATH_FILE_STORE_APP22}:/fast-api-2/fileStore`.

### 3.7. Демонстрационные сценарии-переключатели

`GET /join_one_r/add_user_post?action=N` (`app22/async_join_tables/router_join_one.py`) — не эндпоинт в обычном смысле, а сценарный скрипт: числовой `action` выбирает ветку (0 — удалить всех `User`; 1 — найти и удалить `Post`; 2/3 — очистка перед вставкой; 4 — обновить `posts[0]`, `posts[2]` и удалить `posts[1]`). Ветка 4 обращается к элементам списка по индексу без проверки длины — при недостаточном количестве постов это `IndexError` → 500.

Такие же сценарии: `POST /join_one_r/create_person_addr` (очистка + вставка данных из `data_join.py`), `GET /join_one_r/get_person` (JOIN по неключевому полю `JoinAddress.addr_index == JoinPerson.link_addr`, результат только пишется в лог, наружу отдаётся `{}`), `POST /join_one_r/fixing_work_admin` (`selectinload` + `scalar_one()` + `append` в коллекцию `Mapped[List[...]]`).

Это важно учитывать при доработке: значительная часть эндпоинтов `app22` **изменяет и удаляет данные без параметров**, ориентируясь на фиксированные значения в коде (`promocode="first"`, `nickname="user123"`, `list_name="aaa"`, `user_id="new1"`).

---

## 4. Обработка ошибок

### 4.1. Четыре уровня, ни один не глобальный

| Уровень | Механизм | Где | Что даёт клиенту |
|---|---|---|---|
| Транспорт | `route_class=MyApiRouter(Many)` | 4 роутера `app11` | `422` c `detail={"errors": repr(exc), "body": <описание>}` |
| Обработчик | `raise HTTPException(...)` вручную | преобладающий способ во всех роутерах | `422`, реже `404` / `405` / `500` |
| CRUD | `AddResult` вместо исключения | `AsyncBaseCRUD.add_record_try` | Роутер сам решает, что отдать |
| Обработчик | локальный `try/except` вокруг блока ORM | `router_assoc.py` (3 шт.), `router_ex_post.py:41` | `200` с телом `{"ERROR": ...}` |

Глобальных `@app.exception_handler` нет (единственный вариант закомментирован в `app11/example_db/except_ex_db.py:8`). Всё, что не перехвачено локально, обрабатывает Starlette: `RequestValidationError` → `422`, `HTTPException` → указанный код, любое другое исключение → `500 Internal Server Error` с трейсбеком в stdout uvicorn (в файловый лог приложения он **не** попадает, см. §5.3).

### 4.2. Дефект перехвата в `MyApiRouterMany`

Два кастомных класса маршрута различаются одной строкой — типом перехватываемого исключения:

| Класс | Файл | `except` | Роутеры |
|---|---|---|---|
| `MyApiRouter` | `app11/example_db/except_ex_db.py` | `IntegrityError` | `/ex_user`, `/ex_post` |
| `MyApiRouterMany` | `app11/example_many_db/except_many_db.py` | `NotSupportedError` | `/ex_many`, `/ex_assoc` |

`NotSupportedError` SQLAlchemy бросает при обращении к неподдерживаемой возможности СУБД. Нарушение уникальности (`UniqueConstraint("order_id", "product_id")`, `unique=True` у `nickname`/`email`) — это `IntegrityError`, и `MyApiRouterMany` его **не** перехватывает. Значит, для `/ex_many` и `/ex_assoc` дубликат даёт не задуманный `422`, а `500`. Задуманное поведение сохранилось только там, где обработчик сам обернул код в `try/except IntegrityError` (`router_assoc.py`).

Второй нюанс обоих классов: ветвление по `self.name` (`"add_user"` / `"add_post"`) захардкожено. Для любого другого имени функции клиент получает `"что то пошло не так - <name>"`, то есть текст ошибки не зависит от сущности.

### 4.3. Транзакции при ошибке: `rollback` почти отсутствует

`db.rollback()` встречается в проекте **один раз** — `app11/example_db/router_ex_post.py:45`. Ни один генератор зависимости не делает `rollback` в `except`/`finally`:

```python
async def get_db(self):
    session: AsyncSession = self.async_session()
    try:
        yield session
    finally:
        await session.close()     # ← rollback не вызывается
```

Практически это безопасно (SQLAlchemy откатывает незакоммиченную транзакцию при возврате соединения в пул), но имеет два следствия. Первое: после пойманного `IntegrityError` сессия остаётся в состоянии «сломанной транзакции», и любой следующий запрос через **ту же** сессию завершится `PendingRollbackError`. В `AsyncBaseCRUD.add_record_try` это скрыто тем, что запрос почти сразу заканчивается. Второе: обработчики, делающие несколько `commit` подряд (`router_join_one.py`, `router_assoc.py`), не атомарны — частично применённые изменения останутся в БД.

### 4.4. Коды ответов: фактическое использование

| Код | Когда возвращается | Пример |
|---|---|---|
| `422` | Основной код ошибки в проекте: и «не найдено», и «дубликат», и «неоднозначный результат» | `raise HTTPException(422, f"get_order with {params} not found")` |
| `404` | Файл уже существует; задача уже запущена | `upload_file`, `send_task` |
| `405` | Задача не запущена | `check_send_task` |
| `500` | Задача Celery вернула `None`; любое непойманное исключение | `req1_delay`, `weather_create_task` |
| `201` | Явно задан в двух эндпоинтах `/tasks` | `task_apply`, `task_delay` |
| `200` | По умолчанию, в т.ч. для тел вида `{"ERROR": ...}` | `products_append` |

Отсутствие `404` для «не найдено» — сознательное соглашение проекта: `422` возвращается и на пустой результат выборки. При доработке это нужно либо сохранять, либо менять целиком.

### 4.5. Ошибки, возникающие из динамических фильтров

Приём `getattr(self.model, k)` (см. `02_architecture.md` §2.2) переносит ошибки имён из этапа компиляции в рантайм. Что именно ломается:

| Место | Механика | Результат |
|---|---|---|
| `POST /new_many_aCrud_one/get_all_orders_new` | `order_async.get_order_attr(params.order_by_list)`; значение `"time"` → `getattr(Order, "time")`, колонка называется `created_at` | `AttributeError` → `500` |
| `GET /reader_aCrud_two/get_having_cte`, `/get_subquery_count_book` | В `readerDB.get_filter_attr` передана схема `SchemaListBook`, а фильтр строится по модели `Reader` | Работает, пока заполнено только общее поле `id`; заданное `list_name`/`description`/`reader_id` → `AttributeError` → `500` |
| `GET /reader_aCrud_two/get_unique_joinedload` | `select(Reader).where(where_attr)` — список передан как единый аргумент вместо `*where_attr` | Ошибка компиляции запроса SQLAlchemy → `500` |

Диагностика во всех трёх случаях одинаково неудобна: 500 без осмысленного `detail`, трейсбек только в stdout uvicorn.

---

## 5. Логирование

### 5.1. Устройство

Единый механизм в обоих приложениях — `app11/config_log.py` и `app22/config_log.py` (две почти идентичные копии, различаются только `pathDir_default`: `./log` в `app11`, `./example_log_dir` в `app22`). Конфигурация через `logging.config.dictConfig`, собираемая функцией `create_config_dict(log_dir, log_file)`.

| Элемент | Значение |
|---|---|
| Форматтеры | 6: `form1`…`form4` (для файла), `con1`, `con2` (для консоли) |
| Хендлер файла | `rotating_file1` — `RotatingFileHandler`, `level=INFO`, `formatter=form2`, `maxBytes=1048576` (1 МиБ), `backupCount=20` ⇒ до ~21 МиБ на приложение |
| Хендлер консоли | `console1` — `StreamHandler` в `ext://sys.stdout`, `level=INFO`, `formatter=con2` |
| Логгеры | `Stdout` (только консоль), `FileStdout` (файл + консоль), `OnlyFile` (только файл); у всех `level=DEBUG` |
| Путь файла | `BASE_DIR / log_dir / log_file`, где `BASE_DIR` — каталог `app11/` или `app22/` |
| Формат `form2` | `/* %(asctime)s - %(module)s.%(funcName)s(%(lineno)d) - [%(threadName)s] - [%(thread)d] */ \n%(levelname)s: %(message)s` |

Важно: `level` хендлеров — `INFO`, а логгеров — `DEBUG`. Реальный порог фильтрации задаёт хендлер, поэтому `logFC.debug(...)` никуда не попадёт.

Защёлка от повторной настройки — классовый атрибут `ConfigLogger.isSetting`. Настройка выполняется один раз при первом импорте `config_log`, дальше `get_logger("FileStdout")` просто отдаёт `logging.getLogger(...)`. Именно поэтому каждый роутер может свободно повторять `logFC = ConfigLogger.get_logger("FileStdout")` на уровне модуля — это не пересоздаёт конфигурацию.

### 5.2. Что и где логируется

Соглашение по проекту: `logFC` (файл + консоль) на входе в обработчик и на выходе с результатом.

```python
# app22/http_request_routers/router_api_request.py
logFC.info(f"POST/weather_create_task : {datetime.now(timezone.utc)} : \n{body.model_dump()}")
...
logFC.info(f"POST/weather_create_task : {datetime.now(timezone.utc)} : res \n{result}")
```

| Область | Что пишется |
|---|---|
| Роутеры | Входное тело/параметры, тип и содержимое результата |
| Аналитические выборки | Построчный вывод результата в цикле (`router_reader_two.py`, `router_join_one.py`) — на больших выборках это дорогой лог |
| Celery-задачи | Метки `'Celery' <utcnow>: <task> - 'before'/'after'` (`app11/celery_tasks/temp_task.py`) |
| SQL | `echo=True` во **всех трёх** движках (`app11/db_core/db_conf.py`, `app22/db_core/db_async.py`, `app22/not_async_examples/not_async_db_conf.py`) ⇒ полный SQL и параметры идут в stdout логгером `sqlalchemy.engine` |
| Alembic | Отдельная секция `[loggers]` в `alembic.ini`: `root=WARN`, `sqlalchemy=WARN`, `alembic=INFO`, вывод в `sys.stderr` |

`logF` (`OnlyFile`) объявлен в обоих `config_log.py`, но в роутерах не используется — везде берётся `logFC`.

### 5.3. Ограничения, которые нужно учитывать

- **Access-лог uvicorn не перехвачен.** Блоки `"uvicorn"`, `"uvicorn.error"`, `"uvicorn.access"` в `create_config_dict` закомментированы (`app22/config_log.py:105-121`). Следствие: логи HTTP-запросов и **трейсбеки 500-х** идут только в stdout, а прикладной лог живёт в файле. Единая картина инцидента собирается только из двух источников; в Docker stdout виден через `docker logs`, файл — через bind-mount (`./app11/log_app`, `./app22/log_app`).
- **`echo=True` в продакшн-профиле.** SQL-лог включён безусловно, отключается только правкой кода. На аналитических эндпоинтах §3.2 это кратно увеличивает объём вывода.
- **Нет корреляции запросов.** Ни request-id, ни имени пользователя, ни трассировки; при параллельных запросах строки в файле перемешиваются, различить их можно только по `[%(threadName)s]`/`[%(thread)d]` из `form2`.
- **Каталог создаётся через `os.mkdir`.** Вложенный `LOG_DIR` не поддерживается (см. §1.1).
- **Пути логов в Docker расходятся.** Приложения пишут в `BASE_DIR/<LOG_DIR>` = `/fast-api-2/app11/log`, воркер Celery — в `/app11/log` (другой WORKDIR), и монтируются они в разные хостовые каталоги: `./app11/log_app` и `./app11/log_celery`.
- **Секреты попадают в лог.** Обработчики пишут в лог входные тела целиком (`body.dict()`, `body.model_dump()`), включая поля `password` и `APPID`.

---

## 6. Быстрый индекс: симптом → место в коде

Таблица для навигации при отладке и для AI-агентов.

| Симптом | Файл и причина |
|---|---|
| `ModuleNotFoundError: No module named 'base_dir_path'` | `app11/main.py:1`, `app22/main.py:1` — каталог приложения не в `sys.path` (§1.2) |
| `TypeError: unsupported operand type(s) for /: 'PosixPath' and 'NoneType'` | `app*/config_log.py:19` — нет `app*/local.env`, `LOG_DIR is None` (§1.2) |
| `FileNotFoundError` при создании каталога логов | `app*/config_log.py:21` — `os.mkdir` вместо `os.makedirs` (§1.1) |
| `OperationalError: unable to open database file` | `app22/core/config.py` — `DATABASE_URL_ASYNC` указывает на `.app22/`, а не `./app22/` (§1.5) |
| `no such table` / `relation does not exist` | Схема создаётся только Alembic; `create_all` нет. Возможно, ранее вызывали `GET /app11/ex_post/drop_all_tables` (§1.2) |
| 404 на всех маршрутах, неработающий Swagger | Рассогласование `OPEN_API_PREFIX` ↔ `location` в `nginx/nginx.conf` ↔ `root_path` (`02_architecture.md` §4.4) |
| Дубликат вместо `422` даёт `500` | `MyApiRouterMany` ловит `NotSupportedError`, а не `IntegrityError` (§4.2) |
| `AttributeError` на фильтре/сортировке | `AsyncBaseCRUD._get_filter_attr` / `get_order_attr` — имя поля схемы ≠ имя колонки (§4.5) |
| `PendingRollbackError` в следующем запросе | Нет `rollback` в генераторах зависимостей (§4.3) |
| Запрос «висит» ~10 секунд | `POST /tasks/task_apply` — `eta=+10s` плюс блокирующий `task.get()` (§3.4) |
| Приложение перестало отвечать под нагрузкой | Либо исчерпан threadpool блокирующими `task.get()`, либо синхронная сессия в `async def` (`app22/not_async_examples/router_not_async_many_db.py`, §2.4) |
| Трейсбек 500 не найден в файле лога | Логгеры uvicorn не перехвачены — трейсбек только в stdout (§5.3) |
| Эндпоинт удалил данные без параметров | Сценарные обработчики с захардкоженными значениями (§3.7) |
| Изменения не сохранились после ошибки в середине | Несколько `commit` в одном обработчике, атомарности нет (§4.3) |

---

## 7. Куда смотреть дальше

- Карта файлов, внешние зависимости, отсутствующие артефакты — `01_project_structure.md`
- Слои, паттерны, поток данных, конфигурация, технический долг — `02_architecture.md`
- Эталоны для нового кода: `app22/db_core/` (движок, дженерик-CRUD, аннотированные типы) и `app22/template_files/` (шаблоны модели, схемы, CRUD, роутера, env)
