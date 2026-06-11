#include <iostream>
#include <vector>
#include <numeric>

int main() {
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(NULL);

    int n, k;
    std::cin >> n >> k;

    long long MOD = 1000000007;

    // dp_prev[j] stores the number of good sequences of length (current_length - 1) ending with j.
    // dp_curr[j] stores the number of good sequences of length current_length ending with j.
    std::vector<long long> dp_prev(n + 1);
    std::vector<long long> dp_curr(n + 1);

    // Base case: For length 1, any number j from 1 to n forms a good sequence.
    // So, there is 1 way to form a sequence of length 1 ending with j.
    for (int j = 1; j <= n; ++j) {
        dp_prev[j] = 1;
    }

    // Iterate for sequence length from 2 to k
    for (int length = 2; length <= k; ++length) {
        // Initialize dp_curr for the current length
        std::fill(dp_curr.begin(), dp_curr.end(), 0);

        // Iterate through all possible previous values (b_{length-1})
        for (int prev_val = 1; prev_val <= n; ++prev_val) {
            if (dp_prev[prev_val] == 0) {
                continue; // No sequences of length (length-1) ending with prev_val
            }
            // Iterate through all multiples of prev_val (b_length)
            // These are the values that prev_val can divide.
            for (int current_val = prev_val; current_val <= n; current_val += prev_val) {
                dp_curr[current_val] = (dp_curr[current_val] + dp_prev[prev_val]) % MOD;
            }
        }
        // After calculating all dp_curr values for the current length,
        // dp_curr becomes dp_prev for the next iteration.
        dp_prev = dp_curr;
    }

    // The total number of good sequences of length k is the sum of all dp_prev[j]
    // (which now holds counts for length k) for j from 1 to n.
    long long total_good_sequences = 0;
    for (int j = 1; j <= n; ++j) {
        total_good_sequences = (total_good_sequences + dp_prev[j]) % MOD;
    }

    std::cout << total_good_sequences << std::endl;

    return 0;
}