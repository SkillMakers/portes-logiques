"""Portes logiques et circuits combinatoires : un simulateur porte par porte, qui verifie chaque exercice de la video.

Un circuit est une liste de portes reliees entre elles. Le programme le fait tourner sur TOUTES les combinaisons
de ses entrees (sa table de verite complete) et le compare a ce qu'il doit calculer. Il compte aussi les portes,
et la profondeur du circuit : le plus long chemin, en nombre de portes, entre une entree et une sortie. C'est
elle qui fixe le temps de reponse d'un vrai circuit, puisque chaque porte ajoute son propre delai.

    python demo.py           # les exercices de la video
    python -m unittest -v    # les tests
"""
from collections import Counter
from itertools import product

# Les sept portes de la video. Chacune prend des bits (0 ou 1) et rend un bit.
OPERATIONS = {
    "NON": lambda xs: 1 - xs[0],
    "ET": lambda xs: int(all(xs)),
    "OU": lambda xs: int(any(xs)),
    "NAND": lambda xs: 1 - int(all(xs)),
    "NOR": lambda xs: 1 - int(any(xs)),
    "XOR": lambda xs: sum(xs) % 2,
    "XNOR": lambda xs: 1 - sum(xs) % 2,
}


class Circuit:
    """Un circuit combinatoire : des entrees, des portes, des sorties.

    Chaque porte lit des entrees du circuit ou les sorties de portes deja posees : on ne peut donc pas fabriquer
    de boucle, et l'ordre d'ajout est un ordre d'evaluation valable. Les signaux "0" et "1" sont des constantes.
    Les portes s'appellent "et#1", "ou#2"… : le # est interdit dans un nom d'entree, une porte ne peut donc pas
    prendre le nom d'une entree.
    """

    def __init__(self, *entrees):
        if len(set(entrees)) != len(entrees):
            raise ValueError(f"entree en double : {entrees}")
        for e in entrees:
            if e in ("0", "1") or "#" in e or not e:
                raise ValueError(f"nom d'entree interdit : {e!r}")
        self.entrees = list(entrees)
        self.portes = []          # (nom, type, [sources])
        self.sorties = {}         # nom de sortie -> signal
        self._noms = set(self.entrees) | {"0", "1"}

    def porte(self, type_, *sources):
        """Ajoute une porte et rend le nom de son signal de sortie."""
        if type_ not in OPERATIONS:
            raise ValueError(f"porte inconnue : {type_}")
        if type_ == "NON" and len(sources) != 1:
            raise ValueError("une porte NON a une seule entree")
        if type_ != "NON" and len(sources) < 2:
            raise ValueError(f"une porte {type_} a au moins deux entrees")
        for s in sources:
            if s not in self._noms:
                raise ValueError(f"signal inconnu : {s}")
        nom = f"{type_.lower()}#{len(self.portes) + 1}"
        self.portes.append((nom, type_, list(sources)))
        self._noms.add(nom)
        return nom

    def sortie(self, nom, signal):
        if signal not in self._noms:
            raise ValueError(f"signal inconnu : {signal}")
        self.sorties[nom] = signal

    def evaluer(self, **valeurs):
        """Fait tourner le circuit sur une ligne : evaluer(A=1, B=0) -> {"S": 1, ...}."""
        if set(valeurs) != set(self.entrees):
            raise ValueError(f"il faut une valeur pour chaque entree : {self.entrees}")
        if any(v not in (0, 1) for v in valeurs.values()):
            raise ValueError(f"une entree vaut 0 ou 1 : {valeurs}")
        v = {"0": 0, "1": 1, **valeurs}
        for nom, type_, sources in self.portes:
            v[nom] = OPERATIONS[type_]([v[s] for s in sources])
        return {s: v[sig] for s, sig in self.sorties.items()}

    def table(self):
        """La table de verite complete : une ligne par combinaison des entrees, dans l'ordre binaire."""
        lignes = []
        for bits in product((0, 1), repeat=len(self.entrees)):
            valeurs = dict(zip(self.entrees, bits))
            lignes.append((valeurs, self.evaluer(**valeurs)))
        return lignes

    def compte(self):
        """Nombre de portes par type, et au total."""
        c = Counter(type_ for _, type_, _ in self.portes)
        return sum(c.values()), dict(sorted(c.items()))

    def profondeurs(self):
        """Pour chaque sortie, le plus long chemin en nombre de portes depuis une entree.

        Une entree ou une constante est a la profondeur 0 ; une porte est a 1 + la plus grande profondeur de ses
        sources. Chaque porte traversee ajoute son delai : c'est le chemin le plus long qui fixe la vitesse.
        """
        p = {s: 0 for s in (*self.entrees, "0", "1")}
        for nom, _, sources in self.portes:
            p[nom] = 1 + max(p[s] for s in sources)
        return {s: p[sig] for s, sig in self.sorties.items()}


def verifier(circuit, attendu):
    """Compare le circuit a une fonction Python sur TOUTES les lignes de sa table de verite.

    attendu(**entrees) rend un dict {sortie: bit}, pour toutes les sorties ou pour une partie d'entre elles.
    Renvoie (lignes testees, liste des lignes fausses).
    """
    fausses = []
    lignes = circuit.table()
    for valeurs, obtenu in lignes:
        voulu = attendu(**valeurs)
        if {s: obtenu[s] for s in voulu} != voulu:
            fausses.append((valeurs, obtenu, voulu))
    return len(lignes), fausses


# --- Briques de base ---------------------------------------------------------------------------------------

def demi_additionneur(c, a, b):
    """Additionne deux bits : somme = A XOR B, retenue = A ET B. Deux portes."""
    return c.porte("XOR", a, b), c.porte("ET", a, b)


def additionneur_complet(c, a, b, r_entree, internes=None):
    """Additionne deux bits et une retenue entrante, avec deux demi-additionneurs et une porte OU.

    Le premier additionne A et B ; le second ajoute la retenue a leur somme. Les deux retenues ne peuvent pas
    valoir 1 en meme temps : un OU suffit pour les reunir (la demo le verifie sur le circuit lui-meme).
    Si `internes` est une liste, on y ajoute les deux retenues internes, pour pouvoir les observer.
    """
    s1, r1 = demi_additionneur(c, a, b)
    s, r2 = demi_additionneur(c, s1, r_entree)
    if internes is not None:
        internes.extend([r1, r2])
    return s, c.porte("OU", r1, r2)


def noms(prefixe, n):
    """noms("A", 4) -> ["A3", "A2", "A1", "A0"] : le bit de poids fort d'abord, comme on ecrit un nombre."""
    return [f"{prefixe}{i}" for i in reversed(range(n))]


def additionneur(n):
    """Additionneur n bits a propagation de retenue : n additionneurs complets en chaine.

    La retenue du bit i entre dans le bit i + 1 : le bit de poids fort attend toute la chaine.
    Sorties : S(n-1)..S0, la retenue sortante R, et V, le debordement en complement a deux.
    """
    c = Circuit(*noms("A", n), *noms("B", n))
    retenue, retenues = "0", []
    for i in range(n):
        s, retenue = additionneur_complet(c, f"A{i}", f"B{i}", retenue)
        c.sortie(f"S{i}", s)
        retenues.append(retenue)
    c.sortie("R", retenue)
    # Debordement en complement a deux : la retenue qui ENTRE dans le bit de signe differe de celle qui en SORT.
    entree_signe = retenues[-2] if n > 1 else "0"
    c.sortie("V", c.porte("XOR", entree_signe, retenue))
    return c


def soustracteur(n):
    """A - B en complement a deux : A + (NON B) + 1, avec le meme additionneur.

    Une porte XOR par bit inverse B quand M = 1, et M entre comme retenue initiale : c'est le « + 1 ».
    Avec M = 0, le meme circuit additionne. Sorties : S(n-1)..S0 et R.
    """
    c = Circuit(*noms("A", n), *noms("B", n), "M")
    retenue = "M"
    for i in range(n):
        b = c.porte("XOR", f"B{i}", "M")
        s, retenue = additionneur_complet(c, f"A{i}", b, retenue)
        c.sortie(f"S{i}", s)
    c.sortie("R", retenue)
    return c


def mux2(c, a, b, sel, sel_barre=None):
    """Multiplexeur 2 vers 1 : rend A si SEL = 0, B si SEL = 1.  S = A.SEL' + B.SEL.

    Quatre portes, dont un NON pour SEL'. Si SEL' existe deja (sel_barre), on le reutilise : trois portes.
    """
    sel_barre = sel_barre or c.porte("NON", sel)
    return c.porte("OU", c.porte("ET", a, sel_barre), c.porte("ET", b, sel))


def mux4(c, d0, d1, d2, d3, s1, s0):
    """Multiplexeur 4 vers 1, fait de trois multiplexeurs 2 vers 1 : S1 S0 = 00 -> D0, 01 -> D1, 10 -> D2, 11 -> D3.

    Les deux premiers partagent la meme selection S0 : ils partagent aussi son inverse. 11 portes.
    """
    s0_barre = c.porte("NON", s0)
    return mux2(c, mux2(c, d0, d1, s0, s0_barre), mux2(c, d2, d3, s0, s0_barre), s1)


def decodeur2(c, a1, a0):
    """Decodeur 2 vers 4 : une seule des quatre sorties vaut 1, celle dont le numero est A1 A0."""
    n1, n0 = c.porte("NON", a1), c.porte("NON", a0)
    return [c.porte("ET", n1, n0), c.porte("ET", n1, a0), c.porte("ET", a1, n0), c.porte("ET", a1, a0)]


# --- Lire les nombres ---------------------------------------------------------------------------------------

def signe(valeur, n):
    """Lit n bits en complement a deux : 1010 sur 4 bits vaut -6, 0111 vaut 7."""
    return valeur - (1 << n) if valeur >> (n - 1) else valeur


def entrees_nombres(a, b, n):
    """Les valeurs d'entree d'un additionneur pour les nombres a et b (entiers de 0 a 2^n - 1)."""
    if not (0 <= a < 1 << n and 0 <= b < 1 << n):
        raise ValueError(f"{a} et {b} doivent tenir sur {n} bits (0 a {(1 << n) - 1})")
    v = {f"A{i}": (a >> i) & 1 for i in range(n)}
    v.update({f"B{i}": (b >> i) & 1 for i in range(n)})
    return v


def lire(valeurs, prefixe, n):
    """Relit le nombre forme par les signaux prefixe(n-1)..prefixe0 (sorties S, ou entrees A et B)."""
    return sum(valeurs[f"{prefixe}{i}"] << i for i in range(n))


def attendu_addition(n):
    """Ce qu'un additionneur n bits doit rendre : la somme sur n bits, la retenue R, et le debordement V."""
    def attendu(**v):
        a, b = lire(v, "A", n), lire(v, "B", n)
        somme_signee = signe(a, n) + signe(b, n)
        return {**{f"S{i}": ((a + b) >> i) & 1 for i in range(n)},
                "R": int(a + b >= 1 << n),
                "V": int(not -(1 << (n - 1)) <= somme_signee < 1 << (n - 1))}
    return attendu


def attendu_soustraction(n):
    """Ce que le soustracteur doit rendre : A + B si M = 0, A - B (modulo 2^n) si M = 1, et la retenue R."""
    def attendu(M, **v):
        a, b = lire(v, "A", n), lire(v, "B", n)
        total = a + b if M == 0 else a + ((1 << n) - 1 - b) + 1
        return {**{f"S{i}": (total >> i) & 1 for i in range(n)}, "R": int(total >= 1 << n)}
    return attendu
