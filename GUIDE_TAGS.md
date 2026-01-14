# 🏷️ GUIDE DE MODIFICATION DES TAGS

## 📋 Introduction

Le fichier `tags_config.txt` contient toute la configuration des tags automatiques. Vous pouvez facilement **ajouter**, **modifier** ou **supprimer** des tags sans toucher au code Python !

## 🎯 Structure du fichier

```
[nom_du_tag]
\bmot-clé1\b
\bmot-clé2\b
\bmot-clé3\b
```

### Explications :
- `[nom_du_tag]` : Le nom du tag tel qu'il apparaîtra dans Anki
- `\bmot-clé\b` : Un mot-clé à détecter (le `\b` signifie "frontière de mot")
- Chaque mot-clé est sur une ligne séparée
- Les lignes commençant par `#` sont des commentaires (ignorés)

## ✏️ Comment modifier les tags

### ➕ AJOUTER un nouveau tag

1. Ouvrez `tags_config.txt`
2. Ajoutez une nouvelle section à la fin du fichier :

```
[nouveau_tag]
\bmot-clé1\b
\bmot-clé2\b
\bmot-clé3\b
```

**Exemple** - Ajouter un tag "weather" :
```
[weather]
\bweather\b
\brain\b
\bsnow\b
\bsun\b
\bcloudy\b
```

### ✏️ MODIFIER un tag existant

1. Trouvez la section `[nom_du_tag]`
2. Ajoutez ou supprimez des mots-clés dans cette section

**Exemple** - Ajouter "highway" au tag "road" :
```
[road]
\bBR-\d+\b
\bUS-\d+\b
\bRoute\s+\d+\b
\bhighway\b          ← Nouveau mot-clé ajouté
\bautoroute\b
```

### ❌ SUPPRIMER un tag

1. Trouvez la section `[nom_du_tag]`
2. Supprimez toute la section (y compris tous ses mots-clés)

## 🔍 Syntaxe des mots-clés (Regex)

Les mots-clés utilisent des **expressions régulières** (regex). Voici les patterns les plus utiles :

| Pattern | Signification | Exemple |
|---------|---------------|---------|
| `\b` | Frontière de mot | `\bcar\b` trouve "car" mais pas "ca**r**pet" |
| `\d+` | Un ou plusieurs chiffres | `\bBR-\d+\b` trouve "BR-405", "BR-101", etc. |
| `\s+` | Un ou plusieurs espaces | `\bgoogle\s+car\b` trouve "google car" |
| `.*` | N'importe quel caractère | `\bRoute.*\b` trouve "Route 66", "Route nationale" |
| `(a\|b)` | "a" OU "b" | `\b(roof\|toit)\b` trouve "roof" ou "toit" |

### ⚠️ Caractères spéciaux

Si vous voulez chercher un caractère spécial littéralement, ajoutez `\` devant :
- `.` → `\.` (point)
- `?` → `\?` (point d'interrogation)
- `+` → `\+` (plus)
- `-` → Pas besoin d'échapper dans la plupart des cas

## 📝 Exemples pratiques

### Exemple 1 : Détecter les routes brésiliennes

```
[road]
\bBR-\d+\b          # BR-405, BR-101, etc.
\bBR\s+\d+\b        # BR 405, BR 101, etc.
```

### Exemple 2 : Détecter plusieurs langues

```
[langue]
\blanguage\b
\balphabet\b
\bscript\b
\bécriture\b
```

### Exemple 3 : Détecter un pays avec ses variantes

```
[thailand]
\bthailand\b
\bthaïlande\b
\bthai\b
\bbangkok\b
\bphuket\b
\bchiang mai\b
```

## 🎨 Exemples de modifications demandées

### ✅ Ajouter les 4 nouveaux tags

Ces tags ont déjà été ajoutés dans `tags_config.txt` :

1. **architecture** : Détecte roof, shrine, temple, church, mosque, etc.
2. **landscape** : Détecte paysage, montagne, marais, hill, valley, etc.
3. **road** : Détecte BR-405, US-66, highway, autoroute, etc.
4. **bollard** : Détecte bollard, borne, post, reflector

### ✅ Tous les pays ajoutés

Plus de 180 pays ont été ajoutés avec leurs variantes en anglais/français et leurs capitales principales !

### ✅ "roof, shrine, temple" retirés d'infrastructure

Ces mots-clés ont été déplacés vers le tag **architecture**.

## 🔄 Appliquer les modifications

1. Modifiez `tags_config.txt`
2. Sauvegardez le fichier
3. Relancez le script `anki_deck_cleaner.py`

C'est tout ! Les modifications sont appliquées immédiatement.

## 💡 Conseils

### ✅ BONNES PRATIQUES

- Utilisez `\b` autour des mots pour éviter les fausses détections
- Groupez les mots-clés par thème logique
- Ajoutez des commentaires pour expliquer les patterns complexes
- Testez vos modifications sur un petit deck d'abord

### ❌ À ÉVITER

- Ne pas mettre d'espaces au début/fin des lignes (sauf dans les patterns regex)
- Ne pas oublier les `\b` pour les mots simples
- Ne pas dupliquer des patterns entre plusieurs tags

## 🐛 Dépannage

### Le tag n'est pas détecté

1. Vérifiez que le mot-clé est bien écrit
2. Ajoutez `\b` autour du mot
3. Vérifiez que vous êtes dans la bonne section `[tag]`
4. Testez avec un mot plus simple d'abord

### Trop de faux positifs

1. Ajoutez `\b` autour du mot pour être plus précis
2. Utilisez des patterns plus spécifiques
3. Exemple : `\bcar\b` au lieu de `car` (pour éviter "carpet", "carnival", etc.)

### Le script ne voit pas le fichier

1. Assurez-vous que `tags_config.txt` est dans le **même dossier** que `anki_deck_cleaner.py`
2. Vérifiez l'orthographe du nom du fichier
3. Le script affiche "Configuration chargée" s'il trouve le fichier

## 📚 Ressources

Pour apprendre plus sur les regex (expressions régulières) :
- https://regex101.com/ (testeur en ligne)
- https://regexr.com/ (avec explications visuelles)

## 🎯 Résumé rapide

| Action | Étapes |
|--------|--------|
| **Ajouter un tag** | Ajoutez une section `[nouveau_tag]` avec ses mots-clés |
| **Modifier un tag** | Éditez les mots-clés dans la section existante |
| **Supprimer un tag** | Supprimez toute la section `[tag]` |
| **Appliquer** | Sauvegardez et relancez le script |

---

💡 **Astuce** : Commencez par modifier un ou deux tags pour vous familiariser, puis ajoutez-en d'autres progressivement !
