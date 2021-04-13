# Introduction

An implementation of orthogonal drawing algorithm in Python

Main idea comes from [A Generic Framework for the Topology-Shape-Metrics Based Layout](https://rtsys.informatik.uni-kiel.de/~biblio/downloads/theses/pkl-mt.pdf)

# Usage
```Python
# in root dir
import networkx as nx
from topology_shape_metrics.TSM import TSM
from matplotlib import pyplot as plt

G = nx.Graph(nx.read_gml("test/inputs/case1.gml")) # a nx.Graph object
pos = {node: eval(node) for node in G} # initial layout, optional, will be converted to a embedding
# if pos is None, embedding is given by nx.check_planarity

tsm = TSM(G, pos)  # use nx.min_cost_flow to solve minimum cost flow program
# tsm = TSM(G, pos, uselp=True) # use linear programming to solve minimum cost flow program
tsm.display()
plt.savefig("test/outputs/case1.nolp.svg")
```

# An example of results
|not use lp | use lp|
|---|---|
|![not use lp](https://raw.githubusercontent.com/rawfh/orthogonal-drawing-algorithm/master/test/outputs/case1.nolp.svg)|![not use lp](https://raw.githubusercontent.com/rawfh/orthogonal-drawing-algorithm/master/test/outputs/case1.lp.svg)|

# Requirements for input graph
* Planar
* Connected
* Max node degree is no more than 4
* No selfloop

# Features
* Using linear programing to solve minimum-cost flow problem
* Support multigraph

# Existing problems
* Edge overlays and crossings in output
* Node overlaps in output


# TODO
* Cleaner code
* More comments
* Fix overlay