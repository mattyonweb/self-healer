import unittest
import self_healing.self_healer as sh
import ast, astunparse

class BasicsTestCase(unittest.TestCase):

    def test_find_name(self):
        s = "a < b"
        d = sh.m6.apply_mutations(ast.parse(s))

        self.assertTrue(len(list(d.keys())) == 1)

        results = [astunparse.unparse(m).strip() for m in d[(0,0,0)]]

        self.assertEqual(
            set(results),
            set(['(a < b)','(a <= b)','(a >= b)',
                 '(a > b)','(a == b)','(a != b)']))

        
if __name__ == '__main__':
    unittest.main()
