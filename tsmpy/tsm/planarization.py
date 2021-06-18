from .utils import convert_pos_to_embedding
from tsmpy.dcel import Dcel
import networkx as nx


class Planarization:
    """Determine the topology of the drawing which is described by a planar embedding.
    """

    def __init__(self, G, pos=None):
        if pos is None:
            is_planar, embedding = nx.check_planarity(G)
            pos = nx.combinatorial_embedding_to_pos(embedding)
        else:
            embedding = convert_pos_to_embedding(G, pos)

        self.G = G.copy()
        self.dcel = Dcel(G, embedding)
        self.dcel.ext_face = self.get_external_face(pos)
        self.dcel.ext_face.is_external = True

    def get_external_face(self, pos):
        corner_node = min(pos, key=lambda k: (pos[k][0], pos[k][1]))

        sine_vals = {}
        for node in self.G.adj[corner_node]:
            dx = pos[node][0] - pos[corner_node][0]
            dy = pos[node][1] - pos[corner_node][1]
            sine_vals[node] = dy / (dx**2 + dy**2)**0.5

        other_node = min(sine_vals, key=lambda node: sine_vals[node])
        return self.dcel.half_edges[corner_node, other_node].inc
