FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir streamlit requests

COPY app.py .

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1:8501/ || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
