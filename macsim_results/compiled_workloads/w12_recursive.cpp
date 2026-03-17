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

    // Recursive workload (Fibonacci-like)
    function<long long(int)> fib = [&](int n) -> long long {
        if (n <= 1) return n;
        return fib(n-1) + fib(n-2);
    };
    
    long long result = 0;
    for (int i = 30; i < 35; i++) {
        result += fib(i);
    }

    auto end = high_resolution_clock::now();
    auto duration = duration_cast<microseconds>(end - start);
    double exec_time = duration.count() / 1000000.0;
    
    cout << "Execution time: " << exec_time << " seconds" << endl;
    return 0;
}
