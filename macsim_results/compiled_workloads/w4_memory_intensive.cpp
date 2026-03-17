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

    // Memory intensive workload
    const int n = 2000;
    vector<vector<double>> arr(n, vector<double>(n));
    
    random_device rd;
    mt19937 gen(rd());
    uniform_real_distribution<double> dis(0.0, 1.0);
    
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            arr[i][j] = dis(gen);
        }
    }
    
    double result = 0.0;
    for (int i = 0; i < n; i += 8) {
        for (int j = 0; j < n; j += 8) {
            result += arr[i][j];
        }
    }

    auto end = high_resolution_clock::now();
    auto duration = duration_cast<microseconds>(end - start);
    double exec_time = duration.count() / 1000000.0;
    
    cout << "Execution time: " << exec_time << " seconds" << endl;
    return 0;
}
