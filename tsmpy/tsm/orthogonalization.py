import pulp
from collections import defaultdict
from .flownet import FlowNet


class Orthogonalization:
    '''works on a planar embedding, changes shape of the graph.
    '''

    def __init__(self, planar, uselp=False):
        self.G = planar.G
        self.dcel = planar.dcel

        self.flow_network = self.face_determination()
        if not uselp:
            self.flow_dict = self.tamassia_orthogonalization()
        else:
            self.flow_dict = self.lp_solve()

    def face_determination(self):
        flow_network = FlowNet()

        for vertex in self.dcel.vertices.values():
            flow_network.add_v(vertex.id)

        for face in self.dcel.faces.values():
            flow_network.add_f(face.id, len(
                face), face.is_external)

        for vertex in self.dcel.vertices.values():
            for he in vertex.surround_half_edges():
                flow_network.add_v2f(vertex.id, he.inc.id, he.id)

        for he in self.dcel.half_edges.values():
            flow_network.add_f2f(he.twin.inc.id, he.inc.id, he.id)  # lf -> rf

        return flow_network

    def tamassia_orthogonalization(self):
        return self.flow_network.min_cost_flow()

    def lp_solve(self):
        '''
        Use linear programming to solve min cost flow problem, make it possible to define constrains.

        Alert: pulp will automatically transfer node's name into str and repalce some special
        chars into '_', and will throw a error if there are variables' name duplicated.
        '''

        prob = pulp.LpProblem()  # minimize

        var_dict = {}
        var_names = {}  # turn (u, v, he_id) into digit string
        for u, v, he_id in self.flow_network.edges:
            var_names[str(len(var_names))] = (u, v, he_id)
            var_dict[u, v, he_id] = pulp.LpVariable(
                str(len(var_names) - 1),
                self.flow_network[u][v][he_id]['lowerbound'],
                self.flow_network[u][v][he_id]['capacity'],
                pulp.LpInteger
            )

        objs = []
        for he in self.dcel.half_edges.values():
            lf, rf = he.twin.inc.id, he.inc.id
            objs.append(
                self.flow_network[lf][rf][he.id]['weight'] *
                var_dict[lf, rf, he.id]
            )

        # Add bend cost
        for v in self.G:
            if self.G.degree(v) == 2:
                (f1, he1_id), (f2, he2_id) = [(f, key)
                                              for f, keys in self.flow_network.adj[v].items()
                                              for key in keys]
                x = var_dict[v, f1, he1_id]
                y = var_dict[v, f2, he2_id]
                p = pulp.LpVariable(
                    x.name + "*", None, None, pulp.LpInteger)
                prob.addConstraint(x - y <= p)
                prob.addConstraint(y - x <= p)
                objs.append(p)

        prob += pulp.lpSum(objs)  # number of bends in graph

        for f in self.dcel.faces:
            prob += self.flow_network.nodes[f]['demand'] == pulp.lpSum(
                [var_dict[v, f, he_id] for v, _, he_id in self.flow_network.in_edges(f, keys=True)])
        for v in self.G:
            prob += -self.flow_network.nodes[v]['demand'] == pulp.lpSum(
                [var_dict[v, f, he_id] for _, f, he_id in
                 self.flow_network.out_edges(v, keys=True)]
            )

        state = prob.solve()
        res = defaultdict(lambda: defaultdict(dict))
        if state == 1:  # update flow_dict
            self.flow_network.cost = pulp.value(prob.objective)
            for var in prob.variables():
                if var.name.isdigit():
                    u, v, he_id = var_names[var.name]
                    res[u][v][he_id] = int(var.varValue)
            return res
        else:
            raise Exception("Problem can't be solved by linear programming")
