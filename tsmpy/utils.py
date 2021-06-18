from networkx import PlanarEmbedding
from math import atan2
import networkx as nx
import matplotlib.patches as mpatches
from matplotlib import pyplot as plt


def convert_pos_to_embedding(G, pos):
    """Make sure only straight line in layout"""
    emd = PlanarEmbedding()
    for node in G:
        neigh_pos = {
            neigh: (pos[neigh][0]-pos[node][0], pos[neigh][1]-pos[node][1]) for neigh in G[node]
        }
        neighes_sorted = sorted(G.adj[node],
                                key=lambda v: atan2(
                                    neigh_pos[v][1], neigh_pos[v][0])
                                )  # counter clockwise
        last = None
        for neigh in neighes_sorted:
            emd.add_half_edge_ccw(node, neigh, last)
            last = neigh
    emd.check_structure()
    return emd


def number_of_cross(G, pos):
    """
    not accurate, may be equal to actual number or double
    """
    def is_cross(pa, pb, pc, pd):
        def xmul(v1, v2):
            return v1[0] * v2[1] - v1[1] * v2[0]

        def f(pa, pb, p):
            return (pa[1] - pb[1]) * (p[0] - pb[0]) - (p[1] - pb[1]) * (pa[0] - pb[0])

        ca = (pa[0] - pc[0], pa[1] - pc[1])
        cb = (pb[0] - pc[0], pb[1] - pc[1])
        cd = (pd[0] - pc[0], pd[1] - pc[1])
        return xmul(ca, cd) >= 0 and xmul(cd, cb) >= 0 and f(pa, pb, pc) * f(pa, pb, pd) < 0

    count = 0
    for a, b in G.edges:
        for c, d in G.edges:
            if a not in (c, d) and b not in (c, d):
                if is_cross(pos[a], pos[b], pos[c], pos[d]):
                    count += 1

    return count


def overlap_nodes(G, pos):  # not efficient
    inv_pos = {}
    for k, v in pos.items():
        v = tuple(v)  # compatible with pos given by nx.spring_layout()
        inv_pos[v] = inv_pos.get(v, ()) + (k,)
    return [node for nodes in inv_pos.values() if len(nodes) > 1 for node in nodes]


def overlay_edges(G, pos):  # not efficient
    res = set()
    for a, b in G.edges:
        (xa, ya), (xb, yb) = pos[a], pos[b]
        for c, d in G.edges:
            (xc, yc), (xd, yd) = pos[c], pos[d]
            if (a, b) != (c, d):
                if xa == xb == xc == xd:
                    if min(ya, yb) >= max(yc, yd) or max(ya, yb) <= min(yc, yd):
                        continue
                    res.add((a, b))
                    res.add((c, d))
                if ya == yb == yc == yd:
                    if min(xa, xb) >= max(xc, xd) or max(xa, xb) <= min(xc, xd):
                        continue
                    res.add((a, b))
                    res.add((c, d))
    return list(res)


def draw_overlay(G, pos, is_bendnode):
    """Draw graph and highlight bendnodes, overlay nodes and edges"""
    plt.axis('off')
    # draw edge first, otherwise edge may not show in plt result
    # draw all edges
    nx.draw_networkx_edges(G, pos)
    # draw all nodes
    nx.draw_networkx_nodes(G, pos, nodelist=[node for node in G.nodes if not is_bendnode(
        node)], node_color='white', node_side=15)

    draw_nodes_kwds = {'G': G, 'pos': pos, 'node_size': 15}

    bend_nodelist = [node for node in G.nodes if is_bendnode(node)]
    # draw bend nodes if exist
    if bend_nodelist:
        nx.draw_networkx_nodes(
            nodelist=bend_nodelist, node_color='grey', **draw_nodes_kwds)

    # draw overlap nodes if exist
    overlap_nodelist = overlap_nodes(G, pos)
    if overlap_nodelist:
        nx.draw_networkx_nodes(
            nodelist=overlap_nodelist, node_color="red", **draw_nodes_kwds)

    # draw overlay edges if exist
    overlay_edgelist = overlay_edges(G, pos)
    if overlay_edgelist:
        nx.draw_networkx_edges(
            G, pos, edgelist=overlay_edgelist, edge_color='red')

    # draw patches if exist
    patches = []
    if overlap_nodelist or overlay_edgelist:
        patches.append(mpatches.Patch(color='red', label='overlay'))
    if bend_nodelist:
        patches.append(mpatches.Patch(color='grey', label='bend node'))
    if patches:
        plt.legend(handles=patches)
