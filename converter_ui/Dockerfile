FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3000

# We run from the parent directory of 'app' to ensure module imports work
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]
