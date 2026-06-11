#include <iostream>
#include <vector>
#include <algorithm>

struct Friend {
    int id;
    int a;
    int b;
};

bool check(int k, int n, const std::vector<Friend>& friends) {
    if (k == 0) {
        return true;
    }
    int invited_count = 0;
    for (int i = 0; i < n; ++i) {
        // If we invite friend 'i', they would be the (invited_count + 1)-th poorest person
        // among the k invited people.
        // This means there are 'invited_count' people poorer than them.
        // And there would be (k - 1 - invited_count) people richer than them.
        
        // Condition 1: Friend 'i' must tolerate 'invited_count' poorer people.
        // This is always true if we are considering friend 'i' to be invited,
        // as 'invited_count' is the number of people already invited who are poorer than 'i'.
        // So, invited_count <= friends[i].b must hold.
        
        // Condition 2: Friend 'i' must tolerate (k - 1 - invited_count) richer people.
        // So, (k - 1 - invited_count) <= friends[i].a must hold.

        if (invited_count <= friends[i].b && (k - 1 - invited_count) <= friends[i].a) {
            invited_count++;
            if (invited_count == k) {
                return true; // Found k people
            }
        }
    }
    return false; // Could not find k people
}

void solve() {
    int n;
    std::cin >> n;
    std::vector<Friend> friends(n);
    for (int i = 0; i < n; ++i) {
        friends[i].id = i;
        std::cin >> friends[i].a >> friends[i].b;
    }

    int low = 0;
    int high = n;
    int ans = 0;

    while (low <= high) {
        int mid = low + (high - low) / 2;
        if (check(mid, n, friends)) {
            ans = mid;
            low = mid + 1;
        } else {
            high = mid - 1;
        }
    }
    std::cout << ans << std::endl;
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