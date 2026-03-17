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

    // FFT computation (simplified DFT - no FFTW needed)
    const int n = 5000;  // Reduced size but still meaningful
    vector<complex<double>> data(n);
    vector<complex<double>> result(n);
    
    random_device rd;
    mt19937 gen(rd());
    uniform_real_distribution<double> dis(0.0, 1.0);
    
    for (int i = 0; i < n; i++) {
        data[i] = complex<double>(dis(gen), dis(gen));
    }
    
    // Simple DFT computation (O(n^2) - simulates FFT workload)
    for (int k = 0; k < n; k++) {
        complex<double> sum(0.0, 0.0);
        for (int j = 0; j < n; j++) {
            double angle = -2.0 * M_PI * k * j / n;
            sum += data[j] * complex<double>(cos(angle), sin(angle));
        }
        result[k] = sum;
    }
    
    // Use result to prevent optimization
    double res = 0.0;
    for (int i = 0; i < n; i++) {
        res += abs(result[i]);
    }

    auto end = high_resolution_clock::now();
    auto duration = duration_cast<microseconds>(end - start);
    double exec_time = duration.count() / 1000000.0;
    
    cout << "Execution time: " << exec_time << " seconds" << endl;
    return 0;
}
