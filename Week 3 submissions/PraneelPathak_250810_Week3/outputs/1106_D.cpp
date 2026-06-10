#include <iostream>
#include <vector>
#include <queue>
#include <functional> // For std::greater

int main() {
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(NULL);

    int n, m;
    std::cin >> n >> m;

    std::vector<std::vector<int>> adj(n + 1);
    for (int i = 0; i < m; ++i) {
        int u, v;
        std::cin >> u >> v;
        adj[u].push_back(v);
        adj[v].push_back(u);
    }

    std::vector<bool> visited(n + 1, false);
    // Min-priority queue to store candidate nodes, ordered by node value
    std::priority_queue<int, std::vector<int>, std::greater<int>> pq;

    // Start at node 1
    pq.push(1);

    bool first_output = true;
    while (!pq.empty()) {
        int u = pq.top();
        pq.pop();

        if (visited[u]) {
            continue;
        }

        visited[u] = true;

        if (!first_output) {
            std::cout << " ";
        }
        std::cout << u;
        first_output = false;

        for (int v : adj[u]) {
            if (!visited[v]) {
                pq.push(v);
            }
        }
    }
    std::cout << std::endl;

    return 0;
}