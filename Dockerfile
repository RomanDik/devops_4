# Базовый образ Python
FROM python:3.9-slim

# Рабочую директорию
WORKDIR /app

# requirements.txt (для кэширования слоев)
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы
COPY . .

# Открываем порт, который использует приложение
EXPOSE 8181

CMD ["python", "app.py"]