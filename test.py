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


class TestBend(unittest.TestCase):
    def test_bend(self):
        pos = {'0': [233.40717895650255, 245.2668161593756], '1': [197.16129504244714, 30], '2': [141.70696162531476, 231.32493034071877], '3': [60.65624829590422, 113.49167630171439], '4': [108.35736160598731, 76.64552177189921], '5': [87.0130296182083, 188.10311014236993], '6': [319.33416955603843, 259.2393822803765], '7': [30, 277.38385767958584], '8': [98.92200205792096, 284.1742280192017], '9': [179.4743438581056, 319.91589873409737], '10': [287.1444006787124, 72.41331541473198], '11': [31.12464635584422, 32.898914774980994], '12': [158.93331495445887, 99.4944443930458], '13': [
            139.43918552954983, 153.80882320636442], '14': [369.5136536406337, 104.14142146557003], '15': [290.598502710234, 165.863033803461], '16': [211.4553136831521, 174.1784364618411], '17': [228.30221376063673, 102.81798218614415], '18': [37.389296631515435, 206.8668863010132], '19': [387.48004971189835, 189.04480920874767], 'cdnode1': [70.62903289986328, 215.04295834065474], 'cdnode2': [91.39401162703457, 219.91146037454223], 'cdnode3': [98.17352514597789, 132.9352577570292], 'cdnode4': [120.30579006619145, 105.56723017608186], 'cdnode5': [102.94092788747736, 108.040441996923]}


        edges = [['0', '2'], ['0', '6'], ['0', '15'], ['0', '9'], ['1', '4'], ['1', '17'], ['1', '10'], ['2', '16'], ['2', '13'], ['3', '5'], ['3', '11'], ['4', '11'], ['6', '19'], ['7', '18'], ['8', '9'], ['10', '15'], ['10', '14'], ['12', '16'], ['14', '19'], ['15', '17'], ['cdnode1', '18'], [
            '5', 'cdnode1'], ['cdnode1', '7'], ['2', 'cdnode2'], ['cdnode2', 'cdnode1'], ['5', 'cdnode2'], ['cdnode2', '8'], ['3', 'cdnode3'], ['cdnode3', '13'], ['cdnode3', '5'], ['cdnode4', '12'], ['4', 'cdnode4'], ['cdnode4', '13'], ['3', 'cdnode5'], ['cdnode5', 'cdnode4'], ['4', 'cdnode5'], ['cdnode5', 'cdnode3']]

        G = nx.Graph(edges)
        tsm = TSM(G, pos)
        tsm.display()
        plt.savefig(f"test/outputs/bend.svg")
        plt.close()

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
    unittest.main(verbosity=3, exit=False)
