# tsmpy

`tsmpy` is a Python implementation of an orthogonal layout algorithm based on the Topology-Shape-Metrics (TSM) approach. The algorithm is inspired by [A Generic Framework for the Topology-Shape-Metrics Based Layout](https://rtsys.informatik.uni-kiel.de/~biblio/downloads/theses/pkl-mt.pdf).

## Installation

```bash
pip install -r requirements.txt
```

## Quick start

```python
import networkx as nx
from matplotlib import pyplot as plt
from tsmpy import TSM

# Load a planar graph from the test data
G = nx.Graph(nx.read_gml("test/inputs/case2.gml"))

# Optional: provide an initial embedding
pos = {node: eval(node) for node in G}

# Solve the minimum cost flow problem using linear programming
tsm = TSM(G, pos)
# tsm = TSM(G, pos, uselp=False)  # use networkx.min_cost_flow instead

# Display and save the layout
tsm.display()
plt.savefig("test/outputs/case2.lp.svg")
plt.close()
```

## Examples

|case1|case2|
|---|---|
|![case1](https://raw.githubusercontent.com/uknfire/tsmpy/master/test/outputs/case1.lp.svg)|![case2](https://raw.githubusercontent.com/uknfire/tsmpy/master/test/outputs/case2.lp.svg)|

|bend case|grid case|
|---|---|
|![bend](https://raw.githubusercontent.com/uknfire/tsmpy/master/test/outputs/bend.svg)|![grid](https://raw.githubusercontent.com/uknfire/tsmpy/master/test/outputs/grid_5x5.svg)|

## Running tests

```bash
# show help
python test.py -h

# run all tests
python test.py

# run all tests in TestGML
python test.py TestGML
```

## Playground

Try editing the original `case2` graph with [yed](https://www.yworks.com/yed-live/?file=https://gist.githubusercontent.com/uknfire/1a6782b35d066d6e59e00ed8dc0bb795/raw/eaee6eee89c48efa1c234f31fd8f9c32d237ce1e/case2).

### Requirements for input graph

* Planar
* Connected
* Maximum node degree is 4
* No self-loops

## Features

* Linear programming based minimum-cost flow formulation to reduce the number of bends

## TODO

- [ ] Cleaner code
- [ ] More comments
- [x] Fix overlay
- [ ] Support node degree > 4
- [x] Support cut-edges
