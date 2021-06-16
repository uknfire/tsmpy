class Vertex:
    def __init__(self, name):
        self.id = name
        self.inc = None  # 'the first outgoing incident half-edge'

    def surround_faces(self):  # clockwise, duplicated
        for he in self.surround_half_edges():
            yield he.inc

    def surround_half_edges(self):  # clockwise
        yield self.inc
        he = self.inc.prev.twin
        while he is not self.inc:
            yield he
            he = he.prev.twin

    def get_half_edge(self, face):
        for he in self.surround_half_edges():
            if he.inc is face:
                return he
        raise Exception("not find")

    def __repr__(self):
        return f'{self.id}'

    def __hash__(self):
        return hash(self.id)
