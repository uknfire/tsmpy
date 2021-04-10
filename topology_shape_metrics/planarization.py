from topology_shape_metrics.utils import convert_pos_to_embdeding, number_of_cross
from topology_shape_metrics.DCEL import Dcel
import networkx as nx

class Planarization:
    '''This step determines the topology of the drawing which is described by a planar embedding.
    '''
    def __init__(self, G, pos=None):
        if pos is None:
            is_planar, self.embedding = nx.check_planarity(G)
            pos = nx.combinatorial_embedding_to_pos(self.embedding)
        else:
            self.embedding = convert_pos_to_embdeding(G, pos)

        self.G = G
        self.pos = pos  # is only used to find the ext_face now.
        self.dcel = Dcel(G, self.embedding)
        self.ext_face = self.get_external_face()

    @staticmethod
    def precheck(G, pos=None):
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


    def copy(self):
        new_planar = self.__new__(self.__class__)
        new_planar.__init__(self.G, self.pos)
        return new_planar

    def get_external_face(self):
        def left_most(G, pos):
            corner_node = min(pos, key=lambda k: (pos[k][0], pos[k][1]))
            other = max(
                G.adj[corner_node], key=lambda node:
                (pos[node][1] - pos[corner_node][1]) /
                (
                    (pos[node][0] - pos[corner_node][0])**2 +
                    (pos[node][1] - pos[corner_node][1])**2
                )**0.5
            )  # maximum cosine value
            return sorted([corner_node, other], key=lambda node:
                          (pos[node][1], pos[node][0]))

        if len(self.pos) < 2:
            return list(self.dcel.face_dict.values())[0]
        down, up = left_most(self.G, self.pos)
        return self.dcel.half_edge_dict[up, down].inc

    def dfs_face_order(self):  # dfs dual graph, starts at ext_face
        def dfs_face(face, marked):
            marked.add(face.id)
            yield face
            for neighbor_face in set(face.surround_faces()):
                if neighbor_face.id not in marked:
                    yield from dfs_face(neighbor_face, marked)
        yield from dfs_face(self.ext_face, set())
