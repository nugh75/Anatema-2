#!/bin/bash
# Script di inizializzazione per permessi Docker

echo "🔧 Inizializzazione permessi Docker..."

# Mostra informazioni utente corrente
echo "👤 Utente corrente: $(whoami) (UID: $(id -u), GID: $(id -g))"

# Assicura che le directory esistano e abbiano i permessi corretti
mkdir -p /app/instance /app/uploads /app/backups

# Prova a cambiare ownership se necessario e possibile
echo "🔄 Tentativo di correzione ownership delle directory montate..."
chown -R $(id -u):$(id -g) /app/instance /app/uploads /app/backups 2>/dev/null || {
    echo "⚠️  Non è possibile cambiare ownership, useremo solo chmod"
}

# Funzione per verificare e correggere i permessi
fix_permissions() {
    local path=$1
    local type=$2
    
    echo "🔍 Verificando permessi per $path..."
    
    if [ "$type" = "dir" ]; then
        if [ -w "$path" ]; then
            echo "✅ Directory $path scrivibile"
        else
            echo "❌ Directory $path non scrivibile, applicando fix..."
            chmod 777 "$path" 2>/dev/null || {
                echo "⚠️  Impossibile modificare permessi di $path, continuando..."
            }
        fi
    elif [ "$type" = "file" ]; then
        if [ -w "$path" ]; then
            echo "✅ File $path scrivibile"
        else
            echo "❌ File $path non scrivibile, applicando fix..."
            chmod 666 "$path" 2>/dev/null || {
                echo "⚠️  Impossibile modificare permessi di $path, continuando..."
            }
        fi
    fi
}

# Fix permessi per le directory
fix_permissions "/app/instance" "dir"
fix_permissions "/app/uploads" "dir"
fix_permissions "/app/backups" "dir"

# Fix permessi per il database se esiste
if [ -f /app/instance/analisi_mu.db ]; then
    fix_permissions "/app/instance/analisi_mu.db" "file"
    echo "📊 Permessi database correnti: $(ls -la /app/instance/analisi_mu.db)"
else
    echo "⚠️  Database non trovato in /app/instance/analisi_mu.db"
fi

# Fix permessi per tutti i file backup se esistono
for backup_file in /app/instance/*.backup* /app/backups/*.db; do
    if [ -f "$backup_file" ]; then
        fix_permissions "$backup_file" "file"
    fi
done

# Test scrittura database
echo "🧪 Test scrittura database..."
if [ -f /app/instance/analisi_mu.db ]; then
    if touch /app/instance/test_write.tmp 2>/dev/null; then
        rm -f /app/instance/test_write.tmp
        echo "✅ Directory instance scrivibile"
    else
        echo "❌ Directory instance NON scrivibile"
    fi
    
    # Test specifico per il database
    if echo "test" > /app/instance/analisi_mu.db.test 2>/dev/null; then
        rm -f /app/instance/analisi_mu.db.test
        echo "✅ Posso creare file nella directory del database"
    else
        echo "❌ NON posso creare file nella directory del database"
    fi
fi

# Verifica finale
echo "🧪 Verifica finale dei permessi..."
if [ -w /app/instance ] && ( [ ! -f /app/instance/analisi_mu.db ] || [ -w /app/instance/analisi_mu.db ] ); then
    echo "✅ Tutti i permessi configurati correttamente"
else
    echo "⚠️  Alcuni permessi potrebbero non essere configurati correttamente"
    echo "   Controllare i log per ulteriori dettagli"
fi

echo "🚀 Avvio applicazione Flask..."
exec python app.py
