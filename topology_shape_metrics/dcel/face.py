class Face:
    def __init__(self, name):
        self.id = name
        self.inc = None  # the first half-edge incident to the face from left
        self.is_external = False

    def __len__(self):
        return len(list(self.surround_vertices()))

    def __repr__(self) -> str:
        return str(self.id)

    def surround_faces(self):  # clockwise, duplicated!!
        for he in self.surround_half_edges():
            yield he.twin.inc

    def surround_half_edges(self):  # clockwise
        yield from self.inc.traverse()

    def surround_vertices(self):
        for he in self.surround_half_edges():
            yield he.ori

    def __hash__(self):
        return hash(self.id)
