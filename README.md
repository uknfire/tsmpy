# Introduction

An implementation of orthogonal drawing algorithm in Python

Main idea comes from [A Generic Framework for the Topology-Shape-Metrics Based Layout](https://rtsys.informatik.uni-kiel.de/~biblio/downloads/theses/pkl-mt.pdf)

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