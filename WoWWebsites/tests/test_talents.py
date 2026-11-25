import unittest

from wowweb.catalog import resolve
from wowweb.html.guide import talent_page
from wowweb.talents import Talent, Tree, can_spend, can_unspend, encode_build, parse_build, trees_for
from wowweb.talents.models import _t


# Two trees. Arrow requires Focus. Deep sits on row 1 and has no arrow.
TREES = (
    Tree(
        "Arms",
        (
            Talent("Strike", 5, 0, 0),
            Talent("Focus", 3, 1, 0),
            Talent("Arrow", 1, 2, 0, requires="Focus"),
            Talent("Deep", 1, 0, 1),
        ),
    ),
    Tree("Fury", (Talent("Rage", 5, 0, 0),)),
)
STRIKE, FOCUS, ARROW, DEEP, RAGE = range(5)


class TalentRuleTests(unittest.TestCase):
    def test_row_is_blocked_until_the_tree_has_five_points(self):
        self.assertTrue(can_spend(TREES, [0, 0, 0, 0, 0], STRIKE, 51))
        self.assertFalse(can_spend(TREES, [0, 0, 0, 0, 0], DEEP, 51))
        self.assertFalse(can_spend(TREES, [4, 0, 0, 0, 0], DEEP, 51))
        self.assertFalse(can_spend(TREES, [2, 2, 0, 0, 0], DEEP, 51))
        self.assertTrue(can_spend(TREES, [5, 0, 0, 0, 0], DEEP, 51))
        self.assertTrue(can_spend(TREES, [2, 3, 0, 0, 0], DEEP, 51))
        # Points in the other tree do not open this one.
        self.assertFalse(can_spend(TREES, [0, 0, 0, 0, 5], DEEP, 51))
        self.assertFalse(can_spend(TREES, [5, 0, 0, 0, 0], STRIKE, 51))

    def test_required_talent_blocks_until_it_is_maxed(self):
        self.assertFalse(can_spend(TREES, [0, 0, 0, 0, 0], ARROW, 51))
        self.assertFalse(can_spend(TREES, [0, 2, 0, 0, 0], ARROW, 51))
        self.assertTrue(can_spend(TREES, [0, 3, 0, 0, 0], ARROW, 51))
        # Tier still applies when the arrow is already satisfied.
        self.assertFalse(can_spend(TREES, [1, 3, 0, 0, 0], DEEP, 51))

    def test_unspend_blocked_while_higher_row_has_points(self):
        # 4 below + 1 on row 1 is the whole gate. One less strands Deep.
        self.assertFalse(can_unspend(TREES, [4, 0, 0, 1, 0], STRIKE))
        self.assertTrue(can_unspend(TREES, [4, 0, 0, 1, 0], DEEP))
        # A spare point can come out; five points remain in the tree.
        self.assertTrue(can_unspend(TREES, [5, 0, 0, 1, 0], STRIKE))
        self.assertFalse(can_unspend(TREES, [0, 0, 0, 0, 0], STRIKE))

    def test_unspend_blocked_while_a_dependent_is_invested(self):
        self.assertFalse(can_unspend(TREES, [0, 3, 1, 0, 0], FOCUS))
        self.assertTrue(can_unspend(TREES, [0, 3, 1, 0, 0], ARROW))
        self.assertTrue(can_unspend(TREES, [0, 3, 0, 0, 0], FOCUS))

    def test_max_points_zero_blocks_spending(self):
        self.assertFalse(can_spend(TREES, [0, 0, 0, 0, 0], STRIKE, 0))
        self.assertFalse(can_spend(TREES, [0, 0, 0, 0, 0], RAGE, 0))
        self.assertFalse(can_spend(TREES, [1, 0, 0, 0, 1], FOCUS, 2))
        self.assertTrue(can_spend(TREES, [1, 0, 0, 0, 0], FOCUS, 2))

    def test_build_round_trip(self):
        ranks = parse_build(TREES, "53110")
        self.assertEqual(ranks, [5, 3, 1, 1, 0])
        self.assertEqual(parse_build(TREES, encode_build(ranks)), ranks)
        short = parse_build(TREES, "53x1")
        self.assertEqual(encode_build(short), "53100")
        self.assertEqual(parse_build(TREES, encode_build(short)), short)

    def test_existing_constructor_keeps_empty_requires(self):
        mortal = _t("Mortal Strike", 1, 1, 5, "A vicious strike")
        self.assertEqual(mortal.desc, "A vicious strike")
        self.assertEqual(mortal.requires, "")
        improved = _t("Improved Mortal Strike", 5, 1, 6, "", "Mortal Strike")
        self.assertEqual(improved.requires, "Mortal Strike")
        trees = trees_for(resolve("vanilla"), "mage")
        self.assertTrue(all(tal.requires == "" for tree in trees for tal in tree.talents))

    def test_page_emits_tree_row_and_requires(self):
        html = talent_page(resolve("vanilla"), "warrior", TREES, [0, 3, 0, 0, 0], 51, "03000")
        self.assertIn('data-i="2" data-max="1" data-tree="0" data-row="0" data-requires="1"', html)
        self.assertIn('data-i="3" data-max="1" data-tree="0" data-row="1" data-requires=""', html)
        self.assertIn('data-i="4" data-max="5" data-tree="1" data-row="0" data-requires=""', html)
        self.assertIn("3/3", html)
        self.assertIn("0/5", html)


if __name__ == "__main__":
    unittest.main()
