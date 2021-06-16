import networkx as nx
from tsmpy import TSM
from matplotlib import pyplot as plt
import unittest


class TestRefine(unittest.TestCase):
    def test_convex(self): # 凸
        e = [(i, i + 1) for i in range(7)] + [(7, 0)]
        G = nx.Graph(e)
        pos = {0: (0, 0), 1: (0, 1), 2: (1, 1), 3: (1, 2),
            4: (2, 2), 5: (2, 1), 6: (3, 1), 7: (3, 0)}

        tsm = TSM(G, pos)
        tsm.display()
        plt.savefig("test/outputs/convex.svg")
        plt.close()

    def test_cross(self): # 十
        e = [(i, i + 1) for i in range(11)] + [(11, 0)]
        G = nx.Graph(e)
        pos = {0: (0, 0), 1: (0, 1), 2: (1, 1), 3: (1, 2),
            4: (2, 2), 5: (2, 1), 6: (3, 1), 7: (3, 0),
            8: (2, 0), 9: (2, -1), 10: (1, -1), 11: (1, 0),
            }
        tsm = TSM(G, pos)
        tsm.display()
        plt.savefig("test/outputs/cross.svg")
        plt.close()

class TestGML(unittest.TestCase):
    @staticmethod
    def _test(filename, uselp):
        G = nx.Graph(nx.read_gml(filename))
        pos = {node: eval(node) for node in G}

        # shortify node name
        node_dict = {v: i for i, v in enumerate(pos)}
        G = nx.Graph([node_dict[u], node_dict[v]] for u, v in G.edges)
        pos = {node_dict[k]: v for k, v in pos.items()}

        tsm = TSM(G, pos, uselp=uselp)
        tsm.display()
        plt.savefig(filename.replace(
            "inputs", "outputs").replace(".gml", f".{'lp' if uselp else 'nolp'}.svg"))
        plt.close()


    def test_4_nocut(self): # no cut edge
        TestGML._test("test/inputs/case4.gml", False)
        TestGML._test("test/inputs/case4.gml", True)

    def test_2_nocut(self): # no cut edge
        TestGML._test("test/inputs/case2.gml", False)
        TestGML._test("test/inputs/case2.gml", True)

    def test_5_2cut_external(self): # a small graph, has two external cut-edges
        TestGML._test("test/inputs/case5.gml", False)
        TestGML._test("test/inputs/case5.gml", True)

    def test_7_1cut_internal(self): # a small graph, has one internal cut-edge
        TestGML._test("test/inputs/case7.gml", False)
        TestGML._test("test/inputs/case7.gml", True)

    def test_8_cut_external(self): # external face has cut-edges, simpler that case1
        TestGML._test("test/inputs/case8.gml", False)
        TestGML._test("test/inputs/case8.gml", True)

    def test_1_cut_external(self): # external face has cut-edges
        TestGML._test("test/inputs/case1.gml", False)
        TestGML._test("test/inputs/case1.gml", True)

    def test_6_cut_internal(self): # internal face has cut-edges
        TestGML._test("test/inputs/case6.gml", False)
        TestGML._test("test/inputs/case6.gml", True)

    def test_3_cut_both(self): # inner face has cut-edges (most difficult
        TestGML._test("test/inputs/case3.gml", False)
        TestGML._test("test/inputs/case3.gml", True)


class TestGrid(unittest.TestCase):
    def _test_grid(i, j):
        G = nx.grid_2d_graph(i, j)
        pos = {node: node for node in G}
        tsm = TSM(G, pos)
        tsm.display()
        plt.savefig(f"test/outputs/grid_{i}x{j}.svg")
        plt.close()

    def test_2x1(self):
        TestGrid._test_grid(2, 1)

    def test_1x5(self):
        TestGrid._test_grid(1, 5)

    def test_1x2(self):
        TestGrid._test_grid(1, 2)

    def test_5x5(self):
        TestGrid._test_grid(5, 5)

    def test_3x3(self):
        TestGrid._test_grid(3, 3)

    def test_2x2(self):
        TestGrid._test_grid(2, 2)

    def test_1x99(self):
        TestGrid._test_grid(1, 99)



if __name__ == '__main__':
    res = unittest.main(verbosity=3, exit=False)
