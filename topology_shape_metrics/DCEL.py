"""DCEL means Doubly connected edge list(also known as half-edge data structure).
It is a data structure to represent an embedding of a planar graph in the plane
"""
from pprint import pprint

class HalfEdge:
    def __init__(self, name):
        self.id = name
        self.inc = None # the incident face'
        self.twin = None
        self.ori  = None
        self.prev = None
        self.succ = None

    def print(self):
        pprint(vars(self))

    def get_points(self):
        return self.ori.id, self.twin.ori.id

    def set(self, twin, ori, prev, succ, inc):
        self.twin = twin
        self.ori = ori
        self.prev = prev
        self.succ = succ
        self.inc = inc

    def traverse(self):
        he = self.succ
        yield self
        while he is not self:
            yield he
            he = he.succ

    def __repr__(self) -> str:
        return f'{self.id}'


    def __hash__(self):
        return hash(self.id)

class Vertex:
    def __init__(self, name):
        self.id = name
        self.inc = None # 'the first outgoing incident half-edge'

    def surround_faces(self): # clockwise, duplicated
        for he in self.surround_half_edges():
            yield he.inc

    def surround_half_edges(self): # clockwise
        yield self.inc
        he = self.inc.prev.twin
        while he is not self.inc:
            yield he
            he = he.prev.twin

    def get_half_edge(self, face):
        for he in self.surround_half_edges():
            if he.inc is face:
                return he
        return None

    def __repr__(self) -> str:
        return f'{self.id}'

    def __hash__(self):
        return hash(self.id)

    def print(self):
        pprint(vars(self))

class Face:
    def __init__(self, name):
        self.id = name
        self.inc = None # the first half-edge incident to the face from left
        self.is_external = False

    def __len__(self):
        return len(list(self.surround_vertices()))

    def __repr__(self) -> str:
        return str(self.id)

    def surround_faces(self): # clockwise, duplicated!!
        for he in self.surround_half_edges():
            yield he.twin.inc

    def surround_half_edges(self): # clockwise
        yield from self.inc.traverse()

    def surround_vertices(self):
        for he in self.surround_half_edges():
            yield he.ori

    def __hash__(self):
        return hash(self.id)

    def print(self):
        pprint(vars(self))

class Dcel:
    def __init__(self, G, embedding):
        # assert nx.check_planarity(G)[0]

        self.vertices = {}
        self.half_edges = {}
        self.faces = {}
        self.ext_face = None

        for node in G.nodes:
            self.vertices[node] = Vertex(node)

        for u, v in G.edges:
            he1, he2 = HalfEdge((u, v)), HalfEdge((v, u))
            self.half_edges[he1.id] = he1
            self.half_edges[he2.id] = he2
            he1.twin = he2
            he1.ori = self.vertices[u]
            self.vertices[u].inc = he1

            he2.twin = he1
            he2.ori = self.vertices[v]
            self.vertices[v].inc = he2

        for he in self.half_edges.values():
            u, v = he.get_points()
            he.succ = self.half_edges[embedding.next_face_half_edge(u, v)]
            he.succ.prev = he

        for he in self.half_edges.values():
            if not he.inc:
                face_id = ("face", len(self.faces))
                face = Face(face_id)
                face.inc = he
                self.faces[face_id] = face

                nodes_id = embedding.traverse_face(*he.get_points())
                for v1_id, v2_id in zip(nodes_id, nodes_id[1:]+nodes_id[:1]):
                    other = self.half_edges[v1_id, v2_id]
                    assert not other.inc
                    other.inc = face

        if not self.faces:
            self.faces[('face', 0)] = Face(('face', 0))

    def add_node_between(self, u, node_name, v):
        def insert_node(u, v, mi):
            he = self.half_edges.pop((u, v))
            he1 = HalfEdge((u, mi.id))
            he2 = HalfEdge((mi.id, v))
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

    def connect(self, face, u, v): # u, v in same face
        assert u in [v.id for v in face.surround_vertices()], (face, self.vertices[u].inc.inc)
        assert v in [v.id for v in face.surround_vertices()], (v, face)

        def insert_halfedge(u, v, f, prev_he, succ_he):
            he = HalfEdge((u, v))
            self.half_edges[u, v] = he
            f.inc = he
            he.set(None, self.vertices[u], prev_he, succ_he, f)
            prev_he.succ = he
            succ_he.prev = he
            self.faces[f.id] = f
            for h in he.traverse():
                h.inc = f

        def find_all(face, start_id, end_id):
            for he in face.surround_half_edges():
                if he.ori.id == start_id:
                    res = []
                    for e in he.traverse():
                        if e.ori.id == end_id:
                            res.append(e)
                    return res
            raise Exception("Not found")


        face_l = Face(('face', *face.id[1:], 'l'))
        face_r = Face(('face', *face.id[1:], 'r'))
        if face.is_external:
            face_r.is_external = True
            self.ext_face = face_r
        # Be careful here
        hes_u2v = find_all(face, u, v)
        hes_v2u = find_all(face, v, u)
        prev_he_u = hes_v2u[-1].prev
        succ_he_v = hes_u2v[0]
        prev_he_v = hes_u2v[0].prev
        succ_he_u = hes_v2u[-1]

        insert_halfedge(u, v, face_r, prev_he_u, succ_he_v)
        insert_halfedge(v, u, face_l, prev_he_v, succ_he_u)
        self.half_edges[u, v].twin = self.half_edges[v, u]
        self.half_edges[v, u].twin = self.half_edges[u, v]
        self.faces.pop(face.id)

    def print(self):
        for map, name in zip((self.vertices, self.half_edges, self.faces), ('v', 'he', 'face')):
            print(name)
            for obj in map.values():
                obj.print()


