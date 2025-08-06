FROM python:3.13-slim

# Imposta la directory di lavoro
WORKDIR /app

# Installa le dipendenze di sistema
RUN apt-get update && apt-get install -y \
    curl \
    git \
    gcc \
    g++ \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Crea utente non-root per sicurezza con UID/GID specifici
RUN groupadd -r appuser --gid=1000 && useradd -r -g appuser --uid=1000 --create-home --shell /bin/bash appuser

# Copia i file dei requisiti
COPY requirements.txt .

# Installa le dipendenze Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copia il codice dell'applicazione
COPY . .

# Crea le directory necessarie con permessi corretti
RUN mkdir -p uploads instance backups \
    && chown -R appuser:appuser /app \
    && chmod -R 755 /app \
    && chmod -R 777 uploads instance backups

# Assicura che lo script di init abbia i permessi di esecuzione
RUN chmod +x /app/docker-init.sh

# Cambia all'utente non-root
USER appuser

# Imposta le variabili d'ambiente
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:////app/instance/analisi_mu.db

# Espone la porta 5016
EXPOSE 5016

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5016/ || exit 1

# Comando per avviare l'applicazione con script di init
CMD ["/app/docker-init.sh"]
