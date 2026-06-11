#include <iostream>
#include <vector>
#include <algorithm>
#include <utility> // For std::pair

// Structure to represent an event (start or end of a show)
struct Event {
    int time;
    int type; // +1 for a show starting, -1 for a show ending

    // Custom comparison operator for sorting events
    // Events are primarily sorted by time in ascending order.
    // If times are equal, start events (+1) are processed before end events (-1).
    // This ensures that if a show ends at time T and another starts at time T,
    // the count of active shows correctly reflects both being active at time T.
    bool operator<(const Event& other) const {
        if (time != other.time) {
            return time < other.time;
        }
        // Tie-breaker: process start events (+1) before end events (-1)
        return type > other.type; 
    }
};

int main() {
    // Optimize C++ standard streams for faster input/output
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(NULL);

    int n;
    std::cin >> n; // Read the number of shows

    std::vector<Event> events;
    events.reserve(2 * n); // Pre-allocate memory for 2*n events (one start, one end for each show)

    // Read show intervals and create events
    for (int i = 0; i < n; ++i) {
        int l, r;
        std::cin >> l >> r;
        events.push_back({l, 1});  // Add a start event at time l
        events.push_back({r, -1}); // Add an end event at time r
    }

    // Sort all events using the custom comparison operator
    std::sort(events.begin(), events.end());

    int current_shows = 0; // Counter for currently active shows
    int max_shows = 0;     // Maximum number of shows active at any point

    // Sweep line algorithm: iterate through sorted events
    for (const auto& event : events) {
        current_shows += event.type; // Adjust the count of active shows
        
        // Update the maximum number of simultaneously active shows
        if (current_shows > max_shows) {
            max_shows = current_shows;
        }
    }

    // Check if two TVs are sufficient
    if (max_shows <= 2) {
        std::cout << "YES\n";
    } else {
        std::cout << "NO\n";
    }

    return 0;
}