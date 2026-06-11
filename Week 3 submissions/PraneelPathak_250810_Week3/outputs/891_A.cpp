#include <iostream>
#include <vector>
#include <numeric> // For std::gcd
#include <algorithm> // For std::min

long long calculate_gcd(long long a, long long b) {
    while (b) {
        a %= b;
        std::swap(a, b);
    }
    return a;
}

int main() {
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(NULL);

    int n;
    std::cin >> n;

    std::vector<long long> a(n);
    int count_ones = 0;
    for (int i = 0; i < n; ++i) {
        std::cin >> a[i];
        if (a[i] == 1) {
            count_ones++;
        }
    }

    if (count_ones > 0) {
        std::cout << n - count_ones << std::endl;
        return 0;
    }

    int min_len_to_make_one = n + 1;

    for (int i = 0; i < n; ++i) {
        long long current_gcd = a[i];
        if (current_gcd == 1) { // Handle single element case
            min_len_to_make_one = 1;
            break;
        }
        for (int j = i + 1; j < n; ++j) {
            current_gcd = calculate_gcd(current_gcd, a[j]);
            if (current_gcd == 1) {
                min_len_to_make_one = std::min(min_len_to_make_one, j - i + 1);
                break; 
            }
        }
    }

    if (min_len_to_make_one == n + 1) {
        std::cout << -1 << std::endl;
    } else {
        std::cout << (min_len_to_make_one - 1) + (n - 1) << std::endl;
    }

    return 0;
}