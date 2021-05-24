import networkx as nx
from topology_shape_metrics.TSM import TSM
from topology_shape_metrics.utils import convert_pos_to_embedding
from topology_shape_metrics.DCEL import Dcel
import unittest
from matplotlib import pyplot as plt

class TestRefine(unittest.TestCase):
    def test(gml_filename): # 凸
        e = [(i, i + 1) for i in range(7)] + [(7, 0)]
        G = nx.Graph(e)
        pos = {0: (0, 0), 1: (0, 1), 2: (1, 1), 3: (1, 2),
            4: (2, 2), 5: (2, 1), 6: (3, 1), 7: (3, 0)}

        tsm = TSM(G, pos)
        tsm.display()
        plt.savefig("test/outputs/refine1.svg")
        plt.close()

    def test2(gml_filename): # 十
        e = [(i, i + 1) for i in range(11)] + [(11, 0)]
        G = nx.Graph(e)
        pos = {0: (0, 0), 1: (0, 1), 2: (1, 1), 3: (1, 2),
            4: (2, 2), 5: (2, 1), 6: (3, 1), 7: (3, 0),
            8: (2, 0), 9: (2, -1), 10: (1, -1), 11: (1, 0),
            }
        tsm = TSM(G, pos)
        tsm.display()
        plt.savefig("test/outputs/refin2.svg")
        plt.close()

class TestGML(unittest.TestCase):
    def _test(gml_filename, uselp=False):
        G = nx.Graph(nx.read_gml(gml_filename))
        pos = {node: eval(node) for node in G}

        # shortify node name
        node_dict = {v: i for i, v in enumerate(pos)}
        G = nx.Graph([node_dict[u], node_dict[v]] for u, v in G.edges)
        pos = {node_dict[k]: v for k, v in pos.items()}

        tsm = TSM(G, pos)
        tsm.display()
        plt.savefig(gml_filename.replace(
            "inputs", "outputs").replace(".gml", f".{'lp' if uselp else 'nolp'}.svg"))
        plt.close()


    def test_04(self): # no cut edge, convex
        TestGML._test("test/inputs/case4.gml")
        TestGML._test("test/inputs/case4.gml", uselp=True)

    def test_02(self):  # no cut edge, convex
        TestGML._test("test/inputs/case2.gml")
        TestGML._test("test/inputs/case2.gml", uselp=True)

    def test_01(self): # inner face has no cutedge
        TestGML._test("test/inputs/case1.gml")
        TestGML._test("test/inputs/case1.gml", uselp=True)

    def test_03(self): # inner face has cutedge (most difficult)
        TestGML._test("test/inputs/case3.gml")
        TestGML._test("test/inputs/case3.gml", uselp=True)





class TestGrid(unittest.TestCase):
    def _test_grid(i, j):
        G = nx.grid_2d_graph(i, j)
        pos = {node: node for node in G}
        TSM(G, pos)
        TSM(G)

    def test_01(self):
        TestGrid._test_grid(1, 2)

    def test_02(self):
        TestGrid._test_grid(2, 1)

    def test_03(self):
        TestGrid._test_grid(1, 5)

    def test_04(self):
        TestGrid._test_grid(5, 1)

    def test_05(self):
        TestGrid._test_grid(5, 5)

    def test_06(self):
        TestGrid._test_grid(3, 3)

    def test_07(self):
        TestGrid._test_grid(9, 9)


class TestDCEL(unittest.TestCase):
    def test_add_node_between(self):
        e = [(0, 1), (1, 2), (2, 0)]
        G = nx.Graph(e)
        pos = {0: (0, 0), 1: (1, 0), 2: (0, 1)}
        embedding = convert_pos_to_embedding(G, pos)
        dcel = Dcel(G, embedding)
        dcel.add_node_between(1, 3, 2)
        dcel.connect(dcel.faces[('face', 1)], 0, 3)
        assert dcel.half_edges[2, 3].succ.id == (3, 0)
        assert dcel.half_edges[3, 0].prev.id == (2, 3)
        assert dcel.half_edges[3, 0].succ.id == (0, 2)
        assert dcel.half_edges[0, 2].prev.id == (3, 0)

    def test02(self):
        e = [(0, 1), (1, 2), (2, 3), (3, 0)]
        G = nx.Graph(e)
        pos = {0: (0, 0), 1: (1, 0), 2: (2, 0), 3: (3, 0)}
        embedding = convert_pos_to_embedding(G, pos)
        dcel = Dcel(G, embedding)
        dcel.add_node_between(0, 4, 3)
        dcel.connect(dcel.faces[('face', 1)], 1, 4)
        dcel.add_node_between(4, 5, 3)
        dcel.connect(dcel.faces[('face', 1, 'r')], 2, 5)

if __name__ == '__main__':
    res = unittest.main(verbosity=3, exit=False)
