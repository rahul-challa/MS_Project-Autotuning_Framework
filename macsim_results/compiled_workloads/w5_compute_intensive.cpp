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

    // Compute intensive workload
    const int n = 500;
    vector<vector<double>> A(n, vector<double>(n));
    
    random_device rd;
    mt19937 gen(rd());
    uniform_real_distribution<double> dis(0.0, 1.0);
    
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            A[i][j] = dis(gen);
        }
    }
    
    // Heavy mathematical operations (multiple passes)
    vector<vector<double>> B(n, vector<double>(n));
    for (int iter = 0; iter < 10; iter++) {
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                B[i][j] = sin(A[i][j]) * cos(A[i][j]);
                A[i][j] = sqrt(abs(B[i][j]));
                B[i][j] = log1p(A[i][j]);
            }
        }
    }
    
    double result = 0.0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            result += B[i][j];
        }
    }

    auto end = high_resolution_clock::now();
    auto duration = duration_cast<microseconds>(end - start);
    double exec_time = duration.count() / 1000000.0;
    
    cout << "Execution time: " << exec_time << " seconds" << endl;
    return 0;
}
