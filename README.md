# 🎴 Anki Deck Cleaner

Un outil Python pour automatiser le nettoyage de vos decks Anki.

## 📋 Prérequis

- Python 3.6 ou supérieur
- Les bibliothèques sont déjà incluses dans Python (pas de dépendances externes)

## 🚀 Installation

### Étape 1 : Vérifier que Python est installé

Ouvrez un terminal (ou invite de commandes sur Windows) et tapez :

```bash
python --version
```

ou 

```bash
python3 --version
```

Vous devriez voir quelque chose comme `Python 3.x.x`. Si ce n'est pas le cas, [téléchargez Python](https://www.python.org/downloads/).

### Étape 2 : Télécharger le script

Placez le fichier `anki_deck_cleaner.py` dans un dossier de votre choix.

## 💻 Utilisation

### Méthode 1 : Mode interactif (recommandé pour les débutants)

1. Ouvrez un terminal dans le dossier contenant le script
2. Lancez le script :

```bash
python anki_deck_cleaner.py
```

3. Le script vous demandera le chemin vers votre fichier `.apkg`
4. Entrez le chemin complet du fichier (vous pouvez glisser-déposer le fichier dans le terminal)
5. Le script créera automatiquement un fichier nettoyé avec le suffixe `_cleaned.apkg`

### Exemple d'utilisation

```
🎴 ANKI DECK CLEANER
============================================================

📁 Entrez le chemin vers votre fichier .apkg : /Users/vous/Documents/mon_deck.apkg

📦 Extraction de mon_deck.apkg...
✅ Extraction terminée dans temp_anki_deck
🧹 Nettoyage des cartes...
✅ 50 cartes nettoyées
📦 Création du fichier nettoyé : mon_deck_cleaned.apkg...
✅ Fichier créé : /Users/vous/Documents/mon_deck_cleaned.apkg
🗑️  Fichiers temporaires supprimés

============================================================
✨ NETTOYAGE TERMINÉ AVEC SUCCÈS !
============================================================
```

## 🔧 Que fait le script ?

Le script nettoie **automatiquement** vos cartes Anki de manière simple et efficace.

### 📋 Structure des cartes
Vos cartes Anki de type "meta" peuvent avoir 2 ou 3 champs :
- **Champ 1** : Rule name (nom de la règle)
- **Champ 2** : Image (optionnel) OU Answer
- **Dernier champ** : Answer (réponse)

**Important** : Le script ne modifie **QUE le dernier champ** (qui contient la réponse). Tous les autres champs restent intacts.

### 🎯 Suppression automatique du bloc d'en-tête
Dans le champ Answer, le script supprime **systématiquement les 3 premières lignes non-vides**, qui correspondent au bloc d'en-tête standard :
1. **Ligne 1** : Titre du deck (quel qu'il soit)
2. **Ligne 2** : Meta List · X metas · Y locations · by Auteur
3. **Ligne 3** : ▶ Play Map

**Aucune configuration nécessaire** - le script fonctionne avec n'importe quel titre de deck !

### 🧹 Autres éléments supprimés

Le script supprime également tous ces éléments dans le reste de la carte :

#### Compteurs et navigation
- `80 of 102 metas`, `95 of 102 meta` (compteurs de progression)
- `♥ 3`, `♥ 42` (compteurs de favoris)
- `<`, `>`, `< >`, `< > <` (boutons de navigation)

#### Liens et sections
- `Check out [URL] for more clues.`
- `Images` (titre de section)
- `(1)`, `(2)`, etc. (numéros d'images)

### ✨ Ce qui est préservé
Le script :
1. ✅ Extrait votre deck `.apkg`
2. ✅ Ne modifie **QUE le dernier champ** (Answer) - tous les autres champs restent intacts
3. ✅ Supprime automatiquement les 3 premières lignes du champ Answer
4. ✅ Nettoie tous les autres éléments indésirables dans le champ Answer
5. ✅ Crée un nouveau deck nettoyé
6. ✅ Supprime les fichiers temporaires
7. ✅ **Préserve tous vos médias** (images, audio)
8. ✅ **Garde le contenu important** de vos cartes intact
9. ✅ **Fonctionne avec TOUS vos decks** sans modification (2, 3 champs ou plus)

## ⚙️ Personnalisation

Si vous voulez supprimer d'autres lignes, modifiez la fonction `remove_unwanted_lines` dans le script :

```python
patterns_to_remove = [
    r'^A Learnable Indonesia - Intermediate\s*',
    r'^Meta List.*?by.*?\s*',
    r'^Play Map\s*',
    # Ajoutez vos propres motifs ici
    r'^Votre texte à supprimer\s*',
]
```

## 📝 Conseils

1. **Testez d'abord sur une copie** de votre deck avant de supprimer l'original
2. **Vérifiez le résultat** en important le fichier `_cleaned.apkg` dans Anki
3. Si quelque chose ne va pas, vous avez toujours votre fichier original

### 🔍 Script de diagnostic (optionnel)

Si vous voulez **analyser la structure** de votre deck avant de le nettoyer, utilisez le script de diagnostic :

```bash
python anki_diagnostic.py "votre_deck.apkg"
```

Ce script vous montrera :
- Le nombre de champs dans vos cartes
- Les noms des champs
- Des exemples de contenu

Cela peut être utile pour vérifier que le script va nettoyer le bon champ.

## ❓ Résolution de problèmes

### Le script ne trouve pas mon fichier

Assurez-vous :
- Que le chemin est correct
- Que l'extension est bien `.apkg`
- D'utiliser des guillemets si le chemin contient des espaces : `"/chemin/avec des espaces/deck.apkg"`

### Erreur "Permission denied"

Le dossier est peut-être protégé en écriture. Essayez de :
- Déplacer votre fichier dans un autre dossier (Documents, Bureau)
- Lancer le terminal en administrateur (Windows) ou avec `sudo` (Mac/Linux)

## 🔄 Versions futures

Fonctionnalités prévues :
- Interface graphique (GUI)
- Plus d'options de nettoyage
- Prévisualisation avant modification
- Nettoyage en masse de plusieurs decks

## 📧 Support

Si vous rencontrez des problèmes, n'hésitez pas à demander de l'aide !
