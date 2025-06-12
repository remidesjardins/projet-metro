from utils.parser import load_data
from typing import List, Tuple

class UnionFind:
    def __init__(self, elements):
        self.parent = {e: e for e in elements}
        self.rank = {e: 0 for e in elements}

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        xroot = self.find(x)
        yroot = self.find(y)
        if xroot == yroot:
            return False
        if self.rank[xroot] < self.rank[yroot]:
            self.parent[xroot] = yroot
        else:
            self.parent[yroot] = xroot
            if self.rank[xroot] == self.rank[yroot]:
                self.rank[xroot] += 1
        return True

def kruskal_mst():
    graph, positions, stations = load_data()
    edges: List[Tuple[int, str, str]] = []  # (poids, station1, station2)
    seen = set()
    for s1 in graph:
        for s2, weight in graph[s1].items():
            if (s2, s1) not in seen:
                edges.append((weight, s1, s2))
                seen.add((s1, s2))
    # Tri des arêtes par poids croissant
    edges.sort()
    uf = UnionFind(graph.keys())
    mst = []
    total_weight = 0
    for weight, s1, s2 in edges:
        if uf.union(s1, s2):
            mst.append((s1, s2, weight))
            total_weight += weight
            if len(mst) == len(graph) - 1:
                break
    print("\n=== Arbre couvrant de poids minimal (Kruskal) ===")
    for s1, s2, w in mst:
        print(f"{stations[s1]['name']} <-> {stations[s2]['name']} : {w}")
    print(f"\nPoids total de l'arbre couvrant : {total_weight}")
    print(f"Nombre d'arêtes dans l'ACPM : {len(mst)}")
    print(f"Nombre de sommets : {len(graph)}")

if __name__ == "__main__":
    kruskal_mst()
