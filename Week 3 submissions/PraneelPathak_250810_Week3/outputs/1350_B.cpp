#include <iostream>
#include <vector>
#include <algorithm> // For std::max

void solve() {
    int n;
    std::cin >> n;

    // Models are 1-indexed, so we use n+1 size for vectors.
    // s[i] stores the size of model i.
    std::vector<int> s(n + 1); 
    for (int i = 1; i <= n; ++i) {
        std::cin >> s[i];
    }

    // dp[i] stores the maximum length of a beautiful arrangement ending with model i.
    // Any single model itself forms a beautiful arrangement of length 1.
    // So, initialize all dp values to 1.
    std::vector<int> dp(n + 1, 1);

    // max_models will store the overall maximum length found across all possible arrangements.
    // Since any single model is a beautiful arrangement, the minimum length is 1.
    int max_models = 1; 

    // Iterate through each model i from 1 to n.
    // When we are at model i, dp[i] has already been potentially updated by all its valid predecessors p < i.
    // Thus, dp[i] at this point represents the maximum length of an arrangement ending at i.
    // We then use this finalized dp[i] to potentially extend arrangements to its multiples j > i.
    for (int i = 1; i <= n; ++i) {
        // Update max_models with the current dp[i] value.
        // This ensures max_models tracks the overall maximum length found so far.
        max_models = std::max(max_models, dp[i]);

        // Iterate through all multiples of i (j = 2*i, 3*i, ...) up to n.
        // These j's are potential successors to i in a beautiful arrangement.
        for (int j = 2 * i; j <= n; j += i) {
            // Check the condition for extending the arrangement: s_i < s_j
            if (s[i] < s[j]) {
                // If we can extend an arrangement ending at i by adding model j,
                // the new length would be dp[i] + 1.
                // We update dp[j] if this new length is greater than its current value.
                dp[j] = std::max(dp[j], dp[i] + 1);
            }
        }
    }

    // After iterating through all models, max_models will hold the maximum length
    // of any beautiful arrangement.
    std::cout << max_models << std::endl;
}

int main() {
    // Optimize C++ standard streams for competitive programming.
    // This unties cin/cout from the C standard I/O and disables synchronization,
    // making input/output operations faster.
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(NULL);

    int t;
    std::cin >> t; // Read the number of test queries.
    while (t--) {
        solve(); // Process each query.
    }

    return 0;
}