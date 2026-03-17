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

    // Data compression workload (LZ-like)
    const int n = 100000;
    string data = "";
    for (int i = 0; i < n; i++) {
        data += "abcdefghijklmnopqrstuvwxyz";
    }
    
    string compressed = "";
    for (size_t i = 0; i < data.length(); i++) {
        int run_length = 1;
        while (i + run_length < data.length() && data[i] == data[i + run_length] && run_length < 255) {
            run_length++;
        }
        if (run_length > 3) {
            compressed += data[i];
            compressed += (char)run_length;
            i += run_length - 1;
        } else {
            compressed += data[i];
        }
    }
    
    int result = compressed.length();

    auto end = high_resolution_clock::now();
    auto duration = duration_cast<microseconds>(end - start);
    double exec_time = duration.count() / 1000000.0;
    
    cout << "Execution time: " << exec_time << " seconds" << endl;
    return 0;
}
