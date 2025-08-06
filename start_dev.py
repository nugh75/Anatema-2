#!/usr/bin/env python3
"""
Script per avviare l'applicazione in modalità sviluppo
Porta: 5001, Database: analisi_mu_dev.db, Debug: Attivo
"""

import os
import sys
import subprocess
from pathlib import Path

def activate_venv():
    """Attiva il virtual environment se esiste"""
    venv_path = Path('/home/nugh75/Git/analisi-mu/.venv')
    
    if venv_path.exists():
        # Percorso all'interprete Python del venv
        python_exe = venv_path / 'bin' / 'python'
        
        if python_exe.exists():
            print(f"🐍 Attivazione virtual environment: {venv_path}")
            # Re-esegui lo script con il Python del venv
            if sys.executable != str(python_exe):
                os.execv(str(python_exe), [str(python_exe)] + sys.argv)
        else:
            print(f"⚠️  Virtual environment trovato ma Python non disponibile: {python_exe}")
    else:
        print("⚠️  Virtual environment non trovato, uso Python di sistema")

def setup_dev_environment():
    """Configura l'ambiente di sviluppo"""
    # Percorso del progetto
    project_root = Path('/home/nugh75/Git/analisi-mu')
    
    # Usa cartelle di sviluppo separate per evitare conflitti con Docker
    instance_dir = project_root / 'instance_dev'
    upload_dir = project_root / 'uploads_dev'
    
    # Crea le cartelle con permessi corretti (di proprietà di nugh75)
    instance_dir.mkdir(mode=0o755, exist_ok=True)
    upload_dir.mkdir(mode=0o755, exist_ok=True)
    
    # Percorso database di sviluppo nella cartella dedicata
    dev_db_path = instance_dir / 'analisi_mu_dev.db'
    
    # Controlla se il database di sviluppo esiste già
    if dev_db_path.exists():
        try:
            # Verifica se è accessibile in scrittura
            with open(dev_db_path, 'a') as f:
                pass
            print(f"✅ Database di sviluppo esistente: {dev_db_path}")
        except PermissionError:
            # Se non è accessibile, prova a sistemare i permessi
            print(f"🔧 Sistemando permessi database: {dev_db_path}")
            try:
                import stat
                dev_db_path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            except:
                # Se non riesce, rimuovi e ricrea
                print(f"🗑️ Rimuovendo database con permessi errati...")
                dev_db_path.unlink()
    
    # Se il database di sviluppo non esiste, crealo
    if not dev_db_path.exists():
        # Cerca il database principale nella cartella instance originale
        main_db_path = project_root / 'instance' / 'analisi_mu.db'
        if main_db_path.exists():
            print(f"📋 Copiando database principale da {main_db_path} in {dev_db_path}")
            import shutil
            try:
                shutil.copy2(main_db_path, dev_db_path)
                # Imposta permessi corretti
                import stat
                dev_db_path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
                print(f"✅ Database copiato con successo!")
            except PermissionError as e:
                print(f"❌ Errore copia database: {e}")
                print("🆕 Creando database vuoto invece...")
                # Crea un file vuoto che SQLite può inizializzare
                dev_db_path.touch()
                dev_db_path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        else:
            print(f"🆕 Creando nuovo database di sviluppo: {dev_db_path}")
            print(f"⚠️  Database principale non trovato in {main_db_path}")
            # Crea un file vuoto che SQLite può inizializzare
            dev_db_path.touch()
            import stat
            dev_db_path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    
    return f'sqlite:///{dev_db_path}'

def main():
    """Avvia l'applicazione in modalità sviluppo"""
    
    # Attiva il virtual environment se disponibile
    activate_venv()
    
    # Configura l'ambiente di sviluppo
    database_url = setup_dev_environment()
    
    # Configurazione ambiente sviluppo
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    os.environ['DATABASE_URL'] = database_url
    os.environ['SECRET_KEY'] = 'dev-secret-key-for-development-only'
    os.environ['UPLOAD_FOLDER'] = 'uploads_dev'  # Usa cartella di sviluppo
    
    print("🚀 Avvio Anatema in modalità SVILUPPO")
    print(f"📊 Database: {database_url}")
    print("🌐 Porta: 5001")
    print("🐛 Debug: Attivo")
    print("📁 Upload: uploads_dev/")
    print("=" * 50)
    
    # Importa l'app dopo aver configurato l'ambiente
    from app import create_app
    
    # Crea e avvia l'app
    app = create_app()
    
    try:
        app.run(
            host='127.0.0.1',
            port=5001,
            debug=True,
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\n👋 Spegnimento applicazione...")
    except Exception as e:
        print(f"❌ Errore durante l'avvio: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
