"""DCEL means Doubly connected edge list(also known as half-edge data structure).
It is a data structure to represent an embedding of a planar graph in the plane
"""
from .face import Face
from .halfedge import HalfEdge
from .vertex import Vertex


class Dcel:
    """
    Build double connected edge list for a connected planar graph.
    Require the number of nodes greater than 1.
    Naming vertice with node name.
    Naming half_edge with (u, v).
    Nmming face with ('face', %d).
    """

    def __init__(self, G, embedding):
        self.vertices = {}
        self.half_edges = {}
        self.faces = {}
        self.ext_face = None

        self.vertices = {node: Vertex(node) for node in G.nodes}

        def add_half_edge(u, v):
            he = HalfEdge(u, v)
            self.half_edges[u, v] = he
            if (v, u) in self.half_edges:
                he.twin = self.half_edges[v, u]
                he.twin.twin = he
            he.ori = self.vertices[u]
            he.ori.inc = he

        for u, v in G.edges:
            add_half_edge(u, v)
            add_half_edge(v, u)

        for (u, v), he in self.half_edges.items():
            he.succ = self.half_edges[embedding.next_face_half_edge(u, v)]
            he.succ.prev = he

        for (u, v), he in self.half_edges.items():
            if not he.inc:
                face = Face(("face", len(self.faces)))
                self.faces[face.id] = face
                face.inc = he
                for e in he.traverse():
                    e.inc = face

    def add_node_between(self, u, node_name, v):
        def insert_node(u, v, mi):
            he = self.half_edges.pop((u, v))
            he1 = HalfEdge(u, mi.id)
            he2 = HalfEdge(mi.id, v)
            mi.inc = he2
            # update half_edges
            self.half_edges[u, mi.id] = he1
            self.half_edges[mi.id, v] = he2
            he1.set(None, he.ori, he.prev, he2, he.inc)
            he2.set(None, mi, he1, he.succ, he.inc)
            he1.prev.succ = he1
            he2.succ.prev = he2
            # update face
            if he.inc.inc is he:
                he.inc.inc = he1
            # update vertex
            if he.ori.inc is he:
                he.ori.inc = he1

        # update vertices
        mi = Vertex(node_name)
        self.vertices[node_name] = mi
        # insert
        insert_node(u, v, mi)
        insert_node(v, u, mi)
        for v1, v2 in ((u, mi.id), (mi.id, v)):
            self.half_edges[v1, v2].twin = self.half_edges[v2, v1]
            self.half_edges[v2, v1].twin = self.half_edges[v1, v2]

    def connect(self, face: Face, u, v, half_edge_side, side_uv):  # u, v in same face
        def insert_half_edge(u, v, f, prev_he, succ_he):
            he = HalfEdge(u, v)
            self.half_edges[u, v] = he
            f.inc = he
            he.set(None, self.vertices[u], prev_he, succ_he, f)
            prev_he.succ = he
            succ_he.prev = he
            self.faces[f.id] = f
            for h in he.traverse():
                h.inc = f

        # It's true only if G is connected.
        face_l = Face(('face', *face.id[1:], 'l'))
        face_r = Face(('face', *face.id[1:], 'r'))

        if face.is_external:
            face_r.is_external = True
            self.ext_face = face_r

        hes_u = [he for he in self.vertices[u].surround_half_edges()
                 if he.inc == face]
        hes_v = [he for he in self.vertices[v].surround_half_edges()
                 if he.inc == face]

        # It's very important to select the  right half_edge, depending on its side
        def select(outgoing_side, hes):
            if len(hes) == 1:
                return hes[0]

            side_dict = {half_edge_side[he]: he for he in hes}
            for side in [(outgoing_side + i) % 4 for i in [3, 2, 1]]:
                if side in side_dict:
                    return side_dict[side]

        he_u = select(side_uv, hes_u)
        he_v = select((side_uv + 2) % 4, hes_v)

        prev_uv = he_u.prev
        succ_uv = he_v
        prev_vu = he_v.prev
        succ_vu = he_u

        insert_half_edge(u, v, face_r, prev_uv, succ_uv)
        insert_half_edge(v, u, face_l, prev_vu, succ_vu)
        self.half_edges[u, v].twin = self.half_edges[v, u]
        self.half_edges[v, u].twin = self.half_edges[u, v]
        self.faces.pop(face.id)

    def connect_diff(self, face: Face, u, v):
        assert type(u) != Vertex
        assert type(v) != Vertex

        def insert_half_edge(u, v, f, prev_he, succ_he):
            he = HalfEdge(u, v)
            self.half_edges[u, v] = he
            he.set(None, self.vertices[u], prev_he, succ_he, f)
            prev_he.succ = he
            succ_he.prev = he
        he_u = self.vertices[u].get_half_edge(face)
        he_v = self.vertices[v].get_half_edge(face)
        prev_uv = he_u.prev
        succ_uv = he_v
        prev_vu = he_v.prev
        succ_vu = he_u

        insert_half_edge(u, v, face, prev_uv, succ_uv)
        insert_half_edge(v, u, face, prev_vu, succ_vu)
        self.half_edges[u, v].twin = self.half_edges[v, u]
        self.half_edges[v, u].twin = self.half_edges[u, v]
