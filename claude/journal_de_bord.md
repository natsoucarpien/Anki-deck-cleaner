# Journal de bord - Anki Deck Cleaner

## 2026-01-14 - Initialisation

**Statut du projet:**
- Objectif 1 (nettoyage texte) : Termine
- Objectif 2 (tags automatiques) : Termine
- Objectif 3 (crop images) : Abandonne

**Code existant:**
- `anki_deck_cleaner.py` : Script principal fonctionnel
- `tags_config.txt` : Configuration des tags par mots-clefs
- `run_cleaner.bat` : Lanceur Windows

---

## 2026-01-14 - Analyse objectif 3 (crop images)

**Probleme:** Les cartes Anki contiennent des images avec une mini-carte geographique (solution) a cropper.

**Analyse realisee:**
- 9 images test analysees
- Mini-carte toujours a droite, mais position verticale variable
- Fonds tres varies (blanc, noir, bleu, vert, rose...)
- Taille: 25% a 44% de la largeur de l'image

**Conclusion:** Detection automatique peu fiable due a la grande variabilite des images.

**Decision initiale:** Objectif abandonne - detection auto peu fiable.

---

## 2026-01-14 - Objectif 3 restaure

**Script:** `anki_image_cropper.py` + `run_cropper.bat`

**Fonctionnalites:**
- Support PNG, AVIF, JPEG
- Decompression/recompression zstd automatique
- Crop configurable (defaut: 30% depuis la droite)

**Usage:** Pour les decks ou les images ont la mini-carte au meme endroit.

---

## 2026-01-14 - Cloture session

**Etat final:**
- Objectif 1 (nettoyage texte): OK - script remplace par version claude.ai
- Objectif 2 (tags automatiques): OK
- Objectif 3 (crop images): OK - script fonctionnel

**Fichiers:**
- `anki_deck_cleaner.py` : Nettoyage + tags
- `anki_image_cropper.py` : Crop images
- `tags_config.txt` : Configuration des tags

**Projet fonctionnel.** Ameliorations futures a prevoir.

---

## 2026-01-15 - Generalisation du cleaner

**Probleme identifie:**
Le pattern de detection du header etait trop restrictif :
- Cherchait uniquement `<h1>A Learnable [pays]</h1>`
- Ne fonctionnait pas pour les decks avec d'autres formats de titre

**Decks concernes (non fonctionnels avant le fix):**
- "A Major Bajor Chile"
- "ALM - African Spotlights"
- "Learnable Colombia"
- "Ultimate Kazakhstan - Clue Collector"
- "USA USA"
- "A Learnable Plant World"

**Solution appliquee:**
Pattern generalise dans `anki_deck_cleaner.py` (ligne 220) :
```python
# Avant (trop restrictif)
r'<div><div><div><h1>A Learnable [^<]*</h1>...'

# Apres (generique)
r'(?:<div>)+<div><h1>[^<]+</h1>...'
```

**Changements:**
- `(?:<div>)+` : accepte un nombre variable de divs (3, 4, 5...)
- `[^<]+` : accepte n'importe quel titre dans le `<h1>`

**Resultat:** Tous les formats de decks testes fonctionnent maintenant.

---

## 2026-01-16 - Mots-clés et nettoyage Source

**Mots-clés ajoutés au tag infrastructure:**
signpost, signposts, roadway, lane, lanes, traffic, pavements, kerb, kerbs, curb, curbs, sidewalk, lamp, crossing, sign, pedestrian, streetlight, guardrail, guardrails, fence, fences, parking

**Mots-clés ajoutés au tag architecture:**
house, houses, residence, residences, residential, skyscraper, skyscrapers, tower, towers, apartment, foundation, foundations, column, columns, window, windows, entrance, entrances, shutter, shutters, floor, floors, room, rooms, hall, halls

**Déplacement:** `house` retiré de infrastructure (maintenant uniquement dans architecture)

**Nouveau pattern de nettoyage (anki_deck_cleaner.py):**
Ajout étape 5c pour supprimer les lignes "Source: [lien]" (ex: Source: PlonkIt)
```python
source_pattern = r'<div>(?:<!--[^>]*-->)*<p>Source:\s*<a[^>]*>[^<]*</a></p>(?:<!--[^>]*-->)*</div>'
```

---

## Regles pour Claude

**Git - fichiers a ignorer (ne jamais commit/push):**
- `*.apkg` : Fichiers de decks Anki (trop volumineux, donnees utilisateur)
- `decks/` : Stockage personnel des decks en cours d'edition
- `tmpclaude-*` : Fichiers temporaires de session Claude
