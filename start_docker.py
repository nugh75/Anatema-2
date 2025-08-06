#!/usr/bin/env python3
"""
Script di avvio per l'ambiente Docker/Produzione.
Mantiene la configurazione originale.
"""

import os
import sys
from app import create_app

def main():
    """Avvia l'applicazione in modalità Docker/Produzione"""
    
    # Configurazione ambiente Docker/Produzione
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = '0'
    # Usa il database di default (analisi_mu.db)
    if 'DATABASE_URL' not in os.environ:
        os.environ['DATABASE_URL'] = 'sqlite:///instance/analisi_mu.db'
    
    # Configurazioni specifiche per Docker
    os.environ['DOCKER_MODE'] = '1'
    os.environ['DOCKER_PORT'] = '5016'
    
    print("🐳 Avvio in modalità DOCKER/PRODUZIONE")
    print("📍 Porta: 5016")
    print("🗄️  Database: instance/analisi_mu.db")
    print("🔧 Debug: DISATTIVO")
    print("=" * 50)
    
    # Crea l'app
    app = create_app()
    
    # Avvia il server
    try:
        app.run(
            host='0.0.0.0',
            port=5016,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Server arrestato dall'utente")
    except Exception as e:
        print(f"❌ Errore durante l'avvio: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
