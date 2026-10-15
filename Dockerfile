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

# Default: run the connection verifier. Override per-task, e.g.
#   docker run ... python3 scripts/verify-connections.py
CMD ["python3", "scripts/verify-connections.py"]
