"""TSM means topology-shape-metrics, one approach for generating orthogonal layout.
"""
from topology_shape_metrics.planarization import Planarization
from topology_shape_metrics.orthogonalization import Orthogonalization
from topology_shape_metrics.compaction import Compaction
import networkx as nx

class TSM:
    def __init__(self, G, pos=None, precheck=True):
        if precheck:
            Planarization.precheck(G, pos)
        self.planar = Planarization(G, pos)
        self.ortho = Orthogonalization(self.planar)
        self.compa = Compaction(self.ortho)
        self.G = G
        self.pos = self.compa.pos

    def check(self):
        for u, v in self.planar.G.edges:
            assert self.pos[u][0] == self.pos[v][0] or self.pos[u][1] == self.pos[v][1]

    def draw(self, **kwds):
        nx.draw(self.planar.G, self.pos, **kwds)
