#include <iostream>
#include <vector>
#include <numeric>
#include <algorithm>

std::vector<int> parent;
std::vector<int> sz;

int find_set(int v) {
    if (v == parent[v])
        return v;
    return parent[v] = find_set(parent[v]);
}

void union_sets(int a, int b) {
    a = find_set(a);
    b = find_set(b);
    if (a != b) {
        if (sz[a] < sz[b])
            std::swap(a, b);
        parent[b] = a;
        sz[a] += sz[b];
    }
}

int main() {
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(NULL);

    int n, m;
    std::cin >> n >> m;

    parent.resize(n + 1);
    std::iota(parent.begin(), parent.end(), 0); // parent[i] = i
    
    sz.assign(n + 1, 1); // sz[i] = 1

    for (int i = 0; i < m; ++i) {
        int k;
        std::cin >> k;
        if (k == 0) {
            continue;
        }
        int first_user;
        std::cin >> first_user;
        for (int j = 1; j < k; ++j) {
            int current_user;
            std::cin >> current_user;
            union_sets(first_user, current_user);
        }
    }

    for (int i = 1; i <= n; ++i) {
        std::cout << sz[find_set(i)] << (i == n ? "" : " ");
    }
    std::cout << std::endl;

    return 0;
}