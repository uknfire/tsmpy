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
    """Return the number of edge crossings in ``G`` given ``pos``.

    Each crossing is counted once. The routine relies on a robust
    segment intersection test and avoids double counting by iterating
    over unique edge pairs.

    The previous implementation relied on an ad-hoc vector product
    check which produced false positives for some layouts (see issue
    #6 of the upstream project).  The routine below follows the
    standard segment intersection algorithm using orientation tests and
    also handles collinear overlap cases correctly.
    """

    def do_intersect(p1, q1, p2, q2):
        def orientation(p, q, r):
            val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
            if val == 0:
                return 0
            return 1 if val > 0 else 2

        def on_segment(p, q, r):
            return (
                min(p[0], r[0]) <= q[0] <= max(p[0], r[0])
                and min(p[1], r[1]) <= q[1] <= max(p[1], r[1])
            )

        o1 = orientation(p1, q1, p2)
        o2 = orientation(p1, q1, q2)
        o3 = orientation(p2, q2, p1)
        o4 = orientation(p2, q2, q1)

        if o1 != o2 and o3 != o4:
            return True
        if o1 == 0 and on_segment(p1, p2, q1):
            return True
        if o2 == 0 and on_segment(p1, q2, q1):
            return True
        if o3 == 0 and on_segment(p2, p1, q2):
            return True
        if o4 == 0 and on_segment(p2, q1, q2):
            return True
        return False

    count = 0
    edges = list(G.edges)
    for i, (a, b) in enumerate(edges):
        for c, d in edges[i + 1:]:
            if len({a, b, c, d}) == 4:
                if do_intersect(pos[a], pos[b], pos[c], pos[d]):
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
