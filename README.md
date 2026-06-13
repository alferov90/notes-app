# DayFlow

Система **режима дня** с Telegram-уведомлениями. Дизайн в стиле Apple.

## Возможности

- Расписание событий на день (подъём, еда, работа, спорт, сон…)
- Повторение: каждый день или выбранные дни недели
- Уведомление в Telegram **в момент каждого события**
- Личный кабинет, регистрация, PostgreSQL, Docker

## Быстрый старт

```bash
docker compose up -d --build
```

| Страница | URL |
|----------|-----|
| Главная | http://localhost:8000 |
| Расписание | http://localhost:8000/app |
| Кабинет + Telegram | http://localhost:8000/dashboard |

## Настройка Telegram

В `.env`:

```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_BOT_USERNAME=YourBot
APP_TIMEZONE=Europe/Moscow
TELEGRAM_PROXY_URL=   # если api.telegram.org недоступен
```

1. Создайте бота в [@BotFather](https://t.me/BotFather)
2. В кабинете нажмите «Подключить Telegram» → Start
3. Заполните расписание в `/app`

## API

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/events` | Список событий |
| POST | `/api/events` | Создать событие |
| PATCH | `/api/events/{id}` | Изменить |
| DELETE | `/api/events/{id}` | Удалить |

## Деплой на сервер

```bash
git pull
docker compose up -d --build
```

После обновления с версии заметок таблица `routine_events` создаётся автоматически.
