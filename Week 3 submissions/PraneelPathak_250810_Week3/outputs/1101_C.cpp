#include <iostream>
#include <vector>
#include <algorithm>

struct Segment {
    int l, r, original_index;
};

bool compareSegments(const Segment& a, const Segment& b) {
    if (a.l != b.l) {
        return a.l < b.l;
    }
    return a.r < b.r;
}

void solve() {
    int n;
    std::cin >> n;
    std::vector<Segment> segments(n);
    for (int i = 0; i < n; ++i) {
        std::cin >> segments[i].l >> segments[i].r;
        segments[i].original_index = i;
    }

    std::sort(segments.begin(), segments.end(), compareSegments);

    std::vector<int> ans(n);
    int max_r_seen = segments[0].r;
    bool found = false;

    for (int i = 0; i < n - 1; ++i) {
        max_r_seen = std::max(max_r_seen, segments[i].r);
        if (segments[i+1].l > max_r_seen) {
            for (int j = 0; j <= i; ++j) {
                ans[segments[j].original_index] = 1;
            }
            for (int j = i + 1; j < n; ++j) {
                ans[segments[j].original_index] = 2;
            }
            found = true;
            break;
        }
    }

    if (found) {
        for (int i = 0; i < n; ++i) {
            std::cout << ans[i] << (i == n - 1 ? "" : " ");
        }
        std::cout << "\n";
    } else {
        std::cout << "-1\n";
    }
}

int main() {
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(NULL);
    int t;
    std::cin >> t;
    while (t--) {
        solve();
    }
    return 0;
}