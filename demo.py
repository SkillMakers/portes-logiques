"""Les exercices de la video, executes : chaque circuit tourne sur toute sa table de verite.

    python demo.py > ../preuves/demo.txt
"""
from circuits import (Circuit, additionneur, additionneur_complet, attendu_addition, attendu_soustraction, decodeur2,
                      demi_additionneur, entrees_nombres, lire, mux2, mux4, signe, soustracteur, verifier)


def titre(t):
    print()
    print("=" * 72)
    print(t)
    print("=" * 72)


def montrer_table(c, sorties=None):
    sorties = sorties or list(c.sorties)
    print("  " + " ".join(c.entrees) + " | " + " ".join(sorties))
    for valeurs, obtenu in c.table():
        print("  " + " ".join(str(valeurs[e]).rjust(len(e)) for e in c.entrees) + " | "
              + " ".join(str(obtenu[s]).rjust(len(s)) for s in sorties))


def bilan(c, attendu, quoi):
    n, fausses = verifier(c, attendu)
    total, detail = c.compte()
    print(f"  {quoi} : {'vrai' if not fausses else 'FAUX'} sur les {n} lignes ({len(fausses)} fausse(s))")
    print(f"  portes : {total} {detail}")
    print(f"  profondeur (portes traversees, au pire) : {c.profondeurs()}")
    return fausses


# --- Exercice 1 : analyser un circuit -----------------------------------------------------------------------
titre("Exercice 1 - analyser : NAND( NAND(A,B), NAND(A,C) )")
c = Circuit("A", "B", "C")
c.sortie("F", c.porte("NAND", c.porte("NAND", "A", "B"), c.porte("NAND", "A", "C")))
montrer_table(c)
bilan(c, lambda A, B, C: {"F": A & (B | C)}, "F = A(B + C)")

# --- Exercice 2 : la porte de vote (majorite de 3) ------------------------------------------------------------
titre("Exercice 2 - synthese : la majorite de trois votes")
c = Circuit("A", "B", "C")
c.sortie("F", c.porte("OU", c.porte("ET", "A", "B"), c.porte("ET", "A", "C"), c.porte("ET", "B", "C")))
montrer_table(c)
bilan(c, lambda A, B, C: {"F": int(A + B + C >= 2)}, "F = AB + AC + BC")

# --- La porte NAND est universelle ------------------------------------------------------------------------------
titre("NAND universelle : NON, ET, OU avec des NAND seulement")
for nom, construire, attendu in [
    ("NON A = NAND(A, A)", lambda c: c.porte("NAND", "A", "A"), lambda A, B: {"F": 1 - A}),
    ("A ET B = NAND(NAND(A,B), NAND(A,B))",
     lambda c: (lambda n: c.porte("NAND", n, n))(c.porte("NAND", "A", "B")), lambda A, B: {"F": A & B}),
    ("A OU B = NAND(NAND(A,A), NAND(B,B))",
     lambda c: c.porte("NAND", c.porte("NAND", "A", "A"), c.porte("NAND", "B", "B")), lambda A, B: {"F": A | B}),
]:
    c = Circuit("A", "B")
    c.sortie("F", construire(c))
    print(nom)
    bilan(c, attendu, nom.split(" =")[0])

# --- Exercice 3 : XOR avec quatre NAND ------------------------------------------------------------------------
titre("Exercice 3 - XOR avec quatre portes NAND")
c = Circuit("A", "B")
n1 = c.porte("NAND", "A", "B")
c.sortie("F", c.porte("NAND", c.porte("NAND", "A", n1), c.porte("NAND", "B", n1)))
montrer_table(c)
bilan(c, lambda A, B: {"F": A ^ B}, "F = A XOR B")
print()
print("  L'erreur classique : prendre un OU pour un XOR.")
c = Circuit("A", "B")
c.sortie("F", c.porte("OU", "A", "B"))
for valeurs, obtenu, voulu in verifier(c, lambda A, B: {"F": A ^ B})[1]:
    print(f"  OU au lieu de XOR : faux pour A={valeurs['A']} B={valeurs['B']} (donne {obtenu['F']}, il faut {voulu['F']})")

# --- Exercice 4 : l'additionneur complet ------------------------------------------------------------------------
titre("Demi-additionneur : deux bits")
c = Circuit("A", "B")
s, r = demi_additionneur(c, "A", "B")
c.sortie("S", s)
c.sortie("R", r)
montrer_table(c)
bilan(c, lambda A, B: {"S": (A + B) % 2, "R": (A + B) // 2}, "S, R = A + B")

titre("Exercice 4 - additionneur complet = 2 demi-additionneurs + 1 OU")
c = Circuit("A", "B", "Re")
internes = []
s, r = additionneur_complet(c, "A", "B", "Re", internes)
c.sortie("S", s)
c.sortie("Rs", r)
montrer_table(c, ["S", "Rs"])
bilan(c, lambda A, B, Re: {"S": (A + B + Re) % 2, "Rs": (A + B + Re) // 2}, "S, Rs = A + B + Re")
# Les deux retenues internes, lues dans le circuit lui-meme (sorties d'observation, pas des portes en plus).
c.sortie("R1", internes[0])
c.sortie("R2", internes[1])
ensemble = [v for v, o in c.table() if o["R1"] and o["R2"]]
print("  Les deux retenues internes (R1, R2) valent-elles 1 en meme temps, sur les 8 lignes ?",
      "jamais" if not ensemble else f"oui : {ensemble}")

# --- Exercice 5 : l'additionneur 4 bits ---------------------------------------------------------------------------
titre("Exercice 5 - additionneur 4 bits a propagation de retenue")
add4 = additionneur(4)
res = add4.evaluer(**entrees_nombres(0b0101, 0b0011, 4))
print(f"  0101 + 0011 = {''.join(str(res[f'S{i}']) for i in (3, 2, 1, 0))}, retenue {res['R']}"
      f"   (5 + 3 = {lire(res, 'S', 4)})")
n, fausses = verifier(add4, attendu_addition(4))
total, detail = add4.compte()
print(f"  verifie contre a + b : {'vrai' if not fausses else 'FAUX'} sur les {n} paires de nombres")
print(f"  portes : {total} {detail}  (dont 1 XOR pour le debordement V)")
print(f"  profondeur : {add4.profondeurs()}")
grands = {taille: additionneur(taille) for taille in (8, 16, 32, 64)}
for taille, add in grands.items():
    p = add.profondeurs()
    print(f"  {taille:>2} bits : {add.compte()[0]:>3} portes, "
          f"retenue finale apres {p['R']} portes, bit de poids fort apres {p[f'S{taille - 1}']}")
n8, f8 = verifier(grands[8], attendu_addition(8))
print(f"  8 bits verifie contre a + b : {'vrai' if not f8 else 'FAUX'} sur les {n8} paires")

# --- Exercice 6 : la soustraction -------------------------------------------------------------------------------
titre("Exercice 6 - soustraction en complement a deux : A - B = A + NON B + 1")
sub4 = soustracteur(4)
res = sub4.evaluer(**entrees_nombres(0b0101, 0b0011, 4), M=1)
print(f"  0101 - 0011 = {''.join(str(res[f'S{i}']) for i in (3, 2, 1, 0))}   (5 - 3 = {lire(res, 'S', 4)})")
res = sub4.evaluer(**entrees_nombres(0b0011, 0b0101, 4), M=1)
r = lire(res, "S", 4)
print(f"  0011 - 0101 = {''.join(str(res[f'S{i}']) for i in (3, 2, 1, 0))}   (3 - 5 = {signe(r, 4)} en complement a deux)")
n, fausses = verifier(sub4, attendu_soustraction(4))
total, detail = sub4.compte()
print(f"  M=0 additionne, M=1 soustrait : {'vrai' if not fausses else 'FAUX'} sur les {n} lignes")
print(f"  portes : {total} {detail}  (4 XOR de plus que l'additionneur, sans le debordement)")

# --- Le piege : le debordement ------------------------------------------------------------------------------------
titre("Le piege - retenue sortante et debordement ne sont pas la meme chose")
for a, b in ((0b0111, 0b0011), (0b1111, 0b0001), (0b1000, 0b1000)):
    res = add4.evaluer(**entrees_nombres(a, b, 4))
    s = lire(res, "S", 4)
    print(f"  {a:04b} + {b:04b} = {s:04b}  R={res['R']} V={res['V']}   "
          f"non signe : {a} + {b} -> {s}   signe : {signe(a, 4)} + {signe(b, 4)} -> {signe(s, 4)}")
compte = {"R": 0, "V": 0, "R sans V": 0, "V sans R": 0, "R et V": 0}
for a in range(16):
    for b in range(16):
        res = add4.evaluer(**entrees_nombres(a, b, 4))
        compte["R"] += res["R"]
        compte["V"] += res["V"]
        compte["R sans V"] += res["R"] and not res["V"]
        compte["V sans R"] += res["V"] and not res["R"]
        compte["R et V"] += res["R"] and res["V"]
print(f"  sur les 256 additions de 4 bits : {compte}")

# --- Exercice 7 : multiplexeur et decodeur ------------------------------------------------------------------------
titre("Multiplexeur 2 vers 1")
c = Circuit("A", "B", "SEL")
c.sortie("S", mux2(c, "A", "B", "SEL"))
montrer_table(c)
bilan(c, lambda A, B, SEL: {"S": B if SEL else A}, "S = A si SEL=0, B si SEL=1")

titre("Multiplexeur 4 vers 1 (trois 2 vers 1)")
c = Circuit("D0", "D1", "D2", "D3", "S1", "S0")
c.sortie("S", mux4(c, "D0", "D1", "D2", "D3", "S1", "S0"))
bilan(c, lambda D0, D1, D2, D3, S1, S0: {"S": [D0, D1, D2, D3][2 * S1 + S0]}, "S = D(S1 S0)")

titre("Decodeur 2 vers 4")
c = Circuit("A1", "A0")
for i, y in enumerate(decodeur2(c, "A1", "A0")):
    c.sortie(f"Y{i}", y)
montrer_table(c)
bilan(c, lambda A1, A0: {f"Y{i}": int(2 * A1 + A0 == i) for i in range(4)}, "Yi = 1 seulement pour i = A1 A0")

titre("Exercice 7 - la majorite avec un seul multiplexeur 4 vers 1")
print("  A et B choisissent l'entree ; la table dit ce qu'il faut y brancher :")
print("  AB = 00 -> 0   AB = 01 -> C   AB = 10 -> C   AB = 11 -> 1")
c = Circuit("A", "B", "C")
c.sortie("F", mux4(c, "0", "C", "C", "1", "A", "B"))
montrer_table(c)
bilan(c, lambda A, B, C: {"F": int(A + B + C >= 2)}, "F = majorite(A, B, C)")
print("  (le multiplexeur, ici 11 portes, remplace n'importe quelle fonction de 3 variables, avec au plus un NON"
      " pour C' ; la version de l'exercice 2 en a 4)")
