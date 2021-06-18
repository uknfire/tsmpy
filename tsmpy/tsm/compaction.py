from copy import deepcopy
from .flownet import Flow_net
from tsmpy.dcel import Dcel
import networkx as nx


class Compaction:
    """
    Assign minimum lengths to the segments of the edges of the orthogonal representation.
    """

    def __init__(self, ortho):
        self.planar = ortho.planar
        self.G = self.planar.G
        self.dcel = self.planar.dcel

        flow_dict = deepcopy(ortho.flow_dict)
        self.bend_point_processor(flow_dict)
        ori_edges = list(self.G.edges)
        halfedge_side = self.face_side_processor(flow_dict)
        self.refine_faces(halfedge_side)

        halfedge_length = self.tidy_rectangle_compaction(halfedge_side)
        self.pos = self.layout(halfedge_side, halfedge_length)
        self.remove_dummy()
        self.G.add_edges_from(ori_edges)

    def bend_point_processor(self, flow_dict):
        """Create bend nodes. Modify self.G, self.dcel and flow_dict"""
        bends = {}  # left to right
        for he in self.dcel.half_edges.values():
            lf, rf = he.twin.inc, he.inc
            flow = flow_dict[lf.id][rf.id][he.id]
            if flow > 0:
                bends[he] = flow

        idx = 0
        # (u, v) -> (u, bend0, bend1, ..., v)
        for he, num_bends in bends.items():
            # Q: what if there are bends on both (u, v) and (v, u)?
            # A: Impossible, not a min cost
            u, v = he.get_points()
            lf_id, rf_id = he.twin.inc.id, he.inc.id

            self.G.remove_edge(u, v)
            # use ('bend', idx) to represent bend node
            flow_dict[u][rf_id][u,
                                ('bend', idx)] = flow_dict[u][rf_id].pop((u, v))

            for i in range(num_bends):
                cur_node = ('bend', idx)
                pre_node = ('bend', idx - 1) if i > 0 else u
                nxt_node = ('bend', idx + 1) if i < num_bends - 1 else v
                self.G.add_edge(pre_node, cur_node)
                self.dcel.add_node_between(
                    pre_node, cur_node, v
                )
                flow_dict.setdefault(cur_node, {}).setdefault(
                    lf_id, {})[cur_node, pre_node] = 1
                flow_dict.setdefault(cur_node, {}).setdefault(
                    rf_id, {})[cur_node, nxt_node] = 3
                idx += 1

            flow_dict[v][lf_id][v,
                                ('bend', idx - 1)] = flow_dict[v][lf_id].pop((v, u))
            self.G.add_edge(('bend', idx - 1), v)

    def refine_faces(self, halfedge_side):
        """Make face rectangle, create dummpy nodes.
        Modify self.G, self.dcel, halfedge_side
        """

        def find_front(init_he, target):  # first
            cnt = 0
            for he in init_he.traverse():
                side, next_side = halfedge_side[he], halfedge_side[he.succ]
                if side == next_side:  # go straight
                    pass
                elif (side + 1) % 4 == next_side:  # go right
                    cnt += 1
                elif (side + 2) % 4 == next_side:  # go back
                    cnt -= 2
                else:  # go left
                    cnt -= 1
                if cnt == target:
                    return he.succ
            raise Exception(f"can't find front edge of {init_he}")

        def refine_internal(face):
            """Insert only one edge to make face more rect"""
            for he in face.surround_half_edges():
                side, next_side = halfedge_side[he], halfedge_side[he.succ]
                if side != next_side and (side + 1) % 4 != next_side:
                    front_he = find_front(he, 1)
                    extend_node_id = he.twin.ori.id

                    l, r = front_he.ori.id, front_he.twin.ori.id
                    he_l2r = self.dcel.half_edges[l, r]
                    dummy_node_id = ("dummy", extend_node_id)
                    self.G.remove_edge(l, r)
                    self.G.add_edge(l, dummy_node_id)
                    self.G.add_edge(dummy_node_id, r)

                    face = self.dcel.half_edges[l, r].inc
                    self.dcel.add_node_between(l, dummy_node_id, r)
                    he_l2d = self.dcel.half_edges[l, dummy_node_id]
                    he_d2r = self.dcel.half_edges[dummy_node_id, r]
                    halfedge_side[he_l2d] = halfedge_side[he_l2r]
                    halfedge_side[he_l2d.twin] = (
                        halfedge_side[he_l2r] + 2) % 4
                    halfedge_side[he_d2r] = halfedge_side[he_l2r]
                    halfedge_side[he_d2r.twin] = (
                        halfedge_side[he_l2r] + 2) % 4
                    halfedge_side.pop(he_l2r)
                    halfedge_side.pop(he_l2r.twin)

                    self.G.add_edge(dummy_node_id, extend_node_id)
                    self.dcel.connect(face, extend_node_id,
                                      dummy_node_id, halfedge_side, halfedge_side[he])

                    he_e2d = self.dcel.half_edges[extend_node_id,
                                                  dummy_node_id]
                    lf, rf = he_e2d.twin.inc, he_e2d.inc
                    halfedge_side[he_e2d] = halfedge_side[he]
                    halfedge_side[he_e2d.twin] = (halfedge_side[he] + 2) % 4

                    refine_internal(lf)
                    refine_internal(rf)
                    break

        def build_border(G, dcel, halfedge_side):
            """Create border dcel"""
            border_nodes = [("dummy", -i) for i in range(1, 5)]
            border_edges = [(border_nodes[i], border_nodes[(i + 1) % 4])
                            for i in range(4)]
            border_G = nx.Graph(border_edges)
            border_side_dict = {}
            is_planar, border_embedding = nx.check_planarity(border_G)
            border_dcel = Dcel(border_G, border_embedding)
            ext_face = border_dcel.half_edges[(
                border_nodes[0], border_nodes[1])].twin.inc
            border_dcel.ext_face = ext_face
            ext_face.is_external = True

            for face in list(border_dcel.faces.values()):
                if not face.is_external:
                    for i, he in enumerate(face.surround_half_edges()):
                        he.inc = self.dcel.ext_face
                        halfedge_side[he] = i  # assign side
                        halfedge_side[he.twin] = (i + 2) % 4
                        border_side_dict[i] = he
                    border_dcel.faces.pop(face.id)
                    border_dcel.faces[self.dcel.ext_face.id] = self.dcel.ext_face
                else:
                    # rename border_dcel.ext_face's name
                    border_dcel.faces.pop(face.id)
                    face.id = ("face", -1)
                    border_dcel.faces[face.id] = face
            G.add_edges_from(border_edges)

            # merge border dcel into self.dcel
            dcel.vertices.update(border_dcel.vertices)
            dcel.half_edges.update(border_dcel.half_edges)
            dcel.faces.update(border_dcel.faces)
            dcel.ext_face.is_external = False
            dcel.ext_face = border_dcel.ext_face
            return border_side_dict

        ori_ext_face = self.dcel.ext_face
        border_side_dict = build_border(self.G, self.dcel, halfedge_side)

        for he in ori_ext_face.surround_half_edges():
            extend_node_id = he.succ.ori.id
            side, next_side = halfedge_side[he], halfedge_side[he.succ]
            if next_side != side and next_side != (side + 1) % 4:
                if len(self.G[extend_node_id]) <= 2:
                    front_he = border_side_dict[(side + 1) % 4]
                    dummy_node_id = ("dummy", extend_node_id)
                    l, r = front_he.ori.id, front_he.twin.ori.id
                    he_l2r = self.dcel.half_edges[l, r]
                    # process G
                    self.G.remove_edge(l, r)
                    self.G.add_edge(l, dummy_node_id)
                    self.G.add_edge(dummy_node_id, r)
                    self.G.add_edge(dummy_node_id, extend_node_id)

                    # # process dcel

                    self.dcel.add_node_between(l, dummy_node_id, r)
                    self.dcel.connect_diff(
                        ori_ext_face, extend_node_id, dummy_node_id)

                    he_e2d = self.dcel.half_edges[extend_node_id,
                                                  dummy_node_id]
                    he_l2d = self.dcel.half_edges[l, dummy_node_id]
                    he_d2r = self.dcel.half_edges[dummy_node_id, r]
                    # process halfedge_side
                    halfedge_side[he_l2d] = halfedge_side[he_l2r]
                    halfedge_side[he_l2d.twin] = (
                        halfedge_side[he_l2r] + 2) % 4
                    halfedge_side[he_d2r] = halfedge_side[he_l2r]
                    halfedge_side[he_d2r.twin] = (
                        halfedge_side[he_l2r] + 2) % 4

                    halfedge_side[he_e2d] = halfedge_side[he]
                    halfedge_side[he_e2d.twin] = (halfedge_side[he] + 2) % 4
                    halfedge_side.pop(he_l2r)
                    halfedge_side.pop(he_l2r.twin)
                    break
        else:
            raise Exception("not connected")

        for face in list(self.dcel.faces.values()):
            if face.id != ("face", -1):
                refine_internal(face)

    def face_side_processor(self, flow_dict):
        """Give flow_dict, assign halfedges with face sides"""

        halfedge_side = {}

        def set_side(init_he, side):
            for he in init_he.traverse():
                halfedge_side[he] = side
                angle = flow_dict[he.succ.ori.id][he.inc.id][he.succ.id]
                if angle == 1:
                    # turn right in internal face or turn left in external face
                    side = (side + 1) % 4
                elif angle == 3:
                    side = (side + 3) % 4
                elif angle == 4:  # a single edge
                    side = (side + 2) % 4

            for he in init_he.traverse():
                if he.twin not in halfedge_side:
                    set_side(he.twin, (halfedge_side[he] + 2) % 4)

        set_side(self.dcel.ext_face.inc, 0)
        return halfedge_side

    def tidy_rectangle_compaction(self, halfedge_side):
        """
        Compute every edge's length, depending on halfedge_side
        """

        def build_flow(target_side):
            flow = Flow_net()
            for he, side in halfedge_side.items():
                if side == target_side:
                    lf, rf = he.twin.inc, he.inc
                    lf_id = lf.id
                    rf_id = rf.id if not rf.is_external else ('face', 'end')
                    flow.add_edge(lf_id, rf_id, he.id)
            return flow

        def min_cost_flow(flow, source, sink):
            if not flow:
                return {}
            for node in flow:
                flow.nodes[node]['demand'] = 0
            flow.nodes[source]['demand'] = -2 ** 32
            flow.nodes[sink]['demand'] = 2 ** 32
            for lf_id, rf_id, he_id in flow.edges:
                # TODO: what if selfloop?
                flow.edges[lf_id, rf_id, he_id]['weight'] = 1
                flow.edges[lf_id, rf_id, he_id]['lowerbound'] = 1
                flow.edges[lf_id, rf_id, he_id]['capacity'] = 2 ** 32
            flow.add_edge(source, sink, 'extend_edge',
                          weight=0, lowerbound=0, capacity=2 ** 32)

            return flow.min_cost_flow()

        hor_flow = build_flow(1)  # up -> bottom
        ver_flow = build_flow(0)  # left -> right

        hor_flow_dict = min_cost_flow(
            hor_flow, self.dcel.ext_face.id, ('face', 'end'))
        ver_flow_dict = min_cost_flow(
            ver_flow, self.dcel.ext_face.id, ('face', 'end'))

        halfedge_length = {}

        for he, side in halfedge_side.items():
            if side in (0, 1):
                rf = he.inc
                rf_id = ('face', 'end') if rf.is_external else rf.id
                lf_id = he.twin.inc.id

                if side == 0:
                    hv_flow_dict = ver_flow_dict
                else:
                    hv_flow_dict = hor_flow_dict

                length = hv_flow_dict[lf_id][rf_id][he.id]
                halfedge_length[he] = length
                halfedge_length[he.twin] = length

        return halfedge_length

    def layout(self, halfedge_side, halfedge_length):
        """ return pos of self.G"""
        pos = {}

        def set_coord(init_he, x, y):
            for he in init_he.traverse():
                pos[he.ori.id] = (x, y)
                side = halfedge_side[he]
                length = halfedge_length[he]
                if side == 1:
                    x += length
                elif side == 3:
                    x -= length
                elif side == 0:
                    y += length
                else:
                    y -= length

            for he in init_he.traverse():
                for e in he.ori.surround_half_edges():
                    if e.twin.ori.id not in pos:
                        set_coord(e, *pos[e.ori.id])

        set_coord(self.dcel.ext_face.inc, 0, 0)
        return pos

    def remove_dummy(self):
        for node in list(self.G.nodes):
            if type(node) is tuple and len(node) > 1:
                if node[0] == "dummy":
                    self.G.remove_node(node)
                    self.pos.pop(node, None)
