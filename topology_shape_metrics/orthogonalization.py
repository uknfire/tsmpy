import networkx as nx
from collections import defaultdict
from topology_shape_metrics.flownet import Flow_net

class Orthogonalization:
    '''
    works on a planar embedding, changes shape of the graph.
    '''

    def __init__(self, planar):
        assert max(pair[1] for pair in planar.G.degree) <= 4
        assert planar.G.number_of_nodes() > 1

        self.planar = planar

        self.flow_network = self.face_determination()
        self.flow_dict = self.tamassia_orthogonalization()

    def face_determination(self):
        flow_network = Flow_net()

        for vertex in self.planar.dcel.vertex_dict.values():
            flow_network.add_v(vertex.id)

        for face in self.planar.dcel.face_dict.values():
            flow_network.add_f(face.id, len(
                face), face is self.planar.ext_face)

        for vertex in self.planar.dcel.vertex_dict.values():
            for he in vertex.surround_half_edges():
                flow_network.add_v2f(vertex.id, he.inc.id, he.id)

        for he in self.planar.dcel.half_edge_dict.values():
            flow_network.add_f2f(he.twin.inc.id, he.inc.id, he.id)  # lf -> rf

        return flow_network

    def tamassia_orthogonalization(self):
        return self.flow_network.min_cost_flow()

    def lp_solve(self, weight_of_corner=1, weight_of_sym=0, sym_pairs=None,
                 # trans=lambda s: s if s[0] != '(' else eval(s.replace('_', ' ')),
                 ):
        '''
        Another way to solve min cost flow problem, make it possible to define constrains.

        Alert: pulp will automatically transfer node's name into str and repalce some special
        chars into '_', and will throw a error if there are variables' name duplicated.
        '''
        import pulp

        prob = pulp.LpProblem()  # minimize

        var_dict = defaultdict(lambda: defaultdict(dict))

        for u, v, he_id in self.flow_network.edges:
            var_dict[u][v][he_id] = pulp.LpVariable(
                f'{u}%{v}%{he_id}',
                self.flow_network[u][v][he_id]['lowerbound'],
                self.flow_network[u][v][he_id]['capacity'],
                pulp.LpInteger
            )

        objs = []
        for he in self.planar.dcel.half_edge_dict.values():
            lf, rf = he.twin.inc.id, he.inc.id
            objs.append(
                self.flow_network[lf][rf][he.id]['weight'] *
                var_dict[lf][rf][he.id]
            )

        # bend points' cost
        if weight_of_corner != 0:
            for v in self.planar.G:
                if self.planar.G.degree(v) == 2:
                    (f1, he1_id), (f2, he2_id) = [(f, key)
                                                  for f, keys in self.flow_network.adj[v].items()
                                                  for key in keys]
                    x = var_dict[v][f1][he1_id]
                    y = var_dict[v][f2][he2_id]
                    p = pulp.LpVariable(
                        x.name + "%temp", None, None, pulp.LpInteger)
                    prob.addConstraint(x - y <= p)
                    prob.addConstraint(y - x <= p)
                    objs.append(weight_of_corner * p)

        # non symmetrics cost
        if weight_of_sym != 0:
            if sym_pairs:
                for u, v in sym_pairs:
                    if u != v:
                        faces1 = {
                            face.id for face in self.planar.dcel.vertex_dict[u].surround_faces()}
                        faces2 = {
                            face.id for face in self.planar.dcel.vertex_dict[v].surround_faces()}
                        for f in faces1 & faces2:
                            nodes_id = self.planar.dcel.face_dict[f].nodes_id
                            n = len(nodes_id)
                            u_succ = nodes_id[(nodes_id.index(u) + 1) % n]
                            v_succ = nodes_id[(nodes_id.index(v) + 1) % n]
                            he_u = self.planar.dcel.half_edge_dict[u, u_succ]
                            he_v = self.planar.dcel.half_edge_dict[v, v_succ]

                            x, y = var_dict[u][f][he_u.id], var_dict[v][f][he_v.id]
                            p = pulp.LpVariable(
                                x.name + y.name + "%temp", None, None, pulp.LpInteger)
                            prob.addConstraint(x - y <= p)
                            prob.addConstraint(y - x <= p)
                            objs.append(weight_of_sym * p)

            for v in self.planar.G:
                if self.planar.G.degree(v) == 3:
                    for f, keys in self.flow_network.adj[v].items():
                        if len(keys) == 2:
                            he1_id, he2_id = list(keys)
                            x = var_dict[v][f][he1_id]
                            y = var_dict[v][f][he2_id]
                            p = pulp.LpVariable(
                                x.name + y.name + "%temp", None, None, pulp.LpInteger)
                            prob.addConstraint(x - y <= p)
                            prob.addConstraint(y - x <= p)
                            objs.append(weight_of_sym * p)
        prob += pulp.lpSum(objs), "number of bends in graph"

        for f in self.planar.dcel.face_dict:
            prob += self.flow_network.nodes[f]['demand'] == pulp.lpSum(
                [var_dict[v][f][he_id] for v, _, he_id in self.flow_network.in_edges(f, keys=True)])
        for v in self.planar.G:
            prob += -self.flow_network.nodes[v]['demand'] == pulp.lpSum(
                [var_dict[v][f][he_id] for _, f, he_id in
                 self.flow_network.out_edges(v, keys=True)]
            )

        state = prob.solve()
        if state == 1:  # update flow_dict
            # code here works only when nodes are represented by str, likes '(1, 2)'
            for var in prob.variables():
                if 'temp' not in var.name:
                    l = var.name.split('%')
                    if len(l) == 3:
                        # u, v, he_id = map(trans, l) # change str to tuple !!!!!!!!!
                        u, v, he_id = [item.replace('_', ' ') for item in l]
                        he_id = eval(he_id)
                        self.flow_dict[u][v][he_id] = int(var.varValue)
            return pulp.value(prob.objective)
        else:
            return 2**32

    def number_of_corners(self):
        count_right_angle = 0
        for node in self.planar.G:
            if self.planar.G.degree(node) == 2:
                for f, he_id in [(f, key) for f, keys in self.flow_network.adj[node].items()
                                 for key in keys]:
                    if self.flow_dict[node][f][he_id] == 1:
                        count_right_angle += 1
        return count_right_angle + self.flow_network.cost
