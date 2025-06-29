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

def kruskal_mst(edges, n):
    uf = UnionFind(range(n))
    mst = []
    total_weight = 0
    for weight, s1, s2 in edges:
        if uf.union(s1, s2):
            mst.append((s1, s2, weight))
            total_weight += weight
            if len(mst) == n - 1:
                break
    return mst, total_weight

if __name__ == '__main__':
    # Test du calcul de l'ACPM
    graph, positions, stations = load_data()
    
    # Calculer l'ACPM
    edges = []
    seen = set()
    for s1 in graph:
        for s2, weight_data in graph[s1].items():
            if (s2, s1) not in seen:
                # Extraire le poids selon le nouveau format
                if isinstance(weight_data, list) and len(weight_data) > 0:
                    weight = weight_data[0]['time'] if isinstance(weight_data[0], dict) else weight_data[0]
                elif isinstance(weight_data, dict):
                    weight = weight_data.get('time', weight_data)
                else:
                    weight = weight_data
                
                edges.append((weight, s1, s2))
                seen.add((s1, s2))
    
    edges.sort()
    mst, total_weight = kruskal_mst(edges, len(graph))
    
    # Affichage des résultats (supprimé pour la production)
    # print(f"Poids total de l'arbre couvrant : {total_weight}")
    # print(f"Nombre d'arêtes dans l'ACPM : {len(mst)}")
