# NoteFlow

SaaS-платформа для личных заметок на **FastAPI**, **PostgreSQL** и **Docker Compose**.

## Возможности

- Регистрация и вход (JWT-аутентификация)
- Личный кабинет со статистикой и настройками профиля
- Изолированные заметки для каждого пользователя
- Автосохранение, поиск, закрепление, цветовые метки
- Лендинг и современный тёмный интерфейс
- REST API с документацией Swagger

## Быстрый старт

```bash
docker compose up -d --build
```

| Страница | URL |
|----------|-----|
| Лендинг | http://localhost:8000 |
| Регистрация | http://localhost:8000/register |
| Вход | http://localhost:8000/login |
| Заметки | http://localhost:8000/app |
| Личный кабинет | http://localhost:8000/dashboard |
| Swagger | http://localhost:8000/api/docs |

## Остановка

```bash
docker compose down
```

Данные PostgreSQL сохраняются в volume `postgres-data`. Чтобы удалить и данные:

```bash
docker compose down -v
```

## Структура проекта

```
notes-app/
├── app/
│   ├── main.py          # Точка входа, маршруты страниц
│   ├── config.py        # Настройки из переменных окружения
│   ├── auth.py          # JWT, хеширование паролей
│   ├── database.py      # Подключение к PostgreSQL
│   ├── models.py        # User, Note
│   ├── schemas.py       # Pydantic-схемы
│   ├── crud.py          # Операции с БД
│   └── routers/
│       ├── auth.py      # /api/auth/*
│       └── notes.py     # /api/notes/*
├── static/
│   ├── landing.html     # Главная страница
│   ├── login.html       # Вход
│   ├── register.html    # Регистрация
│   ├── app.html         # Редактор заметок
│   ├── dashboard.html   # Личный кабинет
│   ├── css/style.css
│   └── js/
├── docker-compose.yml   # PostgreSQL + приложение
├── Dockerfile
└── requirements.txt
```

## API

### Аутентификация

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/auth/register` | Регистрация |
| POST | `/api/auth/login` | Вход |
| GET | `/api/auth/me` | Текущий пользователь |
| PATCH | `/api/auth/me` | Обновить профиль |
| GET | `/api/auth/me/stats` | Статистика заметок |

Все эндпоинты заметок требуют заголовок `Authorization: Bearer <token>`.

### Заметки

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/notes` | Список заметок |
| GET | `/api/notes/{id}` | Одна заметка |
| POST | `/api/notes` | Создать |
| PATCH | `/api/notes/{id}` | Обновить |
| DELETE | `/api/notes/{id}` | Удалить |

## Локальная разработка

```bash
# Запустить только PostgreSQL
docker compose up -d postgres

# Настроить окружение
cp .env.example .env

# Установить зависимости
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Запустить приложение
uvicorn app.main:app --reload
```

## Переменные окружения

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `DATABASE_URL` | `postgresql://notes:notes@localhost:5432/notes` | URL PostgreSQL |
| `SECRET_KEY` | *(dev-значение)* | Секрет для JWT — **обязательно смените в продакшене** |

Сгенерировать секрет:

```bash
openssl rand -hex 32
```

## Технологии

- [FastAPI](https://fastapi.tiangolo.com/) — веб-фреймворк
- [SQLAlchemy 2.0](https://www.sqlalchemy.org/) — ORM
- [PostgreSQL 16](https://www.postgresql.org/) — база данных
- [python-jose](https://python-jose.readthedocs.io/) — JWT
- [bcrypt](https://github.com/pyca/bcrypt/) — хеширование паролей
- [Docker Compose](https://docs.docker.com/compose/) — контейнеризация
