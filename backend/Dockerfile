FROM python:3.9
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY scripts/getTracks.py scripts/
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]