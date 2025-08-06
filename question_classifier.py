#!/usr/bin/env python3
"""
Sistema di classificazione automatica dei tipi di domande per filtrare
solo quelle che necessitano di annotazione (domande aperte).
"""

import re
from typing import List, Dict, Tuple, Optional
from enum import Enum

class QuestionType(Enum):
    """Tipi di domande identificabili"""
    OPEN = "aperta"                    # Domande che richiedono annotazione
    CLOSED_BINARY = "chiusa_binaria"   # Sì/No, Vero/Falso
    CLOSED_MULTIPLE = "chiusa_multipla" # Scelta multipla
    LIKERT = "likert"                  # Scale Likert
    DEMOGRAPHIC = "anagrafica"         # Dati anagrafici
    NUMERIC = "numerica"               # Risposta numerica
    DATE = "data"                      # Date
    SCALE = "scala"                    # Scale numeriche (1-10, etc.)

class QuestionClassifier:
    """Classificatore automatico per tipi di domande"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict[QuestionType, List[Dict]]:
        """Inizializza i pattern per riconoscere i diversi tipi di domande"""
        return {
            QuestionType.CLOSED_BINARY: [
                {
                    'pattern': r'\b(sì|no|si|vero|falso|true|false)\b',
                    'context': ['question', 'response'],
                    'weight': 0.8
                },
                {
                    'pattern': r'\b(d\'accordo|disaccordo|agree|disagree)\b',
                    'context': ['question'],
                    'weight': 0.7
                }
            ],
            
            QuestionType.CLOSED_MULTIPLE: [
                {
                    'pattern': r'\b(a\)|b\)|c\)|d\)|e\)|\d+\))',
                    'context': ['question', 'response'],
                    'weight': 0.9
                },
                {
                    'pattern': r'\b(seleziona|scegli|indica|mark|select|choose)\b.*\b(una|uno|all|alcune)\b',
                    'context': ['question'],
                    'weight': 0.8
                },
                {
                    'pattern': r'\b(opzioni?|alternative|scelte|choices|options)\b',
                    'context': ['question'],
                    'weight': 0.7
                }
            ],
            
            QuestionType.LIKERT: [
                {
                    'pattern': r'\b(molto|abbastanza|poco|per niente|strongly|somewhat|not at all)\b',
                    'context': ['question', 'response'],
                    'weight': 0.8
                },
                {
                    'pattern': r'\b(scala da|from \d+ to \d+|da \d+ a \d+|rate from)\b',
                    'context': ['question'],
                    'weight': 0.9
                },
                {
                    'pattern': r'\b(soddisfatto|insoddisfatto|satisfied|dissatisfied)\b',
                    'context': ['question', 'response'],
                    'weight': 0.7
                }
            ],
            
            QuestionType.DEMOGRAPHIC: [
                {
                    'pattern': r'\b(età|age|anni|years old|nato|born)\b',
                    'context': ['question'],
                    'weight': 0.9
                },
                {
                    'pattern': r'\b(sesso|genere|gender|sex|maschio|femmina|male|female)\b',
                    'context': ['question', 'response'],
                    'weight': 0.9
                },
                {
                    'pattern': r'\b(titolo di studio|education|laurea|diploma|degree)\b',
                    'context': ['question'],
                    'weight': 0.8
                },
                {
                    'pattern': r'\b(professione|lavoro|job|occupation|work)\b',
                    'context': ['question'],
                    'weight': 0.7
                }
            ],
            
            QuestionType.NUMERIC: [
                {
                    'pattern': r'\b(quanti|how many|numero|number|count)\b',
                    'context': ['question'],
                    'weight': 0.8
                },
                {
                    'pattern': r'^\d+$',
                    'context': ['response'],
                    'weight': 0.9
                }
            ],
            
            QuestionType.SCALE: [
                {
                    'pattern': r'\b(da 1 a \d+|from 1 to \d+|scala \d+-\d+|scale \d+-\d+)\b',
                    'context': ['question'],
                    'weight': 0.9
                },
                {
                    'pattern': r'^\d+(/\d+)?$',
                    'context': ['response'],
                    'weight': 0.6
                }
            ]
        }
    
    def classify_question(self, question_text: str, response_text: str = None) -> Tuple[QuestionType, float]:
        """
        Classifica una domanda basandosi sul testo della domanda e opzionalmente della risposta
        
        Args:
            question_text: Testo della domanda
            response_text: Testo della risposta (opzionale)
            
        Returns:
            Tuple con (tipo_domanda, confidenza)
        """
        scores = {qtype: 0.0 for qtype in QuestionType}
        
        # Analizza ogni tipo di domanda
        for question_type, patterns in self.patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info['pattern']
                weight = pattern_info['weight']
                contexts = pattern_info['context']
                
                # Controlla se il pattern si applica al contesto
                if 'question' in contexts and question_text:
                    matches = len(re.findall(pattern, question_text.lower(), re.IGNORECASE))
                    scores[question_type] += matches * weight
                
                if 'response' in contexts and response_text:
                    matches = len(re.findall(pattern, response_text.lower(), re.IGNORECASE))
                    scores[question_type] += matches * weight
        
        # Euristica aggiuntiva per domande aperte
        if self._is_likely_open_question(question_text, response_text):
            scores[QuestionType.OPEN] += 1.0
        
        # Trova il tipo con score più alto
        best_type = max(scores.keys(), key=lambda k: scores[k])
        confidence = scores[best_type]
        
        # Se non c'è un match chiaro, considera come domanda aperta
        if confidence < 0.5:
            return QuestionType.OPEN, 0.5
        
        return best_type, min(confidence, 1.0)
    
    def _is_likely_open_question(self, question_text: str, response_text: str = None) -> bool:
        """Euristica per identificare domande aperte"""
        if not question_text:
            return False
        
        question_lower = question_text.lower()
        
        # Parole chiave che indicano domande aperte
        open_indicators = [
            'descrivi', 'describe', 'spiega', 'explain', 'racconta', 'tell',
            'cosa pensi', 'what do you think', 'opinione', 'opinion',
            'come', 'how', 'perché', 'why', 'in che modo', 'in what way',
            'esperienza', 'experience', 'commenta', 'comment'
        ]
        
        for indicator in open_indicators:
            if indicator in question_lower:
                return True
        
        # Se la risposta è lunga, probabilmente è una domanda aperta
        if response_text and len(response_text.strip()) > 50:
            return True
        
        # Domande che iniziano con parole tipiche delle domande aperte
        open_starters = ['cosa', 'come', 'perché', 'quando', 'dove', 'chi',
                        'what', 'how', 'why', 'when', 'where', 'who']
        
        first_word = question_lower.split()[0] if question_lower.split() else ""
        if first_word in open_starters:
            return True
        
        return False
    
    def should_annotate(self, question_text: str, response_text: str = None) -> bool:
        """
        Determina se una domanda dovrebbe essere annotata
        
        Returns:
            True se la domanda richiede annotazione (è aperta)
        """
        question_type, confidence = self.classify_question(question_text, response_text)
        return question_type == QuestionType.OPEN

def test_classifier():
    """Test del classificatore con esempi"""
    classifier = QuestionClassifier()
    
    test_cases = [
        # Domande aperte (dovrebbero essere annotate)
        ("Descrivi la tua esperienza con l'intelligenza artificiale", "L'IA mi ha aiutato molto nel lavoro quotidiano, specialmente per automatizzare tasks ripetitivi...", True),
        ("Cosa pensi dell'uso dell'IA nell'educazione?", "Penso che sia uno strumento molto utile ma va usato con cautela...", True),
        ("Come utilizzi ChatGPT nel tuo lavoro?", "Lo uso principalmente per brainstorming e per scrivere bozze di documenti", True),
        
        # Domande chiuse (non dovrebbero essere annotate)
        ("Hai mai usato ChatGPT? Sì/No", "Sì", False),
        ("Seleziona una opzione: a) Molto utile b) Abbastanza utile c) Poco utile", "a) Molto utile", False),
        ("Quanto sei soddisfatto dell'IA? (scala 1-10)", "8", False),
        ("Età:", "25", False),
        ("Titolo di studio:", "Laurea", False),
        
        # Casi borderline
        ("Quale strumento di IA preferisci?", "ChatGPT", False),  # Potrebbe essere multipla
        ("Perché usi l'IA?", "Per velocizzare il lavoro e migliorare la produttività nella gestione delle attività quotidiane", True),
    ]
    
    print("=== TEST CLASSIFICATORE DOMANDE ===\n")
    
    correct = 0
    for question, response, expected in test_cases:
        should_annotate = classifier.should_annotate(question, response)
        question_type, confidence = classifier.classify_question(question, response)
        
        status = "✓" if should_annotate == expected else "✗"
        correct += 1 if should_annotate == expected else 0
        
        print(f"{status} Domanda: {question[:60]}...")
        print(f"   Risposta: {response[:40]}...")
        print(f"   Tipo: {question_type.value} (confidenza: {confidence:.2f})")
        print(f"   Annotare: {should_annotate} (atteso: {expected})")
        print()
    
    accuracy = correct / len(test_cases) * 100
    print(f"Accuratezza: {accuracy:.1f}% ({correct}/{len(test_cases)})")

if __name__ == '__main__':
    test_classifier()
