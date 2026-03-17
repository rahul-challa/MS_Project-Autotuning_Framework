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

    // Sparse matrix operations
    const int n = 10000;
    const int nnz = 100000;  // Non-zero elements
    vector<tuple<int, int, double>> sparse_matrix;
    
    random_device rd;
    mt19937 gen(rd());
    uniform_int_distribution<int> idx_dis(0, n-1);
    uniform_real_distribution<double> val_dis(0.0, 1.0);
    
    for (int i = 0; i < nnz; i++) {
        sparse_matrix.push_back(make_tuple(idx_dis(gen), idx_dis(gen), val_dis(gen)));
    }
    
    vector<double> x(n, 1.0);
    vector<double> y(n, 0.0);
    
    for (const auto& elem : sparse_matrix) {
        int row = get<0>(elem);
        int col = get<1>(elem);
        double val = get<2>(elem);
        y[row] += val * x[col];
    }
    
    double result = 0.0;
    for (int i = 0; i < n; i++) {
        result += y[i];
    }

    auto end = high_resolution_clock::now();
    auto duration = duration_cast<microseconds>(end - start);
    double exec_time = duration.count() / 1000000.0;
    
    cout << "Execution time: " << exec_time << " seconds" << endl;
    return 0;
}
