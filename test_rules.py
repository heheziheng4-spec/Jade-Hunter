import unittest
from dataclasses import asdict
from rules import Village

class RulesTests(unittest.TestCase):
    def test_end_to_end(self):
        v=Village()
        for a in ['elder','canal','cache0','cache1','cache2','dam']+['rest']*4+['jade','altar','altar']:v.act(a)
        self.assertTrue(v.won);self.assertEqual((v.food,v.material,v.population),(16,10,6))
    def test_flood_changes_outcome(self):
        a=Village(canal=True,dam=True);b=Village(canal=True)
        for _ in range(5):a.act('rest');b.act('rest')
        self.assertEqual(a.food-b.food,8)
    def test_duplicate_collection(self):
        v=Village();v.act('cache0');v.act('cache0');self.assertEqual(v.material,8)
    def test_insufficient_resources(self):
        v=Village();v.act('dam');v.act('altar')
        self.assertEqual(v.material,4);self.assertFalse(v.dam or v.shrine)
    def test_job_boundaries(self):
        v=Village()
        for _ in range(20):v.act('farm')
        self.assertEqual(v.farmers,6)
        for _ in range(20):v.act('workshop')
        self.assertEqual(v.farmers,0)
    def test_famine_and_terminal_state(self):
        v=Village()
        for _ in range(30):v.act('rest')
        self.assertEqual(v.population,0);self.assertEqual(v.food,0)
        old=asdict(v);v.act('cache0');self.assertEqual(old,asdict(v))
    def test_victory_gates(self):
        v=Village(material=30,food=30);v.act('altar');v.act('altar');self.assertFalse(v.won)
        v.day=4;v.act('altar');self.assertFalse(v.won)
        v.act('jade');v.act('altar');self.assertTrue(v.won)
    def test_state_roundtrip(self):
        v=Village();v.act('canal');v.act('rest');self.assertEqual(v,Village(**asdict(v)))

if __name__=='__main__':unittest.main()
