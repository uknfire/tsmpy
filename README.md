# Introduction

An implementation of orthogonal drawing algorithm in Python

Main idea comes from [A Generic Framework for the Topology-Shape-Metrics Based Layout](https://rtsys.informatik.uni-kiel.de/~biblio/downloads/theses/pkl-mt.pdf)

# Usage
```Python
# in root dir
import networkx as nx
from topology_shape_metrics.TSM import TSM
from matplotlib import pyplot as plt

G = nx.Graph(nx.read_gml("test/inputs/case2.gml")) # a nx.Graph object
pos = {node: eval(node) for node in G}
# initial layout, optional, will be converted to an embedding
# if pos is None, embedding is given by nx.check_planarity

tsm = TSM(G, pos)  # use nx.min_cost_flow to solve minimum cost flow program
# tsm = TSM(G, pos, uselp=True) # use linear programming to solve minimum cost flow program
tsm.display()
plt.savefig("test/outputs/case2.nolp.svg")
```

# Run tests
```bash
# show help
python test.py -h

# run test on case2 and case4, generating svg file in test/outputs
python test.py TestGML -k nocut

# run all 7 tests in TestGML.
# note that it fails in 4 tests.(because they have cut-edges)
python test.py TestGML
```

# An example of results(case2)
|not use lp | use lp|
|---|---|
|![not use lp](https://raw.githubusercontent.com/rawfh/orthogonal-drawing-algorithm/master/test/outputs/case2.nolp.svg)|![not use lp](https://raw.githubusercontent.com/rawfh/orthogonal-drawing-algorithm/master/test/outputs/case2.lp.svg)|

# Requirements for input graph
* Planar
* Connected
* Max node degree is no more than 4
* No selfloop

# Features
* Using linear programing to solve minimum-cost flow problem, to reduce number of bends

# Existing problems
* Edge overlays and crossings in output
* Node overlaps in output
* May throw exception if the graph has cut-edges


# TODO
* Cleaner code
* More comments
* Fix overlay
* Support node degree > 4
* Support cut-edges