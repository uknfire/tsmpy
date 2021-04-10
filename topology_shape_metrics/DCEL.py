"""DCEL means Doubly connected edge list(also known as half-edge data structure).
It is a data structure to represent an embedding of a planar graph in the plane
"""

import networkx as nx

class GraphElement():
    def __init__(self, name):
        self.id = name

    def __hash__(self):
        return hash(self.id)


class HalfEdge(GraphElement):
    def __init__(self, name):
        super().__init__(name)
        self.inc = None # the incident face'
        self.twin = None
        self.ori  = None
        self.pred = None
        self.succ = None

    def get_points(self):
        return self.ori.id, self.twin.ori.id

    def set_all(self, twin, ori, pred, succ, inc):
        self.twin = twin
        self.ori = ori
        self.pred = pred
        self.succ = succ
        self.inc = inc


class Vertex(GraphElement):
    def __init__(self, name):
        super().__init__(name)
        self.inc = None # 'the first outgoing incident half-edge'
        self.x = None
        self.y = None

    def surround_faces(self): # clockwise, duplicated
        for he in self.surround_half_edges():
            yield he.inc


    def surround_half_edges(self): # clockwise
        yield self.inc
        he = self.inc.pred.twin
        while he is not self.inc:
            yield he
            he = he.pred.twin


class Face(GraphElement):
    def __init__(self, name):
        super().__init__(name)
        self.inc = None # the first half-edge incident to the face from left
        self.nodes_id = []

    def __len__(self):
        return len(self.nodes_id)

    def __repr__(self):
        return f'FaceView{repr(self.nodes_id)}'

    def update_nodes(self):
        self.nodes_id = [vertex.id for vertex in self.surround_vertices()]

    def surround_faces(self): # clockwise, duplicated!!
        for he in self.surround_half_edges():
            yield he.twin.inc

    def surround_half_edges(self): # clockwise
        yield self.inc
        he = self.inc.succ
        while he is not self.inc:
            yield he
            he = he.succ

    def surround_vertices(self):
        for he in self.surround_half_edges():
            yield he.ori


class Dcel:
    def __init__(self, G, embedding):
        # assert nx.check_planarity(G)[0]

        self.vertices = {}
        for node in G.nodes:
            self.vertices[node] = Vertex(node)

        self.half_edges = {}
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
            he.succ.pred = he

        self.faces = {}
        for he in self.half_edges.values():
            if not he.inc:
                face_id = ("face", len(self.faces))
                face = Face(face_id)
                face.inc = he
                self.faces[face_id] = face

                face.nodes_id = embedding.traverse_face(*he.get_points())
                for v1_id, v2_id in zip(face.nodes_id, face.nodes_id[1:]+face.nodes_id[:1]):
                    other = self.half_edges[v1_id, v2_id]
                    assert not other.inc
                    other.inc = face

        if not self.faces:
            self.faces[('face', 0)] = Face(('face', 0))

    def add_node_between(self, u: 'id', v: 'id', node_name):
        def insert_node(u, v, mi):
            he = self.half_edges.pop((u, v))
            he1 = HalfEdge((u, mi.id))
            he2 = HalfEdge((mi.id, v))
            # update half_edges
            self.half_edges[u, mi.id] = he1
            self.half_edges[mi.id, v] = he2
            he1.set_all(None, he.ori, he.pred, he2, he.inc)
            he2.set_all(None, mi, he1, he.succ, he.inc)
            he1.pred.succ = he1
            he2.succ.pred = he2
            # update face
            if he.inc.inc is he:
                he.inc.inc = he1
            he.inc.update_nodes() # not efficient

        # update vertices
        mi = Vertex(node_name)
        self.vertices[node_name] = mi
        # insert
        insert_node(u, v, mi)
        insert_node(v, u, mi)
        for v1, v2 in ((u, mi.id), (mi.id, v)):
            self.half_edges[v1, v2].twin = self.half_edges[v2, v1]
            self.half_edges[v2, v1].twin = self.half_edges[v1, v2]
