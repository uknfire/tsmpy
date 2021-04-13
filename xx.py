import networkx as nx
from topology_shape_metrics.TSM import TSM
from matplotlib import pyplot as plt

G = nx.Graph(nx.read_gml("test/inputs/case1.gml"))

# initial layout, will be converted to embedding
# if pos is not given, will use embedding given by nx.check_planarity
pos = {node: eval(node) for node in G}

tsm = TSM(G, pos)  # use nx.min_cost_flow to solve minimum cost flow program
# tsm = TSM(G, pos, uselp=True) # use linear programming to solve minimum cost flow program
tsm.display()
plt.savefig("test/outputs/case1.nolp.svg")
