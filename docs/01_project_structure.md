# 01. Карта проекта

> Ветка на момент составления: `betaReform`. Remote: `https://github.com/xaphan13/fast-api-two-2-reformat.git`.
> Все пути — относительно корня репозитория.

---

## 1. Назначение проекта

`fast-api-two-2-reformat` — **учебно-демонстрационный полигон FastAPI + SQLAlchemy 2.0**, а не прикладной продукт. В одном репозитории живут два независимых FastAPI-приложения, поставленные рядом намеренно, чтобы сопоставить два подхода к работе с БД: `app11` — синхронный стек (`sessionmaker`, `psycopg2`, блокирующий ORM) с внешней обработкой задач через Celery/Redis, и `app22` — асинхронный стек (`async_sessionmaker`, `asyncpg`/`aiosqlite`, `await db.execute(...)`) с дженерик-слоем CRUD. Прикладной домен (пользователи, посты, заказы, товары, читатели, книги) выбран как минимальный носитель для демонстрации типов связей SQLAlchemy, а не как бизнес-требование.

Отсюда вытекают свойства, которые важно понимать до чтения кода. Пакеты называются `example_db`, `example_many_db`, `example_simple`, `not_async_examples`, `async_join_tables`, `async_reader_project` — это **не слои приложения, а параллельные, взаимно независимые примеры**; один и тот же домен (`Order`/`Product`) реализован по несколько раз в разных стилях, и роутеры сознательно дублируют пути (`POST /add_order` объявлен в четырёх разных файлах). Тесты, аутентификация и CI отсутствуют полностью; роль «проверки гипотезы» играет сам факт работоспособности примера. Каталог `app22/template_files/` — это библиотека заготовок для копирования при создании нового модуля. Как следствие, репозиторий следует читать как набор рецептов: точка входа + инфраструктура общие, а каждый пакет `*_examples`/`example_*`/`async_*` самодостаточен и может быть изучен изолированно.

---

## 2. Дерево директорий и ключевых файлов

### 2.1. Корень: инфраструктура, сборка, эксплуатация

```
fast-api-two-2-reformat/
├── pyproject.toml                     # Метаданные, 22 зависимости, конфиг ruff и black
├── uv.lock                            # Лок-файл uv — фактический менеджер зависимостей
├── .python-version                    # 3.12
├── reqs_top.txt                       # Снимок прямых зависимостей (10 из 22) — УСТАРЕЛ
├── reqs_all.txt                        # Снимок полного дерева (55) — УСТАРЕЛ
├── alembic.ini                        # Один конфиг миграций, жёстко указан на app22/alembic
├── Makefile                           # Локальный запуск, create-net, миграции
├── READ-me.md                         # Шпаргалка по Python-окружению для Windows (не README)
│
├── comp-nginx-postg-redis.yml         # Стек: db + redis + nginx
├── comp-nginx-postg-redis-admin.yml   # То же + pgadmin + flower
├── comp-pgadmin-flower.yml            # Только админки (довесок)
├── comp-app11-celery11-app22.yml      # Только приложения: app_first, app_two, celery_worker
├── comp-ng-ap1-cel1-ap2-post-red.yml  # «Всё в одном»
│
├── .dockerignore                      # Исключает env, логи, .venv, pg_db, *.yml
├── .gitignore                         # Исключает *.env, *.log, *.db, pg_db/, сертификаты
├── .gitattributes                     # * text=auto (LF-нормализация; разработка на Linux+Windows)
│
├── docker_manager.sh                  # net-create (обязательный шаг) и cont-stop
├── adminGit.sh                        # Обёртки git: br/st/brst/rembrst/commit/push_two
├── cmd.sh                             # Черновик-песочница; прототип sed+heredoc правки конфигов
├── ufw-docker-17-20.sh                # Сторонний ufw-docker, адаптирован под подсеть 172.20.0.0/16
│
└── nginx/
    ├── Docker-nginx                   # nginx:1.20-alpine, копирует конфиг, web/ и сертификаты
    ├── nginx.conf                     # Два server-блока (80 → редирект, 443 TLS); 5 location
    └── web/default/
        ├── index.html                 # Заглушка «Silence is golden!» (18 байт, не подключена)
        └── custom_50x.html            # Заглушка «Silence is golden!» (18 байт, не подключена)
```

Пять compose-файлов — не альтернативы, а **взаимодополняющие срезы одного стека**, склеенные через внешнюю сеть `app_net_new` со статической IP-адресацией в `172.20.0.0/16`. Именно `external: true` плюс захардкоженные адреса в `nginx.conf` позволяют поднимать сервисы разными командами: они находят друг друга по фиксированным IP, а не через DNS одного compose-проекта. Обязательное предусловие — создать сеть вручную (`make create-net` либо `bash docker_manager.sh net-create`).

### 2.2. `app11/` — синхронное приложение (uvicorn `:8000`)

```
app11/
├── main.py                  # Точка входа: get_app_fastapi(), include_router × 7, uvicorn :8000
├── base_dir_path.py         # DIR_CWD = Path.cwd(); BASE_DIR = каталог app11/
├── config_log.py            # ConfigLogger + dictConfig; логгеры logF (OnlyFile), logFC (FileStdout)
│
├── core/
│   ├── __init__.py          # Синглтон app_fastapi = FastAPI(root_path=OPEN_API_PREFIX) + фабрика
│   └── config.py            # dotenv из ./app11/local.env; DATABASE_URL (psycopg2), CELERY_*
│
├── db_core/
│   ├── base.py              # class Base(DeclarativeBase) — декларативная база SQLAlchemy 2.0
│   ├── db_conf.py           # class SessionDB: engine, sessionLocal, get_db() (Depends), get_models()
│   └── __init__.py
│
├── example_db/              # ПРИМЕР 1: связь один-ко-многим User → Post
│   ├── model_ex_db.py       # User (nickname/email unique) и Post (FK users.id); relationship posts/author
│   ├── schema_ex_db.py      # Pydantic-схемы для User/Post
│   ├── crud_db_users.py     # CRUD-операции для User/Post
│   ├── router_ex_user.py    # 12 эндпоинтов: add/get/delete/update + template_* варианты
│   ├── router_ex_post.py    # 11 эндпоинтов, включая joinedload и DROP всех таблиц
│   └── except_ex_db.py      # Кастомный APIRoute для перехвата ошибок БД
│
├── example_many_db/         # ПРИМЕР 2: many-to-many Order ↔ Product + association object
│   ├── model_many_db.py     # Order, Product, OrderProductAssociation (count, unit_price)
│   ├── schema_many_db.py    # Схемы заказов и товаров
│   ├── crud_base.py         # class CRUDBase — ДЖЕНЕРИК синхронный Repository (см. 02_architecture)
│   ├── crud_many.py         # Наследники CRUDBase под конкретные модели
│   ├── router_many.py       # 14 эндпоинтов: Order + Product (подключён в main.py)
│   ├── router_many_first.py # 5 эндпоинтов — альтернативная реализация, НЕ подключена
│   ├── router_many_sec.py   # 5 эндпоинтов — альтернативная реализация, НЕ подключена
│   ├── router_assoc.py      # 6 эндпоинтов: работа через association object (подключён)
│   └── except_many_db.py    # class MyApiRouterMany(APIRoute) — перехват NotSupportedError → 422
│
├── example_simple/          # ПРИМЕР 3: базовый роутинг без БД
│   ├── router_ex_simple.py  # 5 эндпоинтов GET/POST/PUT/PATCH/DELETE, path-параметры
│   └── schema_ex_simple.py
│
├── run_task/                # HTTP-фасад над Celery
│   ├── model_task.py        # TaskOne (title, msg), TaskTwo (username, password)
│   ├── schema_task.py       # ReqTaskSchema, RespTaskSchema, TaskOneAdd, Req1BodyReq, Req1ParamsReq
│   ├── router_task.py       # 5 эндпоинтов: apply_async, delay, shared_task, send_task, check_send_task
│   └── temp_router_task.py  # 2 эндпоинта: req1_delay (погода через Celery), sql_celery (запись в БД)
│
├── celery_tasks/
│   ├── celery_worker.py     # Celery("celery_worker_new"); include=[celery_tasks.async_task, ...]
│   ├── async_task.py        # create_task (@celery.task), create_shared_task (@shared_task)
│   ├── temp_task.py         # req1_task (HTTP к погоде), sql_task (INSERT в TaskOne)
│   └── Class_client_https.py# HTTP-клиент + main_weather(), RespServer
│
├── alembic/
│   ├── env.py               # Синхронные миграции; set_main_option("sqlalchemy.url", DATABASE_URL)
│   └── versions/            # 5 ревизий в ДЕФОЛТНОМ формате имён (081987267877_.py и др.)
│
├── Docker-app11             # python:3.11, WORKDIR /fast-api-2, pip install -r requirements.txt
└── Docker-app11-celery      # python:3.11, WORKDIR /app11, PYTHONPATH=/ (двойное разрешение импортов)
```

### 2.3. `app22/` — асинхронное приложение (uvicorn `:9000`)

```
app22/
├── main.py                     # Точка входа: include_router × 9, uvicorn :9000
├── base_dir_path.py            # То же, что в app11 (дублируется)
├── config_log.py               # То же, что в app11 (дублируется)
│
├── core/
│   ├── __init__.py             # Синглтон FastAPI(root_path=OPEN_API_PREFIX)
│   └── config.py               # dotenv из ./app22/local.env; URL БД ЗАХАРДКОЖЕН на SQLite
│
├── db_core/                    # ЯДРО: единственный настоящий переиспользуемый слой проекта
│   ├── base.py                 # class Base(DeclarativeBase)
│   ├── db_async.py             # class AsyncSessionDB (3 стратегии сессии) + синглтон async_db
│   ├── async_crud_base.py      # class AsyncBaseCRUD[5 TypeVar] + AddResult + db_json()
│   ├── type_for_models.py      # Annotated-типы: int_primary_key, str_len_100, time_stamp_utc
│   └── __init__.py             # Реэкспорт Base + импорт всех модулей моделей для Alembic
│
├── async_many_sql/             # ПРИМЕР: many-to-many + association object, АСИНХРОННО
│   ├── model_new_many_db.py    # Order, Product, OrderProductAssociation
│   ├── schema_many_sql.py      # Схемы Create/Read/Update/Delete
│   ├── async_crud_order.py     # Наследники AsyncBaseCRUD
│   ├── router_many_async_one.py# 5 эндпоинтов — стиль «ручной SQL» (select/insert напрямую)
│   ├── router_many_async_two.py# 4 эндпоинта — ручной SQL: delete/update, одиночные и списком
│   ├── router_many_aCrud_one.py# 5 эндпоинтов — тот же домен через AsyncBaseCRUD
│   └── router_many_aCrud_two.py# 5 эндпоинтов — update/delete через AsyncBaseCRUD
│
├── async_join_tables/          # ПРИМЕР: JOIN, один-к-одному, один-ко-многим
│   ├── model_new_ex_db.py      # User, Post
│   ├── model_join.py           # JoinPerson, JoinAddress
│   ├── model_admin.py          # Admin_list, Admin_work
│   ├── schema_join.py          # Схемы для Person/Address
│   ├── schema_user_post.py     # Схемы для User/Post
│   ├── async_crud_user.py      # CRUD для User
│   ├── async_crud_post.py      # CRUD для Post
│   ├── async_crud_join_person.py  # CRUD для JoinPerson
│   ├── async_crud_join_address.py # CRUD для JoinAddress
│   ├── data_join.py            # Тестовые данные / хелперы
│   └── router_join_one.py      # 6 эндпоинтов: add_user_post, create_person_addr, fixing_work_admin
│
├── async_reader_project/       # ПРИМЕР: самый крупный (84 узла графа) — ассоциативные таблицы
│   ├── model_reader_book.py    # Reader, ListBook, Book, Category
│   ├── model_reader_assoc.py   # ListBookAssociation, BookCategoryAssociation
│   ├── schema_reader.py        # Схемы Reader/Book
│   ├── schema_reader_assoc.py  # Схемы ассоциаций
│   ├── schema_relationship.py  # Схемы с вложенными связями для ответов
│   ├── async_crud_reader.py    # Наследники AsyncBaseCRUD
│   ├── router_reader_one.py    # 9 эндпоинтов: CRUD + привязка книг к спискам
│   └── router_reader_two.py    # 7 эндпоинтов: subquery, CTE, having, distinct + upload/download
│
├── http_request_routers/       # Исходящие HTTP-вызовы (интеграция)
│   ├── Class_client_https.py   # Класс HTTP-клиента
│   ├── client_openweathermap.py# Клиент OpenWeatherMap
│   └── router_api_request.py   # 2 эндпоинта: weather_create_task, weather_await_response
│
├── not_async_examples/         # Синхронный островок внутри async-приложения (для сравнения)
│   ├── not_async_db_conf.py    # Отдельный синхронный движок и сессия
│   ├── not_async_crud_base.py  # Синхронный базовый CRUD
│   ├── not_async_crud_many.py  # Наследники
│   └── router_not_async_many_db.py # 2 эндпоинта
│
├── template_files/             # БИБЛИОТЕКА ЗАГОТОВОК — эталон для нового модуля
│   ├── templates_model.py      # Шаблон модели SQLAlchemy
│   ├── templates_schema.py     # Шаблон Pydantic-схем
│   ├── templates_async_crud.py # Шаблон наследника AsyncBaseCRUD
│   ├── templates_router.py     # Шаблон роутера (4 эндпоинта: add_/get_/update_/delete_)
│   ├── templates_super_router.py # Расширенный шаблон (3 эндпоинта)
│   ├── local.env_temp1         # Шаблон env: app11, локальный запуск
│   ├── local.env_temp2         # Шаблон env: app22 + переменные для compose
│   ├── dock_app1.env_temp      # Шаблон env: app11 в Docker (DNS-имена контейнеров)
│   └── dock_app2.env_temp      # Шаблон env: app22 в Docker
│
├── alembic/
│   ├── env.py                  # Асинхронные миграции
│   └── versions/               # 6 ревизий в формате file_template (2026-01-11_19-33--...)
│
└── Docker-app22                # python:3.11, WORKDIR /fast-api-2
```

### 2.4. Файлы, отсутствующие в репозитории, но необходимые для запуска

Эти артефакты исключены через `.gitignore` либо никогда не коммитились. Без них проект не собирается и не стартует.

| Артефакт | Кто требует | Следствие отсутствия |
|---|---|---|
| `requirements.txt` | 3 Dockerfile (`COPY requirements.txt`) | 🔴 сборка образов падает; в git не было никогда |
| `nginx/cert/certificate.pem`, `private_key.pem` | `nginx/Docker-nginx` | 🔴 сборка nginx-образа падает |
| `app11/local.env`, `app22/local.env` | `app*/core/config.py` | 🔴 падение на импорте (см. `03_execution_flow.md`) |
| `app11/dock_app1.env`, `app22/dock_app2.env` | `env_file` в compose | 🔴 контейнеры без конфигурации |
| Корневой `.env` | `${DB_USER}`, `${OPEN_API_PREFIX_APP11}`, `${PATH_LOG_*}` в compose | 🔴 пустая подстановка переменных |
| Внешняя сеть `app_net_new` | все compose-файлы (`external: true`) | 🔴 `docker compose up` падает |

Образцы для восстановления — в `app22/template_files/`. Для корневого `.env` ближайший источник — `local.env_temp2` (единственный, где есть `OPEN_API_PREFIX_APP11/22`, `PATH_LOG_*`, `PATH_FILE_STORE_APP22`, `PGADMIN_*`).

---

## 3. Внешние зависимости и их роль

### 3.1. Инфраструктурные сервисы

| Сервис | Образ | Порт (host:container) | Роль | Кто использует |
|---|---|---|---|---|
| **PostgreSQL** | `postgres:16` (в «всё-в-одном» — `postgres` без тега) | `7032:5432` | Основная СУБД. Данные в bind-mount `./pg_db` | `app11` через `psycopg2`; `app22` — только в закомментированном конфиге |
| **Redis** | `redis:6.2-alpine` | `7079:6379` | Одновременно **брокер** и **backend результатов** Celery. Кэша приложения нет | `app11` (`celery_worker`) |
| **nginx** | `nginx:1.20-alpine` | `443:443` | TLS-терминация и reverse-proxy на два приложения по префиксам URL | Точка входа для всех внешних запросов |
| **pgAdmin** | `dpage/pgadmin4` | не публикуется (`:5123` внутри) | Веб-UI к PostgreSQL, доступен только через nginx `/pgadmin` | Разработчик |
| **Flower** | `mher/flower:0.9.7` | не публикуется (`:5801` внутри) | Мониторинг очередей Celery, через nginx `/flower_first` | Разработчик |
| **SQLite** | — (файл `app22/test_fast_api.db`) | — | **Фактическая БД `app22`**: URL захардкожен в `app22/core/config.py` | `app22` через `aiosqlite` |

Порт `80` не публикуется ни в одном compose-файле, поэтому объявленный в `nginx.conf` редирект HTTP → HTTPS снаружи недостижим.

### 3.2. Сторонние API

| API | Клиент | Назначение |
|---|---|---|
| **OpenWeatherMap** | `app22/http_request_routers/client_openweathermap.py`; `app11/celery_tasks/Class_client_https.py` (`main_weather`) | Единственная внешняя интеграция. Демонстрирует два способа исходящего вызова: напрямую из async-эндпоинта (`app22`) и через Celery-задачу (`app11`, `req1_task`). Ключ передаётся параметром запроса `APPID`, не через env |

### 3.3. Python-библиотеки по ролям

Всего 22 записи в `[project].dependencies`, `requires-python = ">=3.12"`.

| Роль | Пакеты |
|---|---|
| Веб-фреймворк | `fastapi==0.127.0`, `starlette==0.50.0`, `uvicorn==0.40.0`, `python-multipart` (upload файлов) |
| Валидация | `pydantic==2.12.5`, `typing-extensions==4.15.0` |
| ORM и миграции | `sqlalchemy==2.0.45`, `alembic>=1.17.2` |
| Драйверы БД | `psycopg2-binary` (sync Postgres), `asyncpg` (async Postgres), `aiosqlite` (async SQLite) |
| Очередь задач | `celery==5.6.0`, `redis>=7.1.0`, `flower>=2.0.1`, `celery-types` |
| HTTP-клиент | `aiohttp==3.13.2`, `async-timeout` |
| Конфигурация | `python-dotenv==1.2.1` |
| Качество кода | `black>=25.12.0` (в рантайм-зависимостях, т.к. вызывается post-write hook`ом Alembic), `ruff` — только конфиг в `pyproject.toml` |
| Прочее | `bcrypt` (объявлен, хеширование паролей не реализовано), `multipledispatch`, `python-editor` |

**Управление зависимостями раздвоено.** Локально — `uv` с `uv.lock`. В Docker — `pip3 install -r requirements.txt`, причём сам `requirements.txt` в репозитории отсутствует. Снимки `reqs_top.txt` и `reqs_all.txt` отстали от `uv.lock` (нет `aiosqlite`, `celery-types`, `python-editor`, `python-multipart`, `aiohappyeyeballs`). Дополнительно расходятся версии интерпретатора: `.python-version` и `requires-python` требуют 3.12, все Dockerfile используют `FROM python:3.11`.

---

## 4. Численный профиль кодовой базы

По графу знаний (`codebase-memory-mcp`, 1230 узлов, 4641 связь):

| Метрика | Значение |
|---|---|
| Python-файлов | 107 (плюс 5 YAML, 4 Bash, 2 HTML, 1 TOML) |
| Точек входа | 2 — `app11/main.py`, `app22/main.py` |
| Обработчиков маршрутов | **117** в 17 файлах-роутерах |
| Классов / функций / методов | 213 / 232 / 136 |
| Таблиц БД | 8 в `app11`, 15 в `app22` |
| Тестов | **0** (ни `pytest`, ни `conftest.py`, ни CI) |

Самые связные узлы (fan-in) — `AsyncBaseCRUD._get_filter_attr` (11), `AsyncBaseCRUD.get_record_one` (10), `ConfigLogger.get_logger` (10 в `app11`, 9 в `app22`). Это подтверждает, что единственный по-настоящему переиспользуемый код проекта — `app22/db_core/` и продублированный в обоих приложениях `config_log.py`; всё остальное — изолированные примеры.

---

## 5. Куда смотреть дальше

- Слои, паттерны, поток данных, конфигурация — `02_architecture.md`
- Порядок запуска, предусловия импорта, разбор бизнес-процессов, ошибки и логирование — `03_execution_flow.md`
