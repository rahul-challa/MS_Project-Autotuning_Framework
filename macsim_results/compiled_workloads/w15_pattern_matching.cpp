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

    // Pattern matching workload (increased size)
    string text = "";
    for (int i = 0; i < 500000; i++) {
        text += "abcdefghijklmnopqrstuvwxyz";
    }
    string pattern = "xyzabc";
    
    int result = 0;
    for (size_t i = 0; i <= text.length() - pattern.length(); i++) {
        bool match = true;
        for (size_t j = 0; j < pattern.length(); j++) {
            if (text[i + j] != pattern[j]) {
                match = false;
                break;
            }
        }
        if (match) result++;
    }

    auto end = high_resolution_clock::now();
    auto duration = duration_cast<microseconds>(end - start);
    double exec_time = duration.count() / 1000000.0;
    
    cout << "Execution time: " << exec_time << " seconds" << endl;
    return 0;
}
