#include <iostream>
#include <string>
#include <vector>

int main() {
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(NULL);
    std::string s;
    std::cin >> s;

    long long dp_a_waiting_for_b = 0; // Number of sequences ending with 'a' that need a 'b'
    long long dp_b_waiting_for_a = 0; // Number of sequences ending with 'a', having seen a 'b', now need another 'a'
    long long total_sequences_count = 0;

    long long MOD = 1e9 + 7;

    for (char c : s) {
        if (c == 'a') {
            // When an 'a' is encountered:
            // 1. It can start a new sequence of length 1.
            // 2. It can extend sequences that were dp_b_waiting_for_a.
            // So, the number of new sequences ending with this 'a' is (1 + dp_b_waiting_for_a).
            long long newly_formed_a_sequences = (1 + dp_b_waiting_for_a) % MOD;
            
            // Add these newly formed sequences to the total count.
            total_sequences_count = (total_sequences_count + newly_formed_a_sequences) % MOD;
            
            // All sequences that just ended with this 'a' (newly_formed_a_sequences)
            // are now waiting for a 'b'.
            // Also, any sequences that were already dp_a_waiting_for_b are still waiting.
            dp_a_waiting_for_b = (dp_a_waiting_for_b + newly_formed_a_sequences) % MOD;
        } else if (c == 'b') {
            // When a 'b' is encountered:
            // All sequences that were dp_a_waiting_for_b have now seen a 'b'.
            // They transition to the state of dp_b_waiting_for_a.
            dp_b_waiting_for_a = (dp_b_waiting_for_a + dp_a_waiting_for_b) % MOD;
            
            // Since all sequences previously in dp_a_waiting_for_b have now seen a 'b',
            // there are no sequences left in the 'waiting for b' state from before this 'b'.
            dp_a_waiting_for_b = 0;
        } else {
            // Any other character breaks the chain.
            // No sequences can be extended through this character.
            dp_a_waiting_for_b = 0;
            dp_b_waiting_for_a = 0;
        }
    }

    std::cout << total_sequences_count << std::endl;

    return 0;
}