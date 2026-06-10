#include <iostream>
#include <vector>
#include <algorithm>
#include <functional>

const int MOD = 1e9 + 7;
const int MAX_N = 1000;

long long fact[MAX_N + 1];
long long invFact[MAX_N + 1];

long long power(long long base, long long exp) {
    long long res = 1;
    base %= MOD;
    while (exp > 0) {
        if (exp % 2 == 1) {
            res = (res * base) % MOD;
        }
        base = (base * base) % MOD;
        exp /= 2;
    }
    return res;
}

long long modInverse(long long n) {
    return power(n, MOD - 2);
}

long long nCr_mod_p(int n, int r) {
    if (r < 0 || r > n) return 0;
    if (r == 0 || r == n) return 1;
    return (((fact[n] * invFact[r]) % MOD) * invFact[n - r]) % MOD;
}

void precompute_factorials() {
    fact[0] = 1;
    for (int i = 1; i <= MAX_N; i++) {
        fact[i] = (fact[i - 1] * i) % MOD;
    }
    
    invFact[MAX_N] = modInverse(fact[MAX_N]);
    for (int i = MAX_N - 1; i >= 0; i--) {
        invFact[i] = (invFact[i + 1] * (i + 1)) % MOD;
    }
}

void solve() {
    int n, k;
    std::cin >> n >> k;
    std::vector<int> a(n);
    for (int i = 0; i < n; ++i) {
        std::cin >> a[i];
    }

    std::sort(a.begin(), a.end(), std::greater<int>());

    int threshold_val = a[k - 1];

    int total_threshold_count = 0;
    for (int x : a) {
        if (x == threshold_val) {
            total_threshold_count++;
        }
    }

    int required_threshold_count = 0;
    for (int i = 0; i < k; ++i) {
        if (a[i] == threshold_val) {
            required_threshold_count++;
        }
    }

    std::cout << nCr_mod_p(total_threshold_count, required_threshold_count) << std::endl;
}

int main() {
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(NULL);

    precompute_factorials();

    int t;
    std::cin >> t;
    while (t--) {
        solve();
    }

    return 0;
}