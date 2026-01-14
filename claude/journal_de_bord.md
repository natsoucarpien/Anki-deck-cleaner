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
