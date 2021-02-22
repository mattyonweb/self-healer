import unittest
import self_healing.self_healer as sh
import ast, astunparse

class BasicsTestCase(unittest.TestCase):

    def test_simple_comparison(self):
        s = "a < b"
        d = sh.m6.apply_mutations(ast.parse(s))

        self.assertTrue(len(list(d.keys())) == 1)

        results = [astunparse.unparse(m).strip() for m in d[(0,0,0)]]

        self.assertEqual(
            set(results),
            set(['(a < b)','(a <= b)','(a >= b)',
                 '(a > b)','(a == b)','(a != b)']))

    def test_not_comparison(self):
        s = "not a < b"

        mutants = set()
        for x in sh.m6.return_new_asts(ast.parse(s)):
            mutants.add(astunparse.unparse(x).strip())
        
        self.assertEqual(
            mutants, 
            set(["(not (a < b))",
                 "(not (a <= b))",
                 "(not (a >= b))",
                 "(not (a > b))",
                 "(not (a == b))",
                 "(not (a != b))"]))

    def test_triple_comparison(self):
        s = "a < d < c"

        mutants = set()
        for x in sh.m6.return_new_asts(ast.parse(s)):
            mutants.add(astunparse.unparse(x).strip())

        print(mutants)
        # BUG: ritorna {'(a != d)', '(a == d)', '(a >= d)', '(a <= d)', '(a > d)', '(a < d)'}
        
if __name__ == '__main__':
    unittest.main()
