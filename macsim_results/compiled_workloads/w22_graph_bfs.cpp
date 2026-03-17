#include <iostream>
#include <vector>
#include <random>
#include <chrono>
#include <cmath>
#include <algorithm>
#include <complex>

#include <queue>
#include <unordered_map>
#include <functional>

using namespace std;
using namespace std::chrono;

int main() {
    auto start = high_resolution_clock::now();

    // Graph BFS workload
    const int n = 5000;
    vector<vector<int>> graph(n);
    
    // Create a graph
    for (int i = 0; i < n; i++) {
        for (int j = i + 1; j < min(i + 10, n); j++) {
            graph[i].push_back(j);
            graph[j].push_back(i);
        }
    }
    
    // BFS
    vector<bool> visited(n, false);
    queue<int> q;
    q.push(0);
    visited[0] = true;
    int result = 0;
    
    while (!q.empty()) {
        int node = q.front();
        q.pop();
        result++;
        
        for (int neighbor : graph[node]) {
            if (!visited[neighbor]) {
                visited[neighbor] = true;
                q.push(neighbor);
            }
        }
    }

    auto end = high_resolution_clock::now();
    auto duration = duration_cast<microseconds>(end - start);
    double exec_time = duration.count() / 1000000.0;
    
    cout << "Execution time: " << exec_time << " seconds" << endl;
    return 0;
}
