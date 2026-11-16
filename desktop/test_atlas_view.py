"""Pure geometry tests for read-only geographic atlas."""
import unittest
from energymap import clip_hemisphere, project_orthographic, rings_from_features


class AtlasGeometryTests(unittest.TestCase):
    def test_orthographic_projects_visible_and_backside(self):
        x, y, depth = project_orthographic(-100, 30, -100)
        self.assertAlmostEqual(x, 0, places=4)
        self.assertGreater(depth, 0)
        self.assertLess(project_orthographic(80, 30, -100)[2], 0)

    def test_pins_stay_within_disc(self):
        for lon in range(-180, 180, 15):
            for lat in range(-75, 80, 15):
                x, y, _ = project_orthographic(lon, lat, 37)
                self.assertLessEqual(x*x + y*y, 1.00001)

    def test_pentagon_clipped_on_visible_hemisphere(self):
        polygon = [[-110, 25], [-80, 25], [-80, 50], [-110, 50], [-110, 25]]
        self.assertGreater(len(clip_hemisphere(polygon, -90)), 2)
        self.assertEqual(clip_hemisphere(polygon, 85), [])

    def test_polygon_and_multipolygon(self):
        geo = {'features': [
            {'name': 'A', 'geometry': {'type': 'Polygon', 'coordinates': [
                [[0, 0], [1, 0], [1, 1], [0, 0]]]}},
            {'name': 'B', 'geometry': {'type': 'MultiPolygon', 'coordinates': [
                [[[0, 0], [1, 0], [1, 1], [0, 0]]],
                [[[2, 0], [3, 0], [3, 1], [2, 0]]]]}}
        ]}
        self.assertEqual([n for n, _ in rings_from_features(geo)], ['A','B','B'])


if __name__ == '__main__':
    unittest.main()
