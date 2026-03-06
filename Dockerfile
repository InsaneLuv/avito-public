FROM python:3.14-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Копируем файлы зависимостей первыми для кэширования слоёв
COPY pyproject.toml uv.lock* ./

# Устанавливаем зависимости
RUN uv sync --frozen

# Копируем исходный код
COPY . .

EXPOSE 8000

# Переменные окружения по умолчанию (переопределяются при запуске)
ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]