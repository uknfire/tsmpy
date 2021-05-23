from copy import deepcopy
from collections import defaultdict
from topology_shape_metrics.flownet import Flow_net
from topology_shape_metrics.planarization import Planarization
from topology_shape_metrics.orthogonalization import Orthogonalization
import networkx as nx


class Compaction:
    '''
    Assign minimum lengths to the segments of the edges of the orthogonal representation.
    Never reverse ortho in this class.
    '''

    def __init__(self, ortho):
        self.planar = ortho.planar.copy()
        self.flow_dict = deepcopy(ortho.flow_dict)
        # preprocess
        self.bend_point_processor()
        self.refine_faces()
        halfedge_side = self.face_side_processor()
        halfedge_length = self.tidy_rectangle_compaction(halfedge_side)
        self.pos = self.layout(halfedge_side, halfedge_length)

    def bend_point_processor(self):
        '''Create dummy nodes for bends.
        '''
        bends = {}  # left to right
        for he in self.planar.dcel.half_edges.values():
            lf, rf = he.twin.inc, he.inc
            flow = self.flow_dict[lf.id][rf.id][he.id]
            if flow > 0:
                bends[he] = flow

        idx = 0
        # (u, v) -> (u, bend0, bend1, ..., v)
        for he, num_bends in bends.items():
            # Q: what if there are bends on both (u, v) and (v, u)?
            # A: Impossible, not a min cost
            u, v = he.get_points()
            lf_id, rf_id = he.twin.inc.id, he.inc.id

            self.planar.G.remove_edge(u, v)
            # use ('bend', idx) to represent bend node
            self.flow_dict[u][rf_id][u,
                                        ('bend', idx)] = self.flow_dict[u][rf_id].pop((u, v))

            for i in range(num_bends):
                cur_node = ('bend', idx)
                pre_node = ('bend', idx-1) if i > 0 else u
                nxt_node = ('bend', idx+1) if i < num_bends - 1 else v
                self.planar.G.add_edge(pre_node, cur_node)
                self.planar.dcel.add_node_between(
                    pre_node, cur_node, v
                )
                self.flow_dict.setdefault(cur_node, {}).setdefault(
                    lf_id, {})[cur_node, pre_node] = 1
                self.flow_dict.setdefault(cur_node, {}).setdefault(
                    rf_id, {})[cur_node, nxt_node] = 3
                idx += 1

            self.flow_dict[v][lf_id][v,
                                     ('bend', idx-1)] = self.flow_dict[v][lf_id].pop((v, u))
            self.planar.G.add_edge(('bend', idx-1), v)

    def refine_faces(self):
        '''Make face rectangle
        '''
        halfedge_side = self.face_side_processor()
        def search_prev(he, side):
            while halfedge_side[he] != side:
                he = he.prev
            return he
        def search_succ(he, side):
            while halfedge_side[he] != side:
                he = he.succ
            return he

        inv_front = defaultdict(dict)
        for face in self.planar.dcel.faces.values():
            if not face.is_external:
                for he in face.surround_half_edges():
                    if (halfedge_side[he] + 1) % 4 != halfedge_side[he.succ]:
                        # only extend he with side 0 or 2
                        extend_he = he if halfedge_side[he] in (0, 2) else he.succ
                        if he is extend_he:
                            cross_he = search_succ(extend_he, (halfedge_side[extend_he] + 1) % 4)
                            inv_front[cross_he][he] = (he.succ.ori.id, 1)
                        else:
                            cross_he = search_prev(extend_he, (halfedge_side[extend_he] + 3) % 4)
                            inv_front[cross_he][he] = (he.ori.id, -1)

        # sort dummy nodes in cross_he to avoid cross
        insert_nodes = {}
        for cross_he in inv_front:
            sorted_hes = []
            for he in cross_he.traverse():
                if he in inv_front[cross_he]:
                    sorted_hes.append(inv_front[cross_he][he])
                    break
            insert_nodes[cross_he] = sorted_hes[::-1]

        # remove dulplicate half edge

        for cross_he in list(insert_nodes.keys()):
            if cross_he in insert_nodes and cross_he.twin in insert_nodes:
                insert_nodes[cross_he] += insert_nodes.pop(cross_he.twin)

        for cross_he, extend_nodes_id in insert_nodes.items():
            l, v = cross_he.get_points()

            self.planar.G.remove_edge(l, v)
            for i, (extend_node_id, direction) in enumerate(extend_nodes_id):
                # process G
                dummy_node_id = ("dummy", (cross_he.id, i))
                self.planar.G.add_edge(l, dummy_node_id)
                self.planar.G.add_edge(dummy_node_id, extend_node_id)

                # # process dcel
                face = self.planar.dcel.half_edges[l, v].inc
                self.planar.dcel.add_node_between(l, dummy_node_id, v)
                assert (extend_node_id, dummy_node_id) not in self.planar.dcel.half_edges
                self.planar.dcel.connect(face, extend_node_id, dummy_node_id)


                # preprocess flow_dict
                he_e2d = self.planar.dcel.half_edges[extend_node_id, dummy_node_id]
                lf, rf = he_e2d.twin.inc, he_e2d.inc

                # init
                self.flow_dict[lf.id] = {}
                self.flow_dict[rf.id] = {}
                self.flow_dict[dummy_node_id] = {}

                for f1, f2 in ((lf, rf), (rf, lf)):
                    # f2f
                    for f in f1.surround_faces():
                        if f is not f2:
                            self.flow_dict[f1.id][f.id] = self.flow_dict[face.id][f.id]
                            self.flow_dict[f.id][f1.id] = self.flow_dict[f.id][face.id]
                        self.flow_dict[f1.id][f2.id] = {
                            he_e2d.id: 0} if f1 is lf else {he_e2d.twin.id: 0}

                    # v2f
                    for v in f1.surround_vertices():
                        if v.id == extend_node_id:
                            self.flow_dict[v.id][f1.id] = {he_e2d.id: 1 if direction == 1 else 2} if f1 is lf else \
                            {he_e2d.id: 2 if direction == 1 else 1}
                        elif v.id == dummy_node_id:
                            self.flow_dict[v.id][f1.id] = {he_e2d.twin.id: 1}
                        else:
                            self.flow_dict[v.id][f1.id] = self.flow_dict[v.id][face.id]
            # debug code
            # print("v of lf")
            # for v in lf.surround_vertices():
            #     print(v.id)
            # print("v of rf")
            # for v in rf.surround_vertices():
            #     print(v.id)
            # print('v of face')
            # for v in face.surround_vertices():
            #     print(v.id)
            # clear face.id in flow_dict


                l = dummy_node_id
            self.planar.G.add_edge(l, v)


    def face_side_processor(self):
        '''Associating edges with face sides.
        '''

        def update_face_edge(halfedge_side, face, base):
            for he in face.surround_half_edges():
                halfedge_side[he] = (halfedge_side[he] + base) % 4

        halfedge_side = {}
        # clockwise 0 -> 1 -> 2 -> 3
        for face in self.planar.dcel.faces.values():
            # set edges' side in internal faces independently at first
            side = 0
            for he in face.surround_half_edges():
                halfedge_side[he] = side
                end_angle = self.flow_dict[he.succ.ori.id][face.id][he.succ.id]
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


