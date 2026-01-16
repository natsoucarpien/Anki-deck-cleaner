#!/usr/bin/env python3
"""
Anki Deck Cleaner
Automatise le nettoyage des cartes dans un deck Anki (.apkg)
"""

import zipfile
import sqlite3
import os
import shutil
import re
from pathlib import Path


class AnkiDeckCleaner:
    """Classe pour nettoyer les decks Anki"""
    
    def __init__(self, input_file):
        """
        Initialise le nettoyeur de deck
        
        Args:
            input_file: Chemin vers le fichier .apkg à nettoyer
        """
        self.input_file = Path(input_file)
        self.temp_dir = Path("temp_anki_deck")
        self.db_path = None
        
        # Vérifier que le fichier existe
        if not self.input_file.exists():
            raise FileNotFoundError(f"Le fichier {input_file} n'existe pas")
    
    def extract_apkg(self):
        """Extrait le contenu du fichier .apkg dans un dossier temporaire"""
        print(f"📦 Extraction de {self.input_file.name}...")
        
        # Créer le dossier temporaire
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.temp_dir.mkdir()
        
        # Extraire le fichier ZIP
        with zipfile.ZipFile(self.input_file, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)
        
        # Trouver le fichier de base de données
        # Essayer d'abord anki21 (format plus récent)
        self.db_path = self.temp_dir / "collection.anki21"
        if not self.db_path.exists():
            # Sinon essayer anki2 (ancien format)
            self.db_path = self.temp_dir / "collection.anki2"
        
        if not self.db_path.exists():
            raise FileNotFoundError("Base de données Anki non trouvée (ni .anki21 ni .anki2)")
        
        print(f"✅ Base de données trouvée : {self.db_path.name}")
    
    def load_tags_config(self, config_file='tags_config.txt'):
        """
        Charge la configuration des tags depuis un fichier
        
        Args:
            config_file: Chemin vers le fichier de configuration
            
        Returns:
            Dictionnaire {tag: [liste de patterns]}
        """
        import re
        from pathlib import Path
        
        # Chercher le fichier dans différents emplacements
        possible_paths = [
            Path(config_file),  # Chemin relatif
            Path(__file__).parent / config_file,  # Même dossier que le script
            Path.cwd() / config_file,  # Dossier courant
        ]
        
        config_path = None
        for path in possible_paths:
            if path.exists():
                config_path = path
                break
        
        if not config_path:
            print(f"⚠️  Fichier de configuration '{config_file}' non trouvé")
            print(f"   Le tagging automatique sera désactivé")
            return {}
        
        tags_config = {}
        current_tag = None
        
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Ignorer les lignes vides et les commentaires
                if not line or line.startswith('#'):
                    continue
                
                # Nouvelle section de tag
                if line.startswith('[') and line.endswith(']'):
                    current_tag = line[1:-1]
                    tags_config[current_tag] = []
                
                # Mot-clé pour le tag actuel
                elif current_tag:
                    tags_config[current_tag].append(line)
        
        print(f"✅ Configuration chargée : {len(tags_config)} tags définis")
        return tags_config
    
    def detect_tags(self, text):
        """
        Détecte les tags appropriés basés sur le contenu du texte
        
        Args:
            text: Le texte à analyser (nom de la carte + contenu)
            
        Returns:
            Liste de tags détectés
        """
        import re
        
        # Charger la configuration si pas déjà chargée
        if not hasattr(self, 'tags_config'):
            self.tags_config = self.load_tags_config()
        
        # Si pas de configuration, retourner une liste vide
        if not self.tags_config:
            return []
        
        # Normaliser le texte (minuscules, sans HTML)
        text_lower = text.lower()
        text_clean = re.sub(r'<[^>]+>', '', text_lower)
        
        detected_tags = []
        
        # Détecter les tags basés sur les patterns de la configuration
        for tag, patterns in self.tags_config.items():
            for pattern in patterns:
                try:
                    if re.search(pattern, text_clean):
                        if tag not in detected_tags:
                            detected_tags.append(tag)
                        break  # Pas besoin de vérifier les autres patterns pour ce tag
                except re.error:
                    # Pattern regex invalide, on l'ignore
                    continue
        
        return detected_tags
    
    def clean_cards(self):
        """Nettoie les cartes en supprimant les lignes indésirables"""
        print("🧹 Nettoyage des cartes...")
        
        # Connexion à la base de données SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Récupérer toutes les notes
        cursor.execute("SELECT id, flds, tags FROM notes")
        notes = cursor.fetchall()
        
        cleaned_count = 0
        
        for note_id, fields, existing_tags in notes:
            # Les champs sont séparés par '\x1f' dans Anki
            field_list = fields.split('\x1f')
            
            # Ne nettoyer que le DERNIER champ (généralement le champ "answer")
            # Cela fonctionne que la carte ait 2, 3 ou plus de champs
            cleaned_fields = []
            for i, field in enumerate(field_list):
                if i == len(field_list) - 1:  # Dernier champ = answer
                    cleaned_field = self.remove_unwanted_lines(field)
                    cleaned_fields.append(cleaned_field)
                else:
                    # Garder les autres champs intacts
                    cleaned_fields.append(field)
            
            # Reconstituer les champs
            new_fields = '\x1f'.join(cleaned_fields)
            
            # Détecter les tags automatiquement
            # Analyser le premier champ (nom) + dernier champ (answer) pour plus de précision
            text_to_analyze = field_list[0] + " " + cleaned_fields[-1]
            detected_tags = self.detect_tags(text_to_analyze)
            
            # Combiner avec les tags existants
            existing_tags_list = existing_tags.strip().split() if existing_tags.strip() else []
            all_tags = list(set(existing_tags_list + detected_tags))  # Éliminer les doublons
            new_tags = ' '.join(all_tags)
            
            # Mettre à jour si des modifications ont été faites
            if new_fields != fields or new_tags != existing_tags:
                cursor.execute("UPDATE notes SET flds = ?, tags = ? WHERE id = ?", 
                             (new_fields, new_tags, note_id))
                cleaned_count += 1
        
        # Sauvegarder les modifications
        conn.commit()
        conn.close()
        
        print(f"✅ {cleaned_count} cartes nettoyées et taguées")
    
    def remove_unwanted_lines(self, text):
        """
        Supprime les lignes indésirables dans le texte
        
        Args:
            text: Le texte à nettoyer
            
        Returns:
            Le texte nettoyé
        """
        import re
        
        # Étape 1 : Supprimer le bloc d'en-tête complet s'il existe
        # Pattern générique qui fonctionne pour tous les titres (A Learnable X, Learnable X, Ultimate X, etc.)
        header_block_pattern = r'(?:<div>)+<div><h1>[^<]+</h1>.*?Play Map.*?</a><!--\]--><!--[^>]*--></div></div>'
        text = re.sub(header_block_pattern, '', text, flags=re.DOTALL)
        
        # Étape 2 : Supprimer les divs avec compteurs (ex: <div>4 of 102 metas</div>)
        counter_div_pattern = r'<!--\[--><div>\d+\s+of\s+\d+\s+metas?</div><!--\]-->'
        text = re.sub(counter_div_pattern, '', text)
        
        # Étape 3 : Supprimer le bouton avec cœur et compteur
        # Pattern : <button ... ><div>...<svg avec heart>... <span>3</span></div>...</button>
        heart_button_pattern = r'<button[^>]*data-tooltip-trigger[^>]*>.*?<path[^>]*d="M12 12q\.825.*?</button><!--\]-->'
        text = re.sub(heart_button_pattern, '', text, flags=re.DOTALL)
        
        # Étape 4 : Supprimer les boutons de navigation (< et >) 
        # Pattern simple pour tous les boutons avec data-slot="button"
        nav_button_pattern = r'<button data-slot="button"[^>]*>.*?</button>'
        text = re.sub(nav_button_pattern, '', text, flags=re.DOTALL)
        
        # Étape 5 : Supprimer "Check out ... for more clues" avec lien
        check_out_pattern = r'Check out\s+<a[^>]*>.*?</a>\s+for more clues\.'
        text = re.sub(check_out_pattern, '', text, flags=re.DOTALL)
        
        # Étape 5b : Supprimer "Description and images taken from: [lien]"
        description_pattern = r'Description and images taken from:\s+<a[^>]*>.*?</a>\.?'
        text = re.sub(description_pattern, '', text, flags=re.DOTALL | re.IGNORECASE)

        # Étape 5c : Supprimer "Source: [lien]" (ex: Source: PlonkIt)
        source_pattern = r'<div>(?:<!--[^>]*-->)*<p>Source:\s*<a[^>]*>[^<]*</a></p>(?:<!--[^>]*-->)*</div>'
        text = re.sub(source_pattern, '', text, flags=re.DOTALL | re.IGNORECASE)

        # Étape 6 : Supprimer l'icône d'image (SVG avec path contenant "M5 21q-.825...")
        # C'est le petit symbole d'image qui s'affiche
        image_icon_pattern = r'<svg[^>]*>.*?<path d="M5 21q-.825 0-1\.412-.587T3 19V5.*?</svg><!--\]--><!-- -->'
        text = re.sub(image_icon_pattern, '', text, flags=re.DOTALL)
        
        # Étape 7 : Supprimer "Images" et "(1)", "(2)", etc.
        images_pattern = r'<h3[^>]*>Images</h3>|<!--\[--><span>\(\d+\)</span><!--\]-->'
        text = re.sub(images_pattern, '', text)
        
        # Étape 8 : Nettoyer ligne par ligne pour les éléments restants
        patterns_to_remove = [
            r'^\d+\s+of\s+\d+\s+metas?\s*$',
            r'^♥\s*\d+\s*$',
            r'^[<>\s]+$',
            r'^Check out\s+.*?for more clues\.\s*$',
            r'^Description and images taken from:.*$',
            r'^Images\s*$',
            r'^\(\d+\)\s*$',
            r'^Source\s*:\s*.*$',
        ]
        
        lines = text.split('<br>')
        cleaned_lines = []
        
        for line in lines:
            clean_line = re.sub(r'<[^>]+>', '', line).strip()
            raw_stripped = line.strip()
            
            should_remove = False
            
            for pattern in patterns_to_remove:
                if clean_line and re.match(pattern, clean_line, re.IGNORECASE):
                    should_remove = True
                    break
                if raw_stripped and re.match(pattern, raw_stripped, re.IGNORECASE):
                    should_remove = True
                    break
            
            if not should_remove:
                cleaned_lines.append(line)
        
        result = '<br>'.join(cleaned_lines)
        
        # Nettoyer les <br> multiples consécutifs (plus de 2)
        result = re.sub(r'(<br>\s*){3,}', '<br><br>', result)
        
        return result
    
    def create_cleaned_apkg(self, output_file=None):
        """
        Crée un nouveau fichier .apkg avec les cartes nettoyées
        
        Args:
            output_file: Nom du fichier de sortie (optionnel)
        """
        if output_file is None:
            # Créer un nom par défaut : nom_original_cleaned.apkg
            output_file = self.input_file.stem + "_cleaned.apkg"
        
        output_path = Path(output_file)
        print(f"📦 Création du fichier nettoyé : {output_path.name}...")
        
        # Créer le fichier ZIP
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Ajouter tous les fichiers du dossier temporaire
            for file_path in self.temp_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.temp_dir)
                    zipf.write(file_path, arcname)
        
        print(f"✅ Fichier créé : {output_path.absolute()}")
        return output_path
    
    def cleanup(self):
        """Supprime les fichiers temporaires"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        print("🗑️  Fichiers temporaires supprimés")
    
    def process(self, output_file=None):
        """
        Processus complet de nettoyage
        
        Args:
            output_file: Nom du fichier de sortie (optionnel)
            
        Returns:
            Chemin vers le fichier nettoyé
        """
        try:
            self.extract_apkg()
            self.clean_cards()
            output_path = self.create_cleaned_apkg(output_file)
            return output_path
        finally:
            self.cleanup()


def main():
    """Fonction principale"""
    print("=" * 60)
    print("🎴 ANKI DECK CLEANER")
    print("=" * 60)
    print()
    
    # Demander le fichier à l'utilisateur
    input_file = input("📁 Entrez le chemin vers votre fichier .apkg : ").strip()
    
    # Retirer les guillemets si présents
    input_file = input_file.strip('"').strip("'")
    
    try:
        # Créer le nettoyeur et traiter le deck
        cleaner = AnkiDeckCleaner(input_file)
        output_path = cleaner.process()
        
        print()
        print("=" * 60)
        print("✨ NETTOYAGE TERMINÉ AVEC SUCCÈS !")
        print("=" * 60)
        print(f"Fichier original : {input_file}")
        print(f"Fichier nettoyé  : {output_path}")
        print()
        print("Vous pouvez maintenant importer le fichier nettoyé dans Anki.")
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERREUR")
        print("=" * 60)
        print(f"Une erreur s'est produite : {e}")
        print()
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ UNE ERREUR S'EST PRODUITE")
        print("=" * 60)
        print(f"Erreur : {e}")
        import traceback
        traceback.print_exc()
    finally:
        print()
        input("Appuyez sur Entrée pour fermer cette fenêtre...")
