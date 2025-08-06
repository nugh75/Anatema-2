"""
Utility per la gestione della palette colori delle categorie
"""

import colorsys
import random
from typing import List, Tuple

class ColorPalette:
    """Gestisce la palette di colori per le categorie"""
    
    # Palette predefinita con colori distintivi e accessibili
    DEFAULT_COLORS = [
        '#2563eb',  # Blu moderno
        '#dc2626',  # Rosso
        '#059669',  # Verde smeraldo
        '#d97706',  # Arancione ambra
        '#7c3aed',  # Viola
        '#0891b2',  # Ciano
        '#be123c',  # Rosa scuro
        '#65a30d',  # Verde lime
        '#c2410c',  # Arancione scuro
        '#4338ca',  # Indaco
        '#be185d',  # Rosa
        '#166534',  # Verde scuro
        '#b91c1c',  # Rosso scuro
        '#1d4ed8',  # Blu scuro
        '#92400e',  # Giallo scuro
        '#5b21b6',  # Viola scuro
        '#0f766e',  # Teal
        '#a21caf',  # Fucsia
        '#365314',  # Verde oliva
        '#7e22ce',  # Viola medio
        '#0c4a6e',  # Blu ardesia
        '#991b1b',  # Rosso sangue
        '#1e40af',  # Blu reale
        '#b45309',  # Ambra scuro
        '#581c87',  # Viola profondo
        '#134e4a',  # Teal scuro
        '#9333ea',  # Viola bright
        '#0369a1',  # Blu cielo
        '#ca8a04',  # Giallo senape
        '#86198f'   # Magenta
    ]
    
    @classmethod
    def get_next_color(cls, used_colors: List[str]) -> str:
        """
        Restituisce il prossimo colore disponibile dalla palette
        
        Args:
            used_colors: Lista dei colori già utilizzati
            
        Returns:
            Codice esadecimale del prossimo colore
        """
        # Trova il primo colore non utilizzato
        for color in cls.DEFAULT_COLORS:
            if color not in used_colors:
                return color
        
        # Se tutti i colori sono utilizzati, genera un colore casuale
        return cls.generate_random_color(used_colors)
    
    @classmethod
    def generate_random_color(cls, avoid_colors: List[str] = None) -> str:
        """
        Genera un colore casuale evitando quelli già utilizzati
        
        Args:
            avoid_colors: Lista di colori da evitare
            
        Returns:
            Codice esadecimale del colore generato
        """
        if avoid_colors is None:
            avoid_colors = []
        
        max_attempts = 50
        for _ in range(max_attempts):
            # Genera colore con buona saturazione e luminosità per il contrasto
            hue = random.random()
            saturation = random.uniform(0.6, 0.9)  # Saturazione media-alta
            lightness = random.uniform(0.3, 0.6)   # Luminosità media per buon contrasto
            
            # Converti HSL in RGB
            rgb = colorsys.hls_to_rgb(hue, lightness, saturation)
            color = '#{:02x}{:02x}{:02x}'.format(
                int(rgb[0] * 255),
                int(rgb[1] * 255),
                int(rgb[2] * 255)
            )
            
            # Verifica che non sia troppo simile ai colori esistenti
            if cls.is_color_distinct(color, avoid_colors):
                return color
        
        # Fallback: restituisce un colore dalla palette predefinita
        return cls.DEFAULT_COLORS[0]
    
    @classmethod
    def is_color_distinct(cls, color: str, existing_colors: List[str], threshold: float = 30.0) -> bool:
        """
        Verifica se un colore è sufficientemente distinto da quelli esistenti
        
        Args:
            color: Colore da verificare (hex)
            existing_colors: Lista di colori esistenti (hex)
            threshold: Soglia di differenza (0-100)
            
        Returns:
            True se il colore è sufficientemente distinto
        """
        if not existing_colors:
            return True
        
        color_hsl = cls.hex_to_hsl(color)
        
        for existing in existing_colors:
            existing_hsl = cls.hex_to_hsl(existing)
            
            # Calcola la differenza in spazio HSL
            hue_diff = min(abs(color_hsl[0] - existing_hsl[0]), 
                          360 - abs(color_hsl[0] - existing_hsl[0]))
            sat_diff = abs(color_hsl[1] - existing_hsl[1]) * 100
            light_diff = abs(color_hsl[2] - existing_hsl[2]) * 100
            
            # Peso diverso per diversi componenti
            distance = (hue_diff * 0.6 + sat_diff * 0.3 + light_diff * 0.1)
            
            if distance < threshold:
                return False
        
        return True
    
    @classmethod
    def hex_to_hsl(cls, hex_color: str) -> Tuple[float, float, float]:
        """
        Converte un colore esadecimale in HSL
        
        Args:
            hex_color: Colore in formato esadecimale (#RRGGBB)
            
        Returns:
            Tupla (hue, saturation, lightness) con hue in gradi (0-360)
        """
        # Rimuovi il # se presente
        hex_color = hex_color.lstrip('#')
        
        # Converti in RGB
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        
        # Converti in HSL
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        
        return (h * 360, s, l)
    
    @classmethod
    def hsl_to_hex(cls, h: float, s: float, l: float) -> str:
        """
        Converte HSL in esadecimale
        
        Args:
            h: Hue in gradi (0-360)
            s: Saturation (0-1)
            l: Lightness (0-1)
            
        Returns:
            Colore in formato esadecimale
        """
        # Normalizza hue
        h = h / 360.0
        
        # Converti in RGB
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        
        # Converti in esadecimale
        return '#{:02x}{:02x}{:02x}'.format(
            int(r * 255),
            int(g * 255),
            int(b * 255)
        )
    
    @classmethod
    def adjust_color(cls, hex_color: str, hue_shift: float = 0, 
                    sat_factor: float = 1.0, light_factor: float = 1.0) -> str:
        """
        Aggiusta un colore modificando HSL
        
        Args:
            hex_color: Colore base in esadecimale
            hue_shift: Spostamento di tonalità in gradi (-360 a 360)
            sat_factor: Fattore moltiplicativo per saturazione
            light_factor: Fattore moltiplicativo per luminosità
            
        Returns:
            Nuovo colore in esadecimale
        """
        h, s, l = cls.hex_to_hsl(hex_color)
        
        # Applica le modifiche
        h = (h + hue_shift) % 360
        s = max(0, min(1, s * sat_factor))
        l = max(0.1, min(0.9, l * light_factor))  # Mantieni leggibilità
        
        return cls.hsl_to_hex(h, s, l)
    
    @classmethod
    def get_contrasting_text_color(cls, bg_color: str) -> str:
        """
        Determina se usare testo bianco o nero per un colore di sfondo
        
        Args:
            bg_color: Colore di sfondo in esadecimale
            
        Returns:
            '#ffffff' per testo bianco, '#000000' per testo nero
        """
        # Rimuovi il # se presente
        bg_color = bg_color.lstrip('#')
        
        # Converti in RGB
        r = int(bg_color[0:2], 16)
        g = int(bg_color[2:4], 16)
        b = int(bg_color[4:6], 16)
        
        # Calcola la luminanza relativa
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        
        # Soglia per determinare il contrasto
        return '#000000' if luminance > 0.5 else '#ffffff'
    
    @classmethod
    def validate_color(cls, color: str) -> bool:
        """
        Valida se una stringa è un colore esadecimale valido
        
        Args:
            color: Stringa da validare
            
        Returns:
            True se è un colore valido
        """
        if not color:
            return False
        
        color = color.strip()
        if not color.startswith('#'):
            return False
        
        if len(color) != 7:
            return False
        
        try:
            int(color[1:], 16)
            return True
        except ValueError:
            return False
    
    @classmethod
    def get_color_by_index(cls, index: int) -> str:
        """
        Restituisce un colore dalla palette usando l'indice
        
        Args:
            index: Indice del colore (0-based)
            
        Returns:
            Colore in formato esadecimale
        """
        if index < len(cls.DEFAULT_COLORS):
            return cls.DEFAULT_COLORS[index]
        
        # Se l'indice supera la palette, usa modulo per ciclare
        return cls.DEFAULT_COLORS[index % len(cls.DEFAULT_COLORS)]
