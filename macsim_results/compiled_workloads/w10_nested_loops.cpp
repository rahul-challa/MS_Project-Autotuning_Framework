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

    // Nested loops workload (ensure measurable time)
    const int n = 200;
    double result = 0.0;
    
    // Multiple nested loop passes
    for (int pass = 0; pass < 5; pass++) {
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                for (int k = 0; k < n; k++) {
                    result += sin(i * 0.01 + pass) * cos(j * 0.01 + pass) * tan(k * 0.01 + 1.0 + pass);
                }
            }
        }
    }
    
    // Additional computation to ensure measurable time
    for (int i = 0; i < 10000; i++) {
        result = sqrt(abs(result)) + 1.0;
        result = log1p(result);
    }

    auto end = high_resolution_clock::now();
    auto duration = duration_cast<microseconds>(end - start);
    double exec_time = duration.count() / 1000000.0;
    
    cout << "Execution time: " << exec_time << " seconds" << endl;
    return 0;
}
