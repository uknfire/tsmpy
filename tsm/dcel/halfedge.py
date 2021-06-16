class HalfEdge:
    def __init__(self, name):
        self.id = name
        self.inc = None  # the incident face'
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
        he = self.succ
        yield self
        while he is not self:
            yield he
            he = he.succ

    def __repr__(self) -> str:
        return f'{self.id}'

    def __hash__(self):
        return hash(self.id)
