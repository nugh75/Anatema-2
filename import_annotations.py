#!/usr/bin/env python3
"""
Script per importare le tabelle di annotazione mancanti dal database di produzione
"""

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

def import_annotations():
    """Importa le tabelle di annotazione da produzione"""
    
    # Percorsi dei database
    project_root = Path('/home/nugh75/Git/analisi-mu')
    prod_db = project_root / 'instance' / 'analisi_mu.db'
    dev_db = project_root / 'instance_dev' / 'analisi_mu_dev.db'
    
    print("🔄 Importo le tabelle di annotazione da produzione → sviluppo")
    print(f"📊 Database produzione: {prod_db}")
    print(f"🛠️  Database sviluppo: {dev_db}")
    
    # Backup del database di sviluppo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = dev_db.with_suffix(f'.backup_annotations_{timestamp}.db')
    print(f"💾 Creando backup: {backup_path}")
    shutil.copy2(dev_db, backup_path)
    
    try:
        # Connessioni ai database
        prod_conn = sqlite3.connect(prod_db)
        dev_conn = sqlite3.connect(dev_db)
        
        # Tabelle di annotazione da importare
        annotation_tables = [
            'cell_annotation',
            'text_annotations', 
            'annotation_action'
        ]
        
        print(f"📋 Tabelle di annotazione da importare: {', '.join(annotation_tables)}")
        
        # Per ogni tabella di annotazione
        for table in annotation_tables:
            print(f"🔄 Processando tabella: {table}")
            
            # Verifica se la tabella esiste in produzione
            cursor = prod_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
                (table,)
            )
            
            if not cursor.fetchone():
                print(f"⚠️  Tabella {table} non esiste in produzione, salto")
                continue
            
            # Verifica se la tabella esiste in sviluppo
            cursor = dev_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
                (table,)
            )
            
            if cursor.fetchone():
                # La tabella esiste, svuotala
                dev_conn.execute(f"DELETE FROM {table}")
                print(f"   🗑️  Svuotata tabella {table} in sviluppo")
            else:
                # La tabella non esiste, creala copiando la struttura
                print(f"   🏗️  Creando tabella {table} in sviluppo")
                
                # Ottieni lo schema della tabella da produzione
                cursor = prod_conn.execute(
                    f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'"
                )
                create_sql = cursor.fetchone()[0]
                
                # Crea la tabella in sviluppo
                dev_conn.execute(create_sql)
                print(f"   ✅ Tabella {table} creata")
            
            # Copia i dati da produzione
            prod_cursor = prod_conn.execute(f"SELECT * FROM {table}")
            columns = [desc[0] for desc in prod_cursor.description]
            
            rows_copied = 0
            for row in prod_cursor:
                placeholders = ','.join(['?' for _ in columns])
                try:
                    dev_conn.execute(
                        f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
                        row
                    )
                    rows_copied += 1
                except Exception as e:
                    print(f"   ⚠️  Errore inserimento riga in {table}: {e}")
            
            print(f"   ✅ Copiati {rows_copied} record in {table}")
        
        # Commit delle modifiche
        dev_conn.commit()
        print("💾 Commit delle modifiche completato")
        
        # Verifica finale
        print("🔍 Verifica finale delle annotazioni...")
        
        for table in annotation_tables:
            try:
                cursor = dev_conn.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   📊 {table}: {count} record")
            except Exception as e:
                print(f"   ⚠️  Errore nel contare {table}: {e}")
        
        print("✅ Importazione annotazioni completata!")
        print(f"💾 Backup salvato in: {backup_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante l'importazione: {e}")
        
        # Ripristina il backup in caso di errore
        print("🔄 Ripristino backup...")
        shutil.copy2(backup_path, dev_db)
        print("✅ Backup ripristinato")
        
        return False
        
    finally:
        # Chiudi connessioni
        try:
            prod_conn.close()
            dev_conn.close()
        except:
            pass

if __name__ == '__main__':
    success = import_annotations()
    if success:
        print("\n🎉 Importazione annotazioni completata!")
        print("📝 Il database di sviluppo ora contiene tutto il lavoro di etichettamento")
        print("🔄 Riavvia il server: python start_dev.py")
    else:
        print("\n❌ Importazione fallita, controllare gli errori sopra")
