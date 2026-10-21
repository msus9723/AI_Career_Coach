FROM python:3.12-slim

WORKDIR /ui

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8501

# --server.address=0.0.0.0 makes Streamlit reachable from outside the container.
# Usage stats are turned off so the container doesn't phone home.
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--browser.gatherUsageStats=false"]
