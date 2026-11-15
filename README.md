# Portes logiques et circuits combinatoires : cours et exercices corrigés

Code de la vidéo **Portes logiques et circuits combinatoires** de la chaîne
[IT Skills Maker](https://www.youtube.com/@ItSkillsMaker), 2e vidéo de la playlist « Architecture des ordinateurs : cours
et exercices corrigés ». La vidéo précédente, sur l'algèbre de Boole et Karnaugh :
[SkillMakers/algebre-boole](https://github.com/SkillMakers/algebre-boole).

Un simulateur porte par porte, en Python pur. Chaque circuit de la vidéo tourne sur **toute** sa table de vérité et
il est comparé au calcul attendu. Le programme compte aussi les portes et la **profondeur** (le nombre de portes
traversées au pire), qui fixe le temps de réponse d'un vrai circuit.

## Lancer

Python 3.11 ou plus, aucune dépendance.

```
python demo.py           # les sept exercices de la vidéo, et le piège du débordement
python -m unittest -v    # les 24 tests
```

Les sorties obtenues pour la vidéo sont dans [`preuves/`](preuves/) : `demo.txt` (Python 3.15.1) et `tests.txt`
(24 tests verts sous 3.15.1 et 3.11).

## Les exercices

| | Énoncé | Résultat du programme |
|---|---|---|
| 1 | Analyser NAND(NAND(A,B), NAND(A,C)) | A(B + C), vrai sur les 8 lignes, 3 portes |
| 2 | Construire la porte de vote (majorité de 3) | AB + AC + BC : 4 portes, profondeur 2 |
| 3 | Un OU exclusif avec des NAND seulement | 4 portes, profondeur 3 ; un OU à la place est faux sur la ligne 1 1 |
| 4 | L'additionneur complet avec deux demi-additionneurs | 5 portes ; les deux retenues internes ne valent jamais 1 ensemble |
| 5 | L'additionneur 4 bits à propagation de retenue | juste sur les 256 paires ; retenue finale après 9 portes (65 sur 32 bits) |
| 6 | La soustraction en complément à deux | A + B̅ + 1, juste sur les 512 lignes (addition et soustraction) |
| 7 | La majorité avec un seul multiplexeur 4 vers 1 | entrées 0, C, C, 1 ; 11 portes, contre 4 pour l'exercice 2 |

**Le piège** : 0111 + 0011 = 1010, sans retenue sortante. En non signé, 7 + 3 = 10 ; en signé, 1010 vaut -6. La
retenue (R) signale un dépassement non signé, le débordement (V) un dépassement signé : sur les 256 additions de
4 bits, ils sont en désaccord 112 fois.

## Les fichiers

| Fichier | Rôle |
|---|---|
| `circuits.py` | le simulateur (`Circuit`), les briques (demi-additionneur, additionneur, soustracteur, multiplexeurs, décodeur) |
| `demo.py` | les exercices de la vidéo, exécutés |
| `test_circuits.py` | chaque résultat cité dans la vidéo, en test |

## Ce que le simulateur simplifie

- **Une porte = un niveau de délai**, quelle que soit sa nature. Dans un vrai circuit, un OU exclusif est plus lent
  qu'un NON-ET.
- **L'additionneur 4 bits commence par un additionneur complet** avec une retenue d'entrée à 0 : c'est pour ça que le
  premier bit sort après 2 portes. Un demi-additionneur ferait gagner une porte sur ce bit.
- **Pas d'additionneur à retenue anticipée** : il est cité dans la vidéo, pas simulé.
