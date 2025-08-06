# 🚀 Guida per l'Avvio in Ambienti Multipli

Questo progetto supporta due modalità di avvio separate per evitare conflitti tra sviluppo locale e container Docker.

## 📋 Modalità Disponibili

### 🔧 Modalità Sviluppo (Locale)
- **Porta**: 5001
- **Database**: `analisi_mu_dev.db` (nella root del progetto)
- **Debug**: Attivo
- **Hot Reload**: Attivo

### 🐳 Modalità Docker/Produzione
- **Porta**: 5000
- **Database**: `instance/analisi_mu.db`
- **Debug**: Disattivo
- **Ottimizzato**: Per produzione

## 🎯 Come Avviare

### Sviluppo Locale
```bash
# Metodo 1: Script Python
python start_dev.py

# Metodo 2: Script eseguibile
./start_dev.py

# Metodo 3: Con file .env
python -m pip install python-dotenv
python -c "from dotenv import load_dotenv; load_dotenv('.env.dev'); from app import create_app; create_app().run(port=5001, debug=True)"
```

### Docker/Produzione
```bash
# Metodo 1: Script Python
python start_docker.py

# Metodo 2: Script eseguibile
./start_docker.py

# Metodo 3: Container Docker (come prima)
docker-compose up
```

## 🗄️ Database

### Sviluppo
- Il database di sviluppo (`analisi_mu_dev.db`) viene creato automaticamente nella root
- È separato dal database di produzione per evitare conflitti
- Usa lo script `create_dev_db.py` per inizializzare i dati

### Produzione
- Usa il database esistente in `instance/analisi_mu.db`
- Non viene modificato durante lo sviluppo locale

## 🔧 Configurazione

### File di Configurazione
- `.env.dev` - Configurazioni per sviluppo
- `.env.docker` - Configurazioni per Docker

### Variabili d'Ambiente Supportate
- `FLASK_ENV` - Ambiente Flask (`development`/`production`)
- `FLASK_DEBUG` - Debug mode (`1`/`0`)
- `DATABASE_URL` - URL del database
- `SECRET_KEY` - Chiave segreta Flask
- `DEV_MODE` - Modalità sviluppo (`1` per attivo)
- `DOCKER_MODE` - Modalità Docker (`1` per attivo)

## 🌐 URL di Accesso

### Sviluppo
```
http://localhost:5001
```

### Docker/Produzione
```
http://localhost:5000
```

## 🚦 Verifica Status

Controlla quale modalità è attiva guardando i log di avvio:
- `🔧 Modalità sviluppo attivata` → Sviluppo locale
- `🐳 Modalità Docker attivata` → Docker/Produzione

## 🔄 Switch tra Modalità

Per passare da una modalità all'altra:

1. **Ferma il server attuale** (Ctrl+C)
2. **Avvia nella nuova modalità**:
   - Per sviluppo: `python start_dev.py`
   - Per Docker: `python start_docker.py`

## 🛠️ Troubleshooting

### Porta già in uso
Se vedi errori di porta occupata:
- Sviluppo: La porta 5001 è libera
- Docker: Ferma eventuali container: `docker-compose down`

### Database non trovato
- Sviluppo: Esegui `python create_dev_db.py`
- Docker: Verifica che `instance/analisi_mu.db` esista

### Permessi file
```bash
chmod +x start_dev.py start_docker.py
```
