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

    // Hash table workload
    const int n = 100000;
    unordered_map<int, int> hash_table;
    
    random_device rd;
    mt19937 gen(rd());
    uniform_int_distribution<int> dis(1, 10000);
    
    for (int i = 0; i < n; i++) {
        int key = dis(gen);
        hash_table[key] = i;
    }
    
    int result = 0;
    for (int i = 0; i < n; i++) {
        int key = dis(gen);
        if (hash_table.find(key) != hash_table.end()) {
            result += hash_table[key];
        }
    }

    auto end = high_resolution_clock::now();
    auto duration = duration_cast<microseconds>(end - start);
    double exec_time = duration.count() / 1000000.0;
    
    cout << "Execution time: " << exec_time << " seconds" << endl;
    return 0;
}
