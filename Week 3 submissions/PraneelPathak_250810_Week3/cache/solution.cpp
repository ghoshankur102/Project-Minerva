#include <iostream>
#include <vector>
#include <numeric>
#include <algorithm>

// Function to count trailing zeros (v_2(n))
// This determines the highest power of 2 that divides n.
// For example:
// v_2(6) = 1 (6 = 2 * 3)
// v_2(4) = 2 (4 = 2^2 * 1)
// v_2(12) = 2 (12 = 2^2 * 3)
// v_2(3) = 0 (3 is odd)
int count_trailing_zeros(int n) {
    // Problem constraints state a_i >= 1, so n will never be 0.
    int count = 0;
    // While n is even (lowest bit is 0)
    while ((n & 1) == 0) {
        n >>= 1; // Divide n by 2
        count++;
    }
    return count;
}

int main() {
    // Optimize C++ standard streams for competitive programming.
    // This unties cin from cout and disables synchronization with C stdio,
    // leading to faster input/output operations.
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(NULL);

    int n;
    std::cin >> n; // Read the length of the array

    std::vector<int> a(n);
    long long total_sum = 0; // Use long long for sum to prevent potential overflow, though int is sufficient for 200000
    for (int i = 0; i < n; ++i) {
        std::cin >> a[i]; // Read array elements
        total_sum += a[i]; // Calculate total sum
    }

    // Step 1: Check if the array is already "good".
    // An array is good if its total sum is odd, because S/2 would not be an integer.
    if (total_sum % 2 != 0) {
        std::cout << 0 << std::endl; // 0 removals needed
        return 0; // Terminate
    }

    // If total_sum is even, we need to check if there's a subset that sums to total_sum / 2.
    // This is a classic Subset Sum Problem.
    long long target_sum = total_sum / 2;
    // dp[j] will be true if a sum of j can be formed using a subset of elements.
    std::vector<bool> dp(target_sum + 1, false);
    dp[0] = true; // A sum of 0 can always be formed (by choosing no elements)

    // Iterate through each element of the array
    for (int x : a) {
        // Iterate backwards from target_sum down to x.
        // This ensures that each element x is used at most once in forming a sum.
        for (long long j = target_sum; j >= x; --j) {
            dp[j] = dp[j] || dp[j - x];
        }
    }

    // If dp[target_sum] is false, it means no subset sums to total_sum / 2.
    // Therefore, the array cannot be partitioned into two equal sums, and is already good.
    if (!dp[target_sum]) {
        std::cout << 0 << std::endl; // 0 removals needed
        return 0; // Terminate
    }

    // Step 2: If we reach here, the array is NOT good.
    // This means total_sum is even AND there exists a subset summing to total_sum / 2.
    // We need to remove the minimum number of elements to make it good.
    // The problem statement implies 1 removal is always sufficient, and we aim for that.

    // Strategy:
    // 1. Try to find and remove an odd element.
    //    If an odd element 'x' is removed, the new total sum becomes (total_sum - x).
    //    Since total_sum is even and x is odd, (even - odd) = odd.
    //    An array with an odd total sum is always good.
    for (int i = 0; i < n; ++i) {
        if (a[i] % 2 != 0) { // Check if the element is odd
            std::cout << 1 << std::endl; // 1 removal needed
            std::cout << i + 1 << std::endl; // Print 1-based index of the removed element
            return 0; // Terminate
        }
    }

    // 2. If we reach this point, it means all elements in the array are even.
    //    Removing any even element will result in a new total sum that is still even
    //    (even - even = even). So, we cannot make the sum odd by removing one element.
    //    In this case, we need to remove an element such that the remaining array
    //    cannot be partitioned into two equal sums.
    //    The strategy is to remove an element 'a_k' that has the minimum 'v_2' value
    //    (i.e., it's divisible by 2 the fewest number of times compared to other elements).
    //    This ensures that after repeatedly dividing all elements by 2 until at least one
    //    becomes odd, the element corresponding to 'a_k' will be the first to become odd.
    //    Removing it will make the "scaled down" array have an odd total sum, thus making it good.

    int min_v2 = count_trailing_zeros(a[0]); // Initialize with the v_2 of the first element
    int index_to_remove = 0; // Initialize with the index of the first element

    // Iterate from the second element to find an element with a smaller v_2
    for (int i = 1; i < n; ++i) {
        int current_v2 = count_trailing_zeros(a[i]);
        if (current_v2 < min_v2) {
            min_v2 = current_v2;
            index_to_remove = i;
        }
    }

    std::cout << 1 << std::endl; // 1 removal needed
    std::cout << index_to_remove + 1 << std::endl; // Print 1-based index of the removed element

    return 0; // Terminate
}