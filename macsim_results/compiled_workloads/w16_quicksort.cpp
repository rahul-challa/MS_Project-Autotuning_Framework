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

    // Quicksort workload
    const int n = 50000;
    vector<int> arr(n);
    
    random_device rd;
    mt19937 gen(rd());
    uniform_int_distribution<int> dis(1, 10000);
    
    for (int i = 0; i < n; i++) {
        arr[i] = dis(gen);
    }
    
    sort(arr.begin(), arr.end());
    
    int result = 0;
    for (int i = 0; i < n; i += 100) {
        result += arr[i];
    }

    auto end = high_resolution_clock::now();
    auto duration = duration_cast<microseconds>(end - start);
    double exec_time = duration.count() / 1000000.0;
    
    cout << "Execution time: " << exec_time << " seconds" << endl;
    return 0;
}
