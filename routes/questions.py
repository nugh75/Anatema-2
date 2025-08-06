#!/usr/bin/env python3
"""
Route per la gestione e classificazione manuale delle domande
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required
from models import db, TextCell
from sqlalchemy import func, distinct
import json

questions_bp = Blueprint('questions', __name__, url_prefix='/questions')

@questions_bp.route('/manage')
@login_required
def manage_questions():
    """Pagina di gestione e classificazione delle domande"""
    
    # Prima ottieni i dati sui file Excel
    from models import ExcelFile
    
    # Ottieni tutte le domande raggruppate per file
    files_with_questions = db.session.query(
        ExcelFile.id.label('file_id'),
        ExcelFile.filename.label('filename'),
        ExcelFile.uploaded_at.label('uploaded_at'),
        TextCell.column_name,
        func.count(TextCell.id).label('total_cells'),
        func.count(TextCell.question_type).label('classified_cells'),
        func.group_concat(distinct(TextCell.question_type)).label('types_used')
    ).join(TextCell, ExcelFile.id == TextCell.excel_file_id)\
     .group_by(ExcelFile.id, TextCell.column_name)\
     .order_by(ExcelFile.filename, TextCell.column_name).all()
    
    # Raggruppa per file
    files_data = {}
    total_questions = 0
    total_classified = 0
    
    for row in files_with_questions:
        file_id = row.file_id
        if file_id not in files_data:
            files_data[file_id] = {
                'file_id': file_id,
                'filename': row.filename,
                'uploaded_at': row.uploaded_at,
                'questions': [],
                'total_questions': 0,
                'classified_questions': 0
            }
        
        # Crea oggetto domanda
        question = {
            'column_name': row.column_name,
            'total_cells': row.total_cells,
            'classified_cells': row.classified_cells,
            'types_used': row.types_used
        }
        
        files_data[file_id]['questions'].append(question)
        files_data[file_id]['total_questions'] += 1
        total_questions += 1
        
        if row.classified_cells > 0:
            files_data[file_id]['classified_questions'] += 1
            total_classified += 1
    
    # Converti in lista ordinata
    files_list = list(files_data.values())
    
    # Tipi di domanda disponibili
    question_types = [
        ('aperta', '🔓 Domanda Aperta', 'Domande che richiedono risposte elaborate'),
        ('anagrafica', '👤 Anagrafica', 'Dati personali (età, genere, etc.)'),
        ('chiusa_binaria', '✅ Sì/No', 'Domande con risposta binaria'),
        ('chiusa_multipla', '☑️ Scelta Multipla', 'Selezione da opzioni predefinite'),
        ('likert', '📊 Scala Likert', 'Scale di valutazione numeriche'),
        ('numerica', '🔢 Numerica', 'Valori numerici o quantitativi'),
    ]
    
    return render_template('questions/manage.html',
                         files=files_list,
                         question_types=question_types,
                         total_questions=total_questions,
                         total_classified=total_classified)

@questions_bp.route('/classify', methods=['POST'])
@login_required
def classify_question():
    """Classifica una domanda specifica"""
    
    try:
        data = request.get_json()
        column_name = data.get('column_name')
        question_type = data.get('question_type')
        
        if not column_name or not question_type:
            return jsonify({'success': False, 'message': 'Parametri mancanti'})
        
        # Aggiorna tutte le celle con questa domanda
        updated_count = db.session.query(TextCell)\
            .filter_by(column_name=column_name)\
            .update({'question_type': question_type})
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Classificate {updated_count} celle per la domanda "{column_name}"'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Errore: {str(e)}'})

@questions_bp.route('/bulk_classify', methods=['POST'])
@login_required
def bulk_classify():
    """Classificazione di massa basata su selezione multiple"""
    
    try:
        data = request.get_json()
        question_names = data.get('question_names', [])  # Lista di nomi domande selezionate
        question_type = data.get('question_type')
        
        if not question_names or not question_type:
            return jsonify({'success': False, 'message': 'Parametri mancanti'})
        
        total_updated = 0
        
        # Aggiorna tutte le celle per le domande selezionate
        for question_name in question_names:
            updated_count = db.session.query(TextCell)\
                .filter_by(column_name=question_name)\
                .update({'question_type': question_type})
            total_updated += updated_count
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Classificate {total_updated} celle per {len(question_names)} domande come "{question_type}"',
            'total_cells': total_updated,
            'total_questions': len(question_names)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Errore: {str(e)}'})

@questions_bp.route('/bulk_reset', methods=['POST'])
@login_required
def bulk_reset():
    """Reset di massa della classificazione"""
    
    try:
        data = request.get_json()
        question_names = data.get('question_names', [])
        
        if not question_names:
            return jsonify({'success': False, 'message': 'Nessuna domanda selezionata'})
        
        total_updated = 0
        
        for question_name in question_names:
            updated_count = db.session.query(TextCell)\
                .filter_by(column_name=question_name)\
                .update({'question_type': None})
            total_updated += updated_count
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Reset completato per {total_updated} celle di {len(question_names)} domande',
            'total_cells': total_updated,
            'total_questions': len(question_names)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Errore: {str(e)}'})

@questions_bp.route('/auto_suggest', methods=['POST'])
@login_required
def auto_suggest():
    """Suggerimenti automatici per classificazione intelligente"""
    
    try:
        data = request.get_json()
        question_names = data.get('question_names', [])
        
        if not question_names:
            return jsonify({'success': False, 'message': 'Nessuna domanda selezionata'})
        
        suggestions = []
        
        for question_name in question_names:
            question_lower = question_name.lower()
            suggested_type = None
            confidence = 0.0
            
            # Regole euristiche per suggerimenti
            if any(word in question_lower for word in ['età', 'anno', 'nascita', 'data nascita']):
                suggested_type = 'anagrafica'
                confidence = 0.9
            elif any(word in question_lower for word in ['genere', 'sesso', 'maschio', 'femmina']):
                suggested_type = 'anagrafica'
                confidence = 0.85
            elif any(word in question_lower for word in ['nome', 'cognome', 'email', 'telefono']):
                suggested_type = 'anagrafica'
                confidence = 0.8
            elif any(word in question_lower for word in ['scala', 'valut', 'punteggio', '1-10', '1-5']):
                suggested_type = 'likert'
                confidence = 0.8
            elif any(word in question_lower for word in ['sì', 'no', 'si/no', 'vero', 'falso']):
                suggested_type = 'chiusa_binaria'
                confidence = 0.85
            elif any(word in question_lower for word in ['scelta', 'opzione', 'seleziona', 'a)', 'b)', 'c)']):
                suggested_type = 'chiusa_multipla'
                confidence = 0.75
            elif any(word in question_lower for word in ['numero', 'quantità', 'euro', 'prezzo', 'costo']):
                suggested_type = 'numerica'
                confidence = 0.7
            else:
                suggested_type = 'aperta'
                confidence = 0.6
            
            suggestions.append({
                'question_name': question_name,
                'suggested_type': suggested_type,
                'confidence': confidence
            })
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Errore: {str(e)}'})
