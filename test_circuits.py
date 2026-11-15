"""Tests : chaque resultat cite dans la video est verifie ici.

    python -m unittest -v
"""
import unittest

from circuits import (Circuit, additionneur, additionneur_complet, attendu_addition, attendu_soustraction, decodeur2,
                      demi_additionneur, entrees_nombres, lire, mux2, mux4, signe, soustracteur, verifier)


def majorite(A, B, C):
    return {"F": int(A + B + C >= 2)}


class TestCircuit(unittest.TestCase):

    def test_une_porte_inconnue_est_refusee(self):
        """Une faute de frappe dans un type de porte leve une erreur au lieu de fausser le circuit."""
        # GIVEN
        c = Circuit("A", "B")
        # WHEN / THEN
        with self.assertRaises(ValueError):
            c.porte("ETT", "A", "B")

    def test_un_signal_inconnu_est_refuse(self):
        """On ne peut brancher une porte que sur une entree ou une porte deja posee : pas de boucle possible."""
        # GIVEN
        c = Circuit("A")
        # WHEN / THEN
        with self.assertRaises(ValueError):
            c.porte("ET", "A", "B")

    def test_une_entree_ne_peut_pas_s_appeler_comme_une_porte(self):
        """Noms d'entree interdits : « 0 », « 1 », un doublon, ou un nom avec # (reserve aux portes)."""
        # GIVEN
        mauvais = [("0", "B"), ("A", "A"), ("et#1", "B")]
        # WHEN / THEN
        for entrees in mauvais:
            with self.assertRaises(ValueError):
                Circuit(*entrees)

    def test_une_entree_vaut_0_ou_1(self):
        """Un 2 tape par erreur leve une erreur au lieu de donner une table absurde."""
        # GIVEN
        c = Circuit("A")
        c.sortie("F", c.porte("NON", "A"))
        # WHEN / THEN
        with self.assertRaises(ValueError):
            c.evaluer(A=2)

    def test_un_nombre_trop_grand_est_refuse(self):
        """16 ne tient pas sur 4 bits : pas de troncature silencieuse."""
        # GIVEN
        a, b = 16, 1
        # WHEN / THEN
        with self.assertRaises(ValueError):
            entrees_nombres(a, b, 4)

    def test_la_profondeur_compte_les_portes_du_plus_long_chemin(self):
        """NAND(NAND(A,B), NAND(A,C)) : deux portes traversees au pire."""
        # GIVEN
        c = Circuit("A", "B", "C")
        c.sortie("F", c.porte("NAND", c.porte("NAND", "A", "B"), c.porte("NAND", "A", "C")))
        # WHEN
        profondeur = c.profondeurs()
        # THEN
        self.assertEqual(profondeur, {"F": 2})


class TestExercices(unittest.TestCase):

    def test_exercice_1_nand_nand_donne_a_fois_b_plus_c(self):
        """Exercice 1 : NAND(NAND(A,B), NAND(A,C)) = A(B + C) sur les 8 lignes."""
        # GIVEN
        c = Circuit("A", "B", "C")
        c.sortie("F", c.porte("NAND", c.porte("NAND", "A", "B"), c.porte("NAND", "A", "C")))
        # WHEN
        n, fausses = verifier(c, lambda A, B, C: {"F": A & (B | C)})
        # THEN
        self.assertEqual((n, fausses), (8, []))

    def test_exercice_2_majorite_en_quatre_portes(self):
        """Exercice 2 : AB + AC + BC fait la majorite avec 3 ET et 1 OU."""
        # GIVEN
        c = Circuit("A", "B", "C")
        c.sortie("F", c.porte("OU", c.porte("ET", "A", "B"), c.porte("ET", "A", "C"), c.porte("ET", "B", "C")))
        # WHEN
        _, fausses = verifier(c, majorite)
        # THEN
        self.assertEqual(fausses, [])
        self.assertEqual(c.compte(), (4, {"ET": 3, "OU": 1}))

    def test_nand_est_universelle(self):
        """NON, ET et OU se construisent avec des NAND seulement (1, 2 et 3 portes)."""
        # GIVEN
        non_, et_, ou_ = Circuit("A", "B"), Circuit("A", "B"), Circuit("A", "B")
        non_.sortie("F", non_.porte("NAND", "A", "A"))
        n = et_.porte("NAND", "A", "B")
        et_.sortie("F", et_.porte("NAND", n, n))
        ou_.sortie("F", ou_.porte("NAND", ou_.porte("NAND", "A", "A"), ou_.porte("NAND", "B", "B")))
        # WHEN / THEN
        self.assertEqual(verifier(non_, lambda A, B: {"F": 1 - A})[1], [])
        self.assertEqual(verifier(et_, lambda A, B: {"F": A & B})[1], [])
        self.assertEqual(verifier(ou_, lambda A, B: {"F": A | B})[1], [])
        self.assertEqual([x.compte()[0] for x in (non_, et_, ou_)], [1, 2, 3])

    def test_exercice_3_xor_avec_quatre_nand(self):
        """Exercice 3 : quatre NAND font un XOR, en trois niveaux."""
        # GIVEN
        c = Circuit("A", "B")
        n1 = c.porte("NAND", "A", "B")
        c.sortie("F", c.porte("NAND", c.porte("NAND", "A", n1), c.porte("NAND", "B", n1)))
        # WHEN
        _, fausses = verifier(c, lambda A, B: {"F": A ^ B})
        # THEN
        self.assertEqual(fausses, [])
        self.assertEqual((c.compte()[0], c.profondeurs()["F"]), (4, 3))

    def test_un_ou_n_est_pas_un_xor(self):
        """L'erreur classique : un OU a la place du XOR n'est faux que sur la ligne 1 1."""
        # GIVEN
        c = Circuit("A", "B")
        c.sortie("F", c.porte("OU", "A", "B"))
        # WHEN
        _, fausses = verifier(c, lambda A, B: {"F": A ^ B})
        # THEN
        self.assertEqual([(v["A"], v["B"]) for v, _, _ in fausses], [(1, 1)])

    def test_demi_additionneur(self):
        """Somme = A XOR B, retenue = A ET B."""
        # GIVEN
        c = Circuit("A", "B")
        s, r = demi_additionneur(c, "A", "B")
        c.sortie("S", s)
        c.sortie("R", r)
        # WHEN
        _, fausses = verifier(c, lambda A, B: {"S": (A + B) % 2, "R": (A + B) // 2})
        # THEN
        self.assertEqual(fausses, [])

    def test_exercice_4_additionneur_complet(self):
        """Exercice 4 : deux demi-additionneurs et un OU, 5 portes, juste sur les 8 lignes."""
        # GIVEN
        c = Circuit("A", "B", "Re")
        s, r = additionneur_complet(c, "A", "B", "Re")
        c.sortie("S", s)
        c.sortie("Rs", r)
        # WHEN
        _, fausses = verifier(c, lambda A, B, Re: {"S": (A + B + Re) % 2, "Rs": (A + B + Re) // 2})
        # THEN
        self.assertEqual(fausses, [])
        self.assertEqual(c.compte()[0], 5)
        self.assertEqual(c.profondeurs(), {"S": 2, "Rs": 3})

    def test_les_deux_retenues_internes_ne_valent_jamais_1_ensemble(self):
        """Lues dans le circuit : R1 et R2 ne valent jamais 1 sur la meme ligne, donc un OU suffit."""
        # GIVEN
        c = Circuit("A", "B", "Re")
        internes = []
        additionneur_complet(c, "A", "B", "Re", internes)
        c.sortie("R1", internes[0])
        c.sortie("R2", internes[1])
        # WHEN
        ensemble = [v for v, o in c.table() if o["R1"] and o["R2"]]
        # THEN
        self.assertEqual(ensemble, [])

    def test_exercice_5_additionneur_4_bits_sur_les_256_paires(self):
        """Exercice 5 : 0101 + 0011 = 1000, et juste (somme, R, V) pour toutes les paires de 4 bits."""
        # GIVEN
        add = additionneur(4)
        # WHEN
        res = add.evaluer(**entrees_nombres(5, 3, 4))
        n, fausses = verifier(add, attendu_addition(4))
        # THEN
        self.assertEqual((lire(res, "S", 4), res["R"]), (8, 0))
        self.assertEqual((n, fausses), (256, []))
        self.assertEqual(add.compte()[0], 21)

    def test_la_retenue_traverse_toute_la_chaine(self):
        """Profondeurs citees : S0 2, S3 8, R 9 sur 4 bits ; retenue finale 65 sur 32 bits, 129 sur 64."""
        # GIVEN
        tailles = (4, 32, 64)
        # WHEN
        p = {n: additionneur(n).profondeurs() for n in tailles}
        # THEN
        self.assertEqual((p[4]["S0"], p[4]["S3"], p[4]["R"]), (2, 8, 9))
        self.assertEqual((p[32]["R"], p[64]["R"]), (65, 129))

    def test_exercice_6_soustraction(self):
        """Exercice 6 : 0101 - 0011 = 0010, 0011 - 0101 = 1110 (-2), et M=0 additionne toujours."""
        # GIVEN
        sub = soustracteur(4)
        # WHEN
        a = lire(sub.evaluer(**entrees_nombres(5, 3, 4), M=1), "S", 4)
        b = lire(sub.evaluer(**entrees_nombres(3, 5, 4), M=1), "S", 4)
        n, fausses = verifier(sub, attendu_soustraction(4))
        # THEN
        self.assertEqual((a, signe(b, 4)), (2, -2))
        self.assertEqual((n, fausses), (512, []))
        self.assertEqual(sub.compte()[0], 24)


class TestPiege(unittest.TestCase):

    def test_7_plus_3_deborde_sans_retenue(self):
        """0111 + 0011 = 1010 : pas de retenue sortante, mais -6 en signe : V = 1."""
        # GIVEN
        add = additionneur(4)
        # WHEN
        res = add.evaluer(**entrees_nombres(7, 3, 4))
        # THEN
        self.assertEqual((signe(lire(res, "S", 4), 4), res["R"], res["V"]), (-6, 0, 1))

    def test_moins_1_plus_1_retenue_sans_debordement(self):
        """1111 + 0001 = 0000 : retenue sortante, mais -1 + 1 = 0 est juste : V = 0."""
        # GIVEN
        add = additionneur(4)
        # WHEN
        res = add.evaluer(**entrees_nombres(15, 1, 4))
        # THEN
        self.assertEqual((lire(res, "S", 4), res["R"], res["V"]), (0, 1, 0))

    def test_le_debordement_est_juste_sur_les_256_paires(self):
        """V vaut 1 exactement quand la somme signee sort de [-8, 7] ; R et V different sur 112 paires."""
        # GIVEN
        add = additionneur(4)
        # WHEN
        resultats = [(a, b, add.evaluer(**entrees_nombres(a, b, 4))) for a in range(16) for b in range(16)]
        # THEN
        self.assertEqual(verifier(add, attendu_addition(4))[1], [])
        self.assertEqual(sum(r["R"] != r["V"] for _, _, r in resultats), 112)


class TestMultiplexeurs(unittest.TestCase):

    def test_mux2(self):
        """S = A si SEL = 0, B si SEL = 1."""
        # GIVEN
        c = Circuit("A", "B", "SEL")
        c.sortie("S", mux2(c, "A", "B", "SEL"))
        # WHEN / THEN
        self.assertEqual(verifier(c, lambda A, B, SEL: {"S": B if SEL else A})[1], [])

    def test_mux4_sur_les_64_lignes(self):
        """Le multiplexeur 4 vers 1 rend l'entree dont le numero est S1 S0."""
        # GIVEN
        c = Circuit("D0", "D1", "D2", "D3", "S1", "S0")
        c.sortie("S", mux4(c, "D0", "D1", "D2", "D3", "S1", "S0"))
        # WHEN
        n, fausses = verifier(c, lambda D0, D1, D2, D3, S1, S0: {"S": [D0, D1, D2, D3][2 * S1 + S0]})
        # THEN
        self.assertEqual((n, fausses), (64, []))
        self.assertEqual(c.compte()[0], 11)

    def test_decodeur(self):
        """Une seule sortie a 1, celle dont le numero est A1 A0."""
        # GIVEN
        c = Circuit("A1", "A0")
        for i, y in enumerate(decodeur2(c, "A1", "A0")):
            c.sortie(f"Y{i}", y)
        # WHEN / THEN
        self.assertEqual(verifier(c, lambda A1, A0: {f"Y{i}": int(2 * A1 + A0 == i) for i in range(4)})[1], [])

    def test_exercice_7_majorite_par_multiplexeur(self):
        """Exercice 7 : un MUX 4 vers 1 avec les entrees 0, C, C, 1 fait la majorite."""
        # GIVEN
        c = Circuit("A", "B", "C")
        c.sortie("F", mux4(c, "0", "C", "C", "1", "A", "B"))
        # WHEN
        _, fausses = verifier(c, majorite)
        # THEN
        self.assertEqual(fausses, [])


if __name__ == "__main__":
    unittest.main()
