FROM python:3.12-slim

WORKDIR /app

# Install deps first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the AI OS
COPY . .

# Env vars the scripts read. Override these in the Coolify UI —
# never commit real values here.
ENV HUMHUB_USER=aios-bot
ENV HUMHUB_BASE=https://meetup.mentoringba.org

# Default: serve the AI OS dashboard. Override per-task, e.g.
#   docker run ... python3 scripts/verify-connections.py
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
	CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/', timeout=3)"
CMD ["python3", "scripts/dashboard/serve.py"]
