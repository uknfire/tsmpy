from copy import deepcopy
from collections import defaultdict
from topology_shape_metrics.flownet import Flow_net
from topology_shape_metrics.DCEL import Dcel
import networkx as nx

class Compaction:
    '''
    Assign minimum lengths to the segments of the edges of the orthogonal representation.
    '''

    def __init__(self, ortho):
        self.planar = ortho.planar.copy() # Try to not modify original G
        self.G = self.planar.G
        self.dcel = self.planar.dcel

        flow_dict = deepcopy(ortho.flow_dict)
        self.bend_point_processor(flow_dict)
        halfedge_side = self.face_side_processor(flow_dict)
        self.refine_faces(halfedge_side)

        halfedge_length = self.tidy_rectangle_compaction(halfedge_side)
        self.pos = self.layout(halfedge_side, halfedge_length)
        self.remove_dummy()

    def bend_point_processor(self, flow_dict):
        '''Create bend nodes.
        Modify self.G, self.dcel and flow_dict
        '''
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
                pre_node = ('bend', idx-1) if i > 0 else u
                nxt_node = ('bend', idx+1) if i < num_bends - 1 else v
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
                                     ('bend', idx-1)] = flow_dict[v][lf_id].pop((v, u))
            self.G.add_edge(('bend', idx-1), v)

    def refine_faces(self, halfedge_side):
        '''Make face rectangle, create dummpy nodes
        Modify self.G, self.dcel, halfedge_side
        '''

        def find_front(he, target=1):
            init_he = he
            cnt = 0
            while cnt != target:
                side, next_side = halfedge_side[he], halfedge_side[he.succ]
                if side == next_side: # go straight
                    pass
                elif (side + 1) % 4 == next_side: # go right
                    cnt += 1
                elif (side + 2) % 4 == next_side: # go back
                    cnt -= 2
                else: # go left
                    cnt -= 1
                he = he.succ
                if he is init_he:
                    raise Exception("can't find front edge")
            return he

        def refine(face, target): # insert only one edge to make face more rect, internal
            # print(prefix + 'refining', face)
            # assert not face.is_external
            # print(prefix, {he: halfedge_side[he] for he in face.surround_half_edges()})
            for he in face.surround_half_edges():  # traverse face
                side, next_side = halfedge_side[he], halfedge_side[he.succ]
                if side != next_side and (side + 1) % 4 != next_side:
                    front_he = find_front(he, target)
                    extend_node_id = he.twin.ori.id
                    # print(prefix, extend_node_id, 'to', front_he)

                    l, v = front_he.ori.id, front_he.twin.ori.id
                    he_l2r = self.dcel.half_edges[l, v]
                    # process G

                    # f'd{extend_node_id}'
                    dummy_node_id = ("dummy", extend_node_id)
                    self.G.remove_edge(l, v)
                    self.G.add_edge(l, dummy_node_id)
                    self.G.add_edge(dummy_node_id, v)
                    self.G.add_edge(dummy_node_id, extend_node_id)

                    # # process dcel
                    face = self.dcel.half_edges[l, v].inc
                    self.dcel.add_node_between(l, dummy_node_id, v)
                    self.dcel.connect(face, extend_node_id, dummy_node_id)

                    he_e2d = self.dcel.half_edges[extend_node_id, dummy_node_id]
                    he_l2d = self.dcel.half_edges[l, dummy_node_id]
                    he_d2r = self.dcel.half_edges[dummy_node_id, v]
                    lf, rf = he_e2d.twin.inc, he_e2d.inc

                    # process halfedge_side
                    halfedge_side[he_l2d] = halfedge_side[he_l2r]
                    halfedge_side[he_l2d.twin] = (halfedge_side[he_l2r] + 2) % 4
                    halfedge_side[he_d2r] = halfedge_side[he_l2r]
                    halfedge_side[he_d2r.twin] = (halfedge_side[he_l2r] + 2) % 4

                    halfedge_side[he_e2d] = halfedge_side[he]
                    halfedge_side[he_e2d.twin] = (halfedge_side[he] + 2) % 4
                    halfedge_side.pop(he_l2r)
                    halfedge_side.pop(he_l2r.twin)

                    refine(lf, target)
                    refine(rf, target)
                    break

        def build_border(G, dcel):
            # create border dcel
            border_nodes = [("dummy", -i) for i in range(1, 5)]
            border_edges = [(border_nodes[i], border_nodes[(i + 1) % 4]) for i in range(4)]
            border_G = nx.Graph(border_edges)

            is_planar, border_embedding = nx.check_planarity(border_G)
            border_dcel = Dcel(border_G, border_embedding)

            for face in list(border_dcel.faces().values()):
                if not face.is_external:
                    for he in face.surround_halfedges():
                        he.inc = self.planar.ext_face
                    border_dcel.faces.pop(face.id)
                    border_dcel.faces[self.planar.ext_face.id] = self.planar.ext_face
                else:
                    # rename border_dcel.ext_face's name
                    border_dcel.faces.pop(face.id)
                    face.id = ("face", -1)
                    border_dcel.faces[face.id] = face


            G.add_edges(border_edges)

            # merge border dcel into self.dcel
            dcel.vertices.update(border_dcel.vertices)
            dcel.half_edges.update(border_dcel.half_edges)
            dcel.faces.update(border_dcel.faces)

        build_border(self.G, self.dcel)
        # TODO: refine external face
        for face in list(self.dcel.faces.values()):
            if not face.is_external:
                refine(face, 1)
            # else:
            #     refine(face, -1)

        # for face in list(self.dcel.faces.values()):
        #     if face.is_external:
        #         for he in face.surround_half_edges():
        #             halfedge_side[he] = (halfedge_side[he.twin] + 2) % 4
        #         break



    def face_side_processor(self, flow_dict):
        '''Assign edges with face sides, depending on flow_dict
        '''

        def update_face_edge(halfedge_side, face, base):
            for he in face.surround_half_edges():
                halfedge_side[he] = (halfedge_side[he] + base) % 4

        halfedge_side = {}
        # clockwise 0 -> 1 -> 2 -> 3
        for face in self.dcel.faces.values():
            # set edges' side in internal faces independently at first
            side = 0
            for he in face.surround_half_edges():
                halfedge_side[he] = side
                end_angle = flow_dict[he.succ.ori.id][face.id][he.succ.id]
                if end_angle == 1:
                    # turn right in internal face or turn left in external face
                    side = (side + 1) % 4
                elif end_angle == 3:
                    side = (side + 3) % 4
                elif end_angle == 4:  # a single edge
                    side = (side + 2) % 4

        # update other face's edge side based on ext_face's edge side
        faces_dfs = list(self.planar.dfs_face_order())

        # all faces in dfs order
        has_updated = {faces_dfs[0]}
        for face in faces_dfs[1:]:
            # at least one twin edge has been set
            for he in face.surround_half_edges():
                lf = he.twin.inc
                if lf in has_updated:  # neighbor face has been updated
                    # the edge that has been updated
                    l_side = halfedge_side[he.twin]
                    r_side = halfedge_side[he]  # side of u, v in face
                    update_face_edge(
                        halfedge_side, face, (l_side + 2) % 4 - r_side)
                    has_updated.add(face)
                    break
        return halfedge_side

    def tidy_rectangle_compaction(self, halfedge_side):
        '''
        Compute every edge's length, depending on halfedge_side
        '''
        def build_flow(target_side):
            flow = Flow_net()
            for he, side in halfedge_side.items():
                if side == target_side:
                    lf, rf = he.twin.inc, he.inc
                    lf_id = lf.id
                    rf_id = rf.id if not rf.is_external else ('face', 'end')
                    flow.add_edge(lf_id, rf_id, he.id)
            return flow

        def min_cost_flow(flow, source, sink): # sovle what?
            if not flow:
                return {}
            for node in flow:
                flow.nodes[node]['demand'] = 0
            flow.nodes[source]['demand'] = -2**32
            flow.nodes[sink]['demand'] = 2**32
            for lf_id, rf_id, he_id in flow.edges:
                # what if selfloop?
                flow.edges[lf_id, rf_id, he_id]['weight'] = 1
                flow.edges[lf_id, rf_id, he_id]['lowerbound'] = 1
                flow.edges[lf_id, rf_id, he_id]['capacity'] = 2**32
            flow.add_edge(source, sink, 'extend_edge',
                             weight=0, lowerbound=0, capacity=2**32)

            # selfloop，avoid inner edge longer than border
            # for u, _ in flow.selfloop_edges():
            #     in_nodes = [v for v, _ in flow.in_edges(u)]
            #     assert in_nodes
            #     delta = sum(flow[v][u]['lowerbound'] for v in in_nodes) - flow[u][u]['count']
            #     if delta < 0:
            #         flow.edges[in_nodes[0]][u]['lowerbound'] += -delta
            return flow.min_cost_flow()

        hor_flow = build_flow(1)  # up -> bottom
        ver_flow = build_flow(0)  # left -> right

        hor_flow_dict = min_cost_flow(hor_flow, self.planar.ext_face.id, ('face', 'end'))
        ver_flow_dict = min_cost_flow(ver_flow, self.planar.ext_face.id, ('face', 'end'))

        halfedge_length = {}

        for he, side in halfedge_side.items():
            if side in (0, 1):
                rf = he.inc
                rf_id = ('face', 'end') if rf.is_external else rf.id
                lf_id = he.twin.inc.id

                if side == 0:
                    hv_flow_dict = ver_flow_dict
                elif side == 1:
                    hv_flow_dict = hor_flow_dict

                length = hv_flow_dict[lf_id][rf_id][he.id]
                halfedge_length[he] = length
                halfedge_length[he.twin] = length

        return halfedge_length

    def layout(self, halfedge_side, halfedge_length):
        ''' return pos of self.G
        '''
        pos = {}
        for face in self.planar.dfs_face_order():
            for start_he in face.surround_half_edges():
                if not pos:
                    pos[start_he.ori.id] = (0, 0)  # initial point
                if start_he.ori.id in pos:  # has found a start point
                    for he in start_he.traverse():
                        u, v = he.get_points()
                        side = halfedge_side[he]
                        length = halfedge_length[he]
                        x, y = pos[u]
                        if side == 1:
                            pos[v] = (x + length, y)
                        elif side == 3:
                            pos[v] = (x - length, y)
                        elif side == 0:
                            pos[v] = (x, y + length)
                        else:  # side == 2
                            pos[v] = (x, y - length)
                    break
        return pos

    def remove_dummy(self):
        for node in list(self.G.nodes):
            if type(node) is tuple and node[0] == "dummy" and len(node) > 1:
                extend_node_id = node[1]
                assert len(self.G[node]) == 3
                u, v = [nb for nb in self.G[node] if nb != extend_node_id]
                self.G.remove_node(node)
                self.G.add_edge(u, v)
                self.pos.pop(node)



