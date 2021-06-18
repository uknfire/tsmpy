"""TSM means topology-shape-metrics, one approach for generating orthogonal layout.
"""
from .planarization import Planarization
from .orthogonalization import Orthogonalization
from .compaction import Compaction
from .utils import number_of_cross
import networkx as nx
from matplotlib import pyplot as plt

__all__ = [
    "TSM",
    "ortho_layout",
    "is_bendnode",
    "precheck"
]

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


def is_bendnode(node):
    return type(node) is tuple and len(node) > 1 and node[0] == "bend"


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


# TODO: implement it rightly in the future
# def postcheck(G, pos):
#     """Check if there is cross or overlay in layout"""
#     for u, v in G.edges:
#         assert pos[u][0] == pos[v][0] or pos[u][1] == pos[v][1]


class TSM:
    def __init__(self, G, init_pos=None, uselp=False):
        self.G, self.pos = ortho_layout(G, init_pos, uselp)

    def display(self):
        """Draw layout with networkx draw lib"""
        plt.axis('off')
        # draw edge first, otherwise edge may not be shown in result
        nx.draw_networkx_edges(self.G, self.pos)
        nx.draw_networkx_nodes(self.G, self.pos, nodelist=[node for node in self.G.nodes if not is_bendnode(
            node)], node_color='white', node_size=15, edgecolors="black")
