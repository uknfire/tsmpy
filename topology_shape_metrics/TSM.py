"""TSM means topology-shape-metrics, one approach for generating orthogonal layout.
"""
from topology_shape_metrics.planarization import Planarization
from topology_shape_metrics.orthogonalization import Orthogonalization
from topology_shape_metrics.compaction import Compaction
from topology_shape_metrics.utils import number_of_cross, overlap_nodes, overlay_edges
import networkx as nx
from matplotlib import pyplot as plt
import matplotlib.patches as mpatches


class TSM:
    def __init__(self, G, init_pos=None, checkit=True, uselp=False):
        if checkit:
            TSM.precheck(G, init_pos)

        planar = Planarization(G, init_pos)
        ortho = Orthogonalization(planar, uselp)
        compa = Compaction(ortho)

        # self.G != G, it may include additional bend nodes
        self.G = compa.planar.G
        self.pos = compa.pos

    def postcheck(self):
        for u, v in self.G.edges:
            assert self.pos[u][0] == self.pos[v][0] or self.pos[u][1] == self.pos[v][1]


    def display(self):
        bend_nodes = {node for node in self.G.nodes if type(node) == tuple and node[0] == 'bend'}

        draw_nodes_kwds = {'G': self.G, 'pos': self.pos, 'node_size': 15, "edgecolors": 'black'}

        nx.draw_networkx_nodes(node_color='white', **draw_nodes_kwds)
        # bend nodes(dummy nodes, not exist in original graph)
        nx.draw_networkx_nodes(nodelist=bend_nodes, node_color='grey', **draw_nodes_kwds)
        # overlap nodes
        nx.draw_networkx_nodes(nodelist=overlap_nodes(
            self.G, self.pos), node_color="red", **draw_nodes_kwds)


        # all edges
        nx.draw_networkx_edges(self.G, self.pos)
        # overlay edges
        nx.draw_networkx_edges(
            self.G, self.pos, edgelist=overlay_edges(self.G, self.pos), edge_color='red')

        red_patch = mpatches.Patch(color='red', label='overlay')
        grey_patch = mpatches.Patch(color='grey', label='bend node')
        plt.legend(handles=[red_patch, grey_patch])


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
