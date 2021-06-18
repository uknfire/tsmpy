class HalfEdge:
    def __init__(self, name):
        self.id = name
        self.inc = None  # the incident face at its right hand
        self.twin = None
        self.ori = None
        self.prev = None
        self.succ = None

    def get_points(self):
        return self.ori.id, self.twin.ori.id

    def set(self, twin, ori, prev, succ, inc):
        self.twin = twin
        self.ori = ori
        self.prev = prev
        self.succ = succ
        self.inc = inc

    def traverse(self):
        yield self
        he = self.succ
        while he is not self:
            yield he
            he = he.succ

    def __repr__(self) -> str:
        return f'{self.ori}->{self.twin.ori}'

    def __hash__(self):
        return hash(self.id)
