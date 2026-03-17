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

    // Branch intensive workload (increased size for measurable time)
    const int n = 500000;
    vector<int> arr(n);
    
    random_device rd;
    mt19937 gen(rd());
    uniform_int_distribution<int> dis(1, 100);
    
    for (int i = 0; i < n; i++) {
        arr[i] = dis(gen);
    }
    
    int result = 0;
    // Multiple passes to increase execution time
    for (int pass = 0; pass < 10; pass++) {
        for (int x : arr) {
            if (x < 25) {
                result += x * 2;
            } else if (x < 50) {
                result += x * 3;
            } else if (x < 75) {
                result += x * 4;
            } else {
                result += x * 5;
            }
        }
    }

    auto end = high_resolution_clock::now();
    auto duration = duration_cast<microseconds>(end - start);
    double exec_time = duration.count() / 1000000.0;
    
    cout << "Execution time: " << exec_time << " seconds" << endl;
    return 0;
}
