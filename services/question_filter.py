"""
Servizio per la classificazione automatica delle domande e filtro dell'annotazione
"""

import sys
import os

# Importa il classificatore esistente
from question_classifier import QuestionClassifier, QuestionType

from models import db, TextCell

class QuestionFilterService:
    """
    Servizio per filtrare automaticamente le domande che necessitano di annotazione
    """
    
    def __init__(self):
        self.classifier = QuestionClassifier()
    
    def classify_and_update_cell(self, text_cell, question_text=None):
        """
        Classifica una TextCell e aggiorna i suoi metadati
        
        Args:
            text_cell: Oggetto TextCell dal database
            question_text: Testo della domanda (opzionale, usa column_name se non fornito)
        
        Returns:
            tuple: (question_type, confidence, is_annotatable)
        """
        # Usa il nome della colonna come domanda se non fornito
        if question_text is None:
            question_text = text_cell.column_name or ""
        
        # Classifica la domanda
        question_type, confidence = self.classifier.classify_question(
            question_text, 
            text_cell.text_content
        )
        
        # Determina se è annotabile
        is_annotatable = self.classifier.should_annotate(
            question_text, 
            text_cell.text_content
        )
        
        # Aggiorna il database
        text_cell.question_type = question_type.value
        text_cell.classification_confidence = confidence
        text_cell.is_annotatable = is_annotatable
        
        return question_type, confidence, is_annotatable
    
    def classify_multiple_cells(self, text_cells, question_texts=None):
        """
        Classifica multiple TextCell in batch
        
        Args:
            text_cells: Lista di oggetti TextCell
            question_texts: Lista di testi domanda (opzionale)
        
        Returns:
            dict: Risultati della classificazione per ogni cella
        """
        results = {}
        
        for i, text_cell in enumerate(text_cells):
            question_text = None
            if question_texts and i < len(question_texts):
                question_text = question_texts[i]
            
            try:
                question_type, confidence, is_annotatable = self.classify_and_update_cell(
                    text_cell, question_text
                )
                
                results[text_cell.id] = {
                    'question_type': question_type.value,
                    'confidence': confidence,
                    'is_annotatable': is_annotatable,
                    'status': 'success'
                }
                
            except Exception as e:
                results[text_cell.id] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return results
    
    def get_annotatable_cells(self, excel_file_id=None, min_confidence=0.7):
        """
        Ottiene tutte le celle che possono essere annotate
        
        Args:
            excel_file_id: ID del file Excel (opzionale, altrimenti tutti i file)
            min_confidence: Confidenza minima per considerare la classificazione affidabile
        
        Returns:
            query: Query SQLAlchemy per le celle annotabili
        """
        query = TextCell.query.filter(
            TextCell.is_annotatable == True
        )
        
        if excel_file_id:
            query = query.filter(TextCell.excel_file_id == excel_file_id)
        
        if min_confidence:
            query = query.filter(
                db.or_(
                    TextCell.classification_confidence >= min_confidence,
                    TextCell.classification_confidence.is_(None)  # Include celle non ancora classificate
                )
            )
        
        return query
    
    def get_classification_stats(self, excel_file_id=None):
        """
        Ottiene statistiche sulla classificazione delle domande
        
        Args:
            excel_file_id: ID del file Excel (opzionale)
        
        Returns:
            dict: Statistiche di classificazione
        """
        query = TextCell.query
        
        if excel_file_id:
            query = query.filter(TextCell.excel_file_id == excel_file_id)
        
        # Conta per tipo di domanda
        stats = {
            'total_cells': query.count(),
            'annotatable': query.filter(TextCell.is_annotatable == True).count(),
            'non_annotatable': query.filter(TextCell.is_annotatable == False).count(),
            'not_classified': query.filter(TextCell.question_type.is_(None)).count(),
            'by_type': {}
        }
        
        # Conta per ogni tipo di domanda
        for question_type in QuestionType:
            count = query.filter(TextCell.question_type == question_type.value).count()
            stats['by_type'][question_type.value] = count
        
        return stats
    
    def reclassify_all_cells(self, excel_file_id=None, force=False):
        """
        Riclassifica tutte le celle di un file o tutti i file
        
        Args:
            excel_file_id: ID del file Excel (opzionale)
            force: Se True, riclassifica anche le celle già classificate
        
        Returns:
            dict: Risultati della riclassificazione
        """
        from app import create_app
        from models import db
        
        app = create_app()
        
        with app.app_context():
            query = TextCell.query
            
            if excel_file_id:
                query = query.filter(TextCell.excel_file_id == excel_file_id)
            
            if not force:
                query = query.filter(TextCell.question_type.is_(None))
            
            cells = query.all()
            
            print(f"Riclassificando {len(cells)} celle...")
            
            results = self.classify_multiple_cells(cells)
            
            # Salva le modifiche
            try:
                db.session.commit()
                print("✓ Classificazione completata e salvata nel database")
            except Exception as e:
                db.session.rollback()
                print(f"✗ Errore nel salvare la classificazione: {e}")
                raise
                
            return results
