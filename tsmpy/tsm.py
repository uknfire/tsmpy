"""TSM means topology-shape-metrics, one approach for generating orthogonal layout.
"""
from .planarization import Planarization
from .orthogonalization import Orthogonalization
from .compaction import Compaction
from .utils import number_of_cross, overlap_nodes, overlay_edges
import networkx as nx
from matplotlib import pyplot as plt
import matplotlib.patches as mpatches


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
        draw_nodes_kwds = {'G': self.G, 'pos': self.pos,
                           'node_size': 15, "edgecolors": 'black'}

        nx.draw(node_color='white', **draw_nodes_kwds)

        # draw bend nodes if exist
        bend_nodelist = [
            node for node in self.G.nodes if TSM.is_bendnode(node)]
        if bend_nodelist:
            nx.draw_networkx_nodes(
                nodelist=bend_nodelist, node_color='grey', **draw_nodes_kwds)

        # draw overlap nodes if exist
        overlap_nodelist = overlap_nodes(self.G, self.pos)
        if overlap_nodelist:
            nx.draw_networkx_nodes(
                nodelist=overlap_nodelist, node_color="red", **draw_nodes_kwds)

        # draw overlay edges if exist
        overlay_edgelist = overlay_edges(self.G, self.pos)
        if overlay_edgelist:
            nx.draw_networkx_edges(
                self.G, self.pos, edgelist=overlay_edgelist, edge_color='red')

        # draw patches if exist
        patches = []
        if overlap_nodelist or overlay_edgelist:
            patches.append(mpatches.Patch(color='red', label='overlay'))
        if bend_nodelist:
            patches.append(mpatches.Patch(color='grey', label='bend node'))
        if patches:
            plt.legend(handles=patches)

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
