"""TSM means topology-shape-metrics, one approach for generating orthogonal layout.
"""
from topology_shape_metrics.planarization import Planarization
from topology_shape_metrics.orthogonalization import Orthogonalization
from topology_shape_metrics.compaction import Compaction
from topology_shape_metrics.utils import number_of_cross
import networkx as nx


class TSM:
    def __init__(self, G, pos=None, checkit=True, uselp=False):
        if checkit:
            TSM.precheck(G, pos)

        self.planar = Planarization(G, pos)
        self.ortho = Orthogonalization(self.planar, uselp)
        self.compa = Compaction(self.ortho)

        # self.compa.G != G, it may include additional bend nodes
        self.G = self.compa.planar.G
        self.pos = self.compa.pos

    def postcheck(self):
        for u, v in self.planar.G.edges:
            assert self.pos[u][0] == self.pos[v][0] or self.pos[u][1] == self.pos[v][1]

    def draw(self, **kwds):
        nx.draw(self.planar.G, self.pos, **kwds)

    @staticmethod
    def precheck(G, pos=None):
        if max(degree for node, degree in G.degree) > 4:
            raise Exception(
                "Max node degree larger than 4, which is not supported currently")
        if nx.number_of_selfloops(G) > 0:
            raise Exception("G contains selfloop")
        if not nx.is_connected(G):
            raise Exception("G is not a connected graph")

        if pos is None:
            is_planar, _ = nx.check_planarity(G)
            if not is_planar:
                raise Exception("G is not a planar graph")
        else:
            if number_of_cross(G, pos) > 0:
                raise Exception("There are cross edges in pos")
