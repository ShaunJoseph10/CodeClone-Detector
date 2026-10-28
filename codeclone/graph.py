"""Similarity graph and plagiarism clusters (CO5: graphs + BFS)."""

from .structures import Queue


def build_graph(num_files, pairs):
    """Adjacency list: vertex = file index, edge = a pair given in `pairs` as (i, j).
    Callers pass only the pairs whose similarity is >= threshold."""
    adj = [[] for _ in range(num_files)]  # CO5: graph stored as adjacency lists
    for i, j in pairs:
        adj[i].append(j)
        adj[j].append(i)
    return adj


def connected_components(adj):
    """CO5: BFS from every unvisited vertex; each BFS tree is one component.
    CO1: uses our own linked-list Queue. O(V + E)."""
    visited = [False] * len(adj)
    components = []
    for start in range(len(adj)):
        if visited[start]:
            continue
        visited[start] = True
        queue = Queue()
        queue.enqueue(start)
        component = []
        while not queue.is_empty():
            v = queue.dequeue()
            component.append(v)
            for w in adj[v]:
                if not visited[w]:
                    visited[w] = True
                    queue.enqueue(w)
        components.append(component)
    return components


def clusters(adj):
    """Components with 2+ files: groups of submissions that share code."""
    return [c for c in connected_components(adj) if len(c) >= 2]
