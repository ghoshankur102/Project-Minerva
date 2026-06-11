#include <iostream>
#include <vector>
#include <numeric>

int main() {
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(NULL);

    int n, q;
    std::cin >> n >> q;

    std::vector<int> first_occurrence_pos(51, 0); // Stores 1-indexed position for each color (1 to 50)

    for (int i = 1; i <= n; ++i) {
        int color;
        std::cin >> color;
        if (first_occurrence_pos[color] == 0) {
            first_occurrence_pos[color] = i;
        }
    }

    for (int j = 0; j < q; ++j) {
        int query_color;
        std::cin >> query_color;

        int current_pos = first_occurrence_pos[query_color];
        std::cout << current_pos << (j == q - 1 ? "" : " ");

        // Update positions for other colors
        for (int c = 1; c <= 50; ++c) {
            if (c == query_color) {
                // This color is moved to position 1
                first_occurrence_pos[c] = 1;
            } else if (first_occurrence_pos[c] != 0 && first_occurrence_pos[c] < current_pos) {
                // Other colors that were above the moved card shift down
                first_occurrence_pos[c]++;
            }
        }
    }
    std::cout << std::endl;

    return 0;
}