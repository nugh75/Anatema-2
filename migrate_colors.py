#!/usr/bin/env python3
"""
Script di migrazione per assegnare colori univoci alle categorie esistenti
e aggiornare i colori delle etichette in base alla loro categoria.

Questo script:
1. Assegna colori univoci dalla palette a tutte le categorie esistenti
2. Aggiorna le etichette per ereditare il colore della loro categoria
3. Preserva i colori personalizzati delle etichette (se diversi dal default grigio)
"""

import sys
import os

# Aggiungi il percorso del progetto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Category, Label
from utils.color_palette import ColorPalette

def migrate_category_colors():
    """Migrazione principale per i colori delle categorie"""
    
    app = create_app()
    with app.app_context():
        print("🎨 Avvio migrazione colori categorie...")
        
        # Statistiche iniziali
        total_categories = Category.query.filter_by(is_active=True).count()
        total_labels = Label.query.filter_by(is_active=True).count()
        
        print(f"📊 Trovate {total_categories} categorie attive")
        print(f"📊 Trovate {total_labels} etichette attive")
        
        if total_categories == 0:
            print("⚠️  Nessuna categoria attiva trovata. Migrazione annullata.")
            return
        
        # Conta categorie che già hanno un colore personalizzato
        categories_with_colors = Category.query.filter(
            Category.is_active == True,
            Category.color.isnot(None),
            Category.color != '#6c757d'  # colore default grigio
        ).count()
        
        print(f"🎯 {categories_with_colors} categorie hanno già un colore personalizzato")
        
        # Conferma dall'utente
        if input(f"\n❓ Vuoi procedere con la migrazione? (s/N): ").lower() != 's':
            print("❌ Migrazione annullata dall'utente.")
            return
        
        try:
            # FASE 1: Assegna colori univoci alle categorie
            print("\n🔄 FASE 1: Assegnazione colori categorie...")
            
            categories = Category.query.filter_by(is_active=True).order_by(Category.id).all()
            updated_categories = 0
            
            for i, category in enumerate(categories):
                # Se la categoria non ha un colore o ha il colore default
                if not category.color or category.color == '#6c757d':
                    # Assegna il prossimo colore dalla palette
                    new_color = ColorPalette.get_color_by_index(i)
                    category.color = new_color
                    updated_categories += 1
                    print(f"  ✅ {category.name}: {new_color}")
                else:
                    print(f"  ⏭️  {category.name}: mantiene {category.color}")
            
            # FASE 2: Aggiorna etichette per ereditare i colori delle categorie
            print(f"\n🔄 FASE 2: Aggiornamento colori etichette...")
            
            updated_labels = 0
            preserved_labels = 0
            
            for category in categories:
                category_labels = Label.query.filter_by(
                    category_id=category.id, 
                    is_active=True
                ).all()
                
                for label in category_labels:
                    # Se l'etichetta ha il colore default o nessun colore
                    if not label.color or label.color == '#6c757d':
                        label.color = category.color
                        updated_labels += 1
                    else:
                        # Mantieni colori personalizzati esistenti
                        preserved_labels += 1
            
            # FASE 3: Gestisci etichette senza categoria
            print(f"\n🔄 FASE 3: Gestione etichette senza categoria...")
            
            uncategorized_labels = Label.query.filter(
                Label.category_id.is_(None),
                Label.is_active == True
            ).all()
            
            uncategorized_updated = 0
            for label in uncategorized_labels:
                if not label.color or label.color == '#6c757d':
                    label.color = '#6c757d'  # mantieni grigio per etichette senza categoria
                    uncategorized_updated += 1
            
            # Commit delle modifiche
            db.session.commit()
            
            # Statistiche finali
            print(f"\n✅ MIGRAZIONE COMPLETATA!")
            print(f"📈 Categorie aggiornate: {updated_categories}/{total_categories}")
            print(f"📈 Etichette aggiornate: {updated_labels}")
            print(f"🔒 Etichette con colore preservato: {preserved_labels}")
            print(f"📋 Etichette senza categoria gestite: {uncategorized_updated}")
            
            # Verifica finale
            print(f"\n🔍 VERIFICA FINALE:")
            
            # Controlla che ogni categoria attiva abbia un colore
            categories_without_color = Category.query.filter(
                Category.is_active == True,
                Category.color.is_(None)
            ).count()
            
            if categories_without_color == 0:
                print(f"✅ Tutte le categorie hanno un colore assegnato")
            else:
                print(f"⚠️  {categories_without_color} categorie ancora senza colore!")
            
            # Mostra distribuzione colori
            color_counts = {}
            for category in Category.query.filter_by(is_active=True).all():
                color = category.color or 'None'
                color_counts[color] = color_counts.get(color, 0) + 1
            
            print(f"🎨 Distribuzione colori:")
            for color, count in color_counts.items():
                if count > 1 and color != '#6c757d':
                    print(f"  ⚠️  {color}: {count} categorie (duplicato!)")
                else:
                    print(f"  ✅ {color}: {count} categoria/e")
                    
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERRORE durante la migrazione: {str(e)}")
            print("💾 Tutte le modifiche sono state annullate.")
            return False
        
        print(f"\n🎉 Migrazione completata con successo!")
        return True

def show_color_preview():
    """Mostra un'anteprima dei colori della palette"""
    
    print("🎨 ANTEPRIMA PALETTE COLORI:")
    print("=" * 50)
    
    for i in range(min(30, 15)):  # mostra primi 15 colori
        color = ColorPalette.get_color_by_index(i)
        hsl = ColorPalette.hex_to_hsl(color)
        text_color = ColorPalette.get_contrasting_text_color(color)
        
        # Simula l'anteprima con caratteri
        preview = f"██████ {color} ██████"
        print(f"{i+1:2d}. {preview} HSL({hsl[0]:.0f}°, {hsl[1]*100:.0f}%, {hsl[2]*100:.0f}%)")
    
    if ColorPalette.DEFAULT_COLORS.__len__() > 15:
        print(f"... e altri {len(ColorPalette.DEFAULT_COLORS) - 15} colori disponibili")

def verify_current_state():
    """Verifica lo stato attuale dei colori nel database"""
    
    app = create_app()
    with app.app_context():
        print("🔍 STATO ATTUALE COLORI:")
        print("=" * 50)
        
        # Categorie
        categories = Category.query.filter_by(is_active=True).all()
        print(f"📂 CATEGORIE ({len(categories)}):")
        
        for category in categories:
            color = category.color or 'None'
            label_count = Label.query.filter_by(category_id=category.id, is_active=True).count()
            print(f"  • {category.name}: {color} ({label_count} etichette)")
        
        # Etichette senza categoria
        uncategorized = Label.query.filter(
            Label.category_id.is_(None),
            Label.is_active == True
        ).count()
        
        if uncategorized > 0:
            print(f"\n📋 ETICHETTE SENZA CATEGORIA: {uncategorized}")
        
        # Controlla duplicati colori
        color_counts = {}
        for category in categories:
            color = category.color or 'None'
            if color in color_counts:
                color_counts[color].append(category.name)
            else:
                color_counts[color] = [category.name]
        
        duplicates = {color: names for color, names in color_counts.items() 
                     if len(names) > 1 and color != '#6c757d'}
        
        if duplicates:
            print(f"\n⚠️  COLORI DUPLICATI:")
            for color, names in duplicates.items():
                print(f"  {color}: {', '.join(names)}")
        else:
            print(f"\n✅ Nessun colore duplicato trovato")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrazione colori categorie')
    parser.add_argument('--preview', action='store_true', 
                       help='Mostra anteprima della palette colori')
    parser.add_argument('--verify', action='store_true', 
                       help='Verifica lo stato attuale dei colori')
    parser.add_argument('--migrate', action='store_true', 
                       help='Esegui la migrazione')
    
    args = parser.parse_args()
    
    if args.preview:
        show_color_preview()
    elif args.verify:
        verify_current_state()
    elif args.migrate:
        migrate_category_colors()
    else:
        print("🎨 MIGRAZIONE COLORI CATEGORIE")
        print("=" * 40)
        print()
        print("Opzioni disponibili:")
        print("  --preview    Anteprima palette colori")
        print("  --verify     Verifica stato attuale")
        print("  --migrate    Esegui migrazione")
        print()
        print("Esempi:")
        print("  python migrate_colors.py --preview")
        print("  python migrate_colors.py --verify")
        print("  python migrate_colors.py --migrate")
