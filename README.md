# Introduction

An implementation of orthogonal drawing algorithm in Python

Main idea comes from [A Generic Framework for the Topology-Shape-Metrics Based Layout](https://rtsys.informatik.uni-kiel.de/~biblio/downloads/theses/pkl-mt.pdf)

# How to run code
## Install requirements
```bash
pip install -r requirements.txt
```
## Usage
```Python
# in root dir
import networkx as nx
from tsmpy import TSM
from matplotlib import pyplot as plt

G = nx.Graph(nx.read_gml("test/inputs/case2.gml")) # a nx.Graph object
pos = {node: eval(node) for node in G}
# initial layout, optional, will be converted to an embedding
# if pos is None, embedding is given by nx.check_planarity

tsm = TSM(G, pos)  # use nx.min_cost_flow to solve minimum cost flow program
# tsm = TSM(G, pos, uselp=True) # use linear programming to solve minimum cost flow program
tsm.display()
plt.savefig("test/outputs/case2.lp.svg")
```

## Run test
```bash
# show help
python test/test.py -h

# run all tests
python test/test.py

# run all tests in TestGML
python test/test.py TestGML
```

# Example of results
|case1|case2|
|---|---|
|![case1](https://raw.githubusercontent.com/uknfire/tsmpy/master/test/outputs/case1.lp.svg)|![case2](https://raw.githubusercontent.com/uknfire/tsmpy/master/test/outputs/case2.lp.svg)|

|case3|case4|
|---|---|
|![case3](https://raw.githubusercontent.com/uknfire/tsmpy/master/test/outputs/case3.lp.svg)|![case4](https://raw.githubusercontent.com/uknfire/tsmpy/master/test/outputs/case4.lp.svg)|

# Playground
Try editing original graph with [yed](https://www.yworks.com/yed-live/?file=https://gist.githubusercontent.com/uknfire/1a6782b35d066d6e59e00ed8dc0bb795/raw/eaee6eee89c48efa1c234f31fd8f9c32d237ce1e/case2)
# Requirements for input graph
* Planar
* Connected
* Max node degree is no more than 4
* No selfloop

# Features
* Using linear programing to solve minimum-cost flow problem, to reduce number of bends


# TODO
- [ ] Cleaner code
- [ ] More comments
- [x] Fix overlay
- [ ] Support node degree > 4
- [x] Support cut-edges