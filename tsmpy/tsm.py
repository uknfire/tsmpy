"""TSM means topology-shape-metrics, one approach for generating orthogonal layout.
"""
from .planarization import Planarization
from .orthogonalization import Orthogonalization
from .compaction import Compaction
from .utils import number_of_cross, overlap_nodes, overlay_edges
import networkx as nx
from matplotlib import pyplot as plt


class TSM:
    def __init__(self, G, init_pos=None, uselp=False):
        self.G, self.pos = TSM.ortho_layout(G, init_pos, uselp)

    def postcheck(self):
        for u, v in self.G.edges:
            assert self.pos[u][0] == self.pos[v][0] or self.pos[u][1] == self.pos[v][1]

    @staticmethod
    def ortho_layout(G, init_pos=None, uselp=True):
        """
        Returns
        -------
        G : Networkx graph
            which may contain bend nodes

        pos : dict
            A dictionary of positions keyed by node
        """

        planar = Planarization(G, init_pos)
        ortho = Orthogonalization(planar, uselp)
        compa = Compaction(ortho)
        return compa.G, compa.pos

    @staticmethod
    def is_bendnode(node):
        return type(node) is tuple and len(node) > 1 and node[0] == "bend"

    def savefig(self, pathname):
        self.display()
        plt.savefig(pathname)
        plt.close()

    def display(self):
        """Draw layout with networkx draw lib"""
        plt.axis('off')
        # draw edge first, otherwise edge may not be shown in result
        nx.draw_networkx_edges(self.G, self.pos)
        nx.draw_networkx_nodes(self.G, self.pos, nodelist=[node for node in self.G.nodes if not TSM.is_bendnode(
            node)], node_color='white', node_size=15)

    @staticmethod
    def precheck(G, pos=None):
        """Check if input is valid. If not, raise an exception"""
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
                raise Exception("There are cross edges in given layout")

        for node in G.nodes:
            if type(node) is tuple and len(node) > 1 and node[0] in ("dummy", "bend"):
                raise Exception(f"Invalid node name: {node}")
