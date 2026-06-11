#include <iostream>
#include <vector>
#include <algorithm>

bool is_palindrome_with_deletion(const std::vector<int>& arr, int n, int x_to_delete) {
    int l = 0;
    int r = n - 1;
    while (l < r) {
        if (arr[l] == arr[r]) {
            l++;
            r--;
        } else if (arr[l] == x_to_delete) {
            l++;
        } else if (arr[r] == x_to_delete) {
            r--;
        } else {
            return false;
        }
    }
    return true;
}

void solve() {
    int n;
    std::cin >> n;
    std::vector<int> a(n);
    for (int i = 0; i < n; ++i) {
        std::cin >> a[i];
    }

    int left = 0;
    int right = n - 1;
    while (left < right && a[left] == a[right]) {
        left++;
        right--;
    }

    if (left >= right) { // Already a palindrome
        std::cout << "YES\n";
        return;
    }

    // Mismatch found: a[left] != a[right]
    // Try deleting a[left] or a[right]
    if (is_palindrome_with_deletion(a, n, a[left])) {
        std::cout << "YES\n";
    } else if (is_palindrome_with_deletion(a, n, a[right])) {
        std::cout << "YES\n";
    } else {
        std::cout << "NO\n";
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