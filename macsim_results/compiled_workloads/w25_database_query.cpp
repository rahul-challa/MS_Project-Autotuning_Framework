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

    // Database query simulation
    const int n = 50000;
    vector<tuple<int, string, double>> table;
    
    random_device rd;
    mt19937 gen(rd());
    uniform_int_distribution<int> id_dis(1, 1000);
    uniform_real_distribution<double> val_dis(0.0, 100.0);
    
    for (int i = 0; i < n; i++) {
        table.push_back(make_tuple(id_dis(gen), "name" + to_string(i), val_dis(gen)));
    }
    
    // Simulate join and aggregation
    double result = 0.0;
    int count = 0;
    for (const auto& row : table) {
        int id = get<0>(row);
        double val = get<2>(row);
        if (id % 2 == 0 && val > 50.0) {
            result += val;
            count++;
        }
    }
    result = count > 0 ? result / count : 0.0;

    auto end = high_resolution_clock::now();
    auto duration = duration_cast<microseconds>(end - start);
    double exec_time = duration.count() / 1000000.0;
    
    cout << "Execution time: " << exec_time << " seconds" << endl;
    return 0;
}
