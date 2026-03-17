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

    // Vector operations workload
    const int n = 1000000;
    vector<double> a(n), b(n), c(n);
    
    random_device rd;
    mt19937 gen(rd());
    uniform_real_distribution<double> dis(0.0, 1.0);
    
    for (int i = 0; i < n; i++) {
        a[i] = dis(gen);
        b[i] = dis(gen);
    }
    
    // SIMD-friendly vector operations
    for (int i = 0; i < n; i++) {
        c[i] = a[i] * b[i] + sin(a[i]) * cos(b[i]);
    }
    
    double result = 0.0;
    for (int i = 0; i < n; i++) {
        result += c[i];
    }

    auto end = high_resolution_clock::now();
    auto duration = duration_cast<microseconds>(end - start);
    double exec_time = duration.count() / 1000000.0;
    
    cout << "Execution time: " << exec_time << " seconds" << endl;
    return 0;
}
