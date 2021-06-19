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

G = nx.Graph(nx.read_gml("test/inputs/case2.gml"))

# initial layout, it will be converted to an embedding
pos = {node: eval(node) for node in G}

# pos is an optional, if pos is None, embedding will be given by nx.check_planarity

# use linear programming to solve minimum cost flow program
tsm = TSM(G, pos)

# or use nx.min_cost_flow to solve minimum cost flow program
# it is faster but produces worse result
# tsm = TSM(G, pos, uselp=False)

tsm.display()
plt.savefig("test/outputs/case2.lp.svg")
plt.close()
```

## Run test
```bash
# show help
python test.py -h

# run all tests
python test.py

# run all tests in TestGML
python test.py TestGML
```

# Example
|case1|case2|
|---|---|
|![case1](https://raw.githubusercontent.com/uknfire/tsmpy/master/test/outputs/case1.lp.svg)|![case2](https://raw.githubusercontent.com/uknfire/tsmpy/master/test/outputs/case2.lp.svg)|

|bend case|grid case|
|---|---|
|![bend](https://raw.githubusercontent.com/uknfire/tsmpy/master/test/outputs/bend.svg)|![grid](https://raw.githubusercontent.com/uknfire/tsmpy/master/test/outputs/grid_5x5.svg)|

# Playground
Try editing original case2 graph with [yed](https://www.yworks.com/yed-live/?file=https://gist.githubusercontent.com/uknfire/1a6782b35d066d6e59e00ed8dc0bb795/raw/eaee6eee89c48efa1c234f31fd8f9c32d237ce1e/case2)
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