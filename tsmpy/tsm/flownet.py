"""
"""
import networkx as nx
from collections import defaultdict


class FlowNet(nx.MultiDiGraph):
    def add_v2f(self, v, f, key):
        self.add_edge(v, f, key=key, lowerbound=1, capacity=4, weight=0)

    def add_f2f(self, f1, f2, key):
        # if not self.has_edge(f1, f2):
        self.add_edge(f1, f2, key=key, lowerbound=0, capacity=2**32, weight=1)

    def add_v(self, v):
        self.add_node(v, demand=-4)  # the total degree around a node is 2pi

    def add_f(self, f, degree, is_external):
        # the degree of a face is the length of the cycle bounding the face.
        self.add_node(f, demand=(2 * degree + 4)
                      if is_external else (2 * degree - 4))

    def min_cost_flow(self):
        def get_demand(flow_dict, node):
            in_flow = sum(flow_dict[u][v][key]
                          for u, v, key in self.in_edges(node, keys=True))
            out_flow = sum(flow_dict[u][v][key]
                           for u, v, key in self.out_edges(node, keys=True))
            return in_flow - out_flow

        def split(G):
            base_dict = defaultdict(lambda: defaultdict(dict))
            new_G = nx.MultiDiGraph()

            for u, v, key in G.edges:
                lowerbound = G[u][v][key]['lowerbound']
                base_dict[u][v][key] = lowerbound
                new_G.add_edge(u, v, key,
                               capacity=G[u][v][key]['capacity'] -
                               lowerbound,
                               weight=G[u][v][key]['weight'],
                               )
            for node in G:
                new_G.nodes[node]['demand'] =  \
                    G.nodes[node]['demand'] - \
                    get_demand(base_dict, node)
            return base_dict, new_G

        base_dict, new_G = split(self)
        flow_dict = nx.min_cost_flow(new_G)
        for u, v, key in self.edges:
            flow_dict[u][v][key] += base_dict[u][v][key]

        self.cost = self.cost_of_flow(flow_dict)
        return flow_dict

    def cost_of_flow(self, flow_dict):
        return sum(flow_dict[u][v][key] * self[u][v][key]['weight'] for u, v, key in self.edges)
