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

    // N-body simulation
    const int n = 1000;
    vector<double> x(n), y(n), z(n), vx(n), vy(n), vz(n), mass(n);
    
    random_device rd;
    mt19937 gen(rd());
    uniform_real_distribution<double> pos_dis(-100.0, 100.0);
    uniform_real_distribution<double> mass_dis(1.0, 10.0);
    
    for (int i = 0; i < n; i++) {
        x[i] = pos_dis(gen);
        y[i] = pos_dis(gen);
        z[i] = pos_dis(gen);
        vx[i] = vy[i] = vz[i] = 0.0;
        mass[i] = mass_dis(gen);
    }
    
    // Simple force calculation
    for (int iter = 0; iter < 10; iter++) {
        for (int i = 0; i < n; i++) {
            double fx = 0.0, fy = 0.0, fz = 0.0;
            for (int j = 0; j < n; j++) {
                if (i != j) {
                    double dx = x[j] - x[i];
                    double dy = y[j] - y[i];
                    double dz = z[j] - z[i];
                    double dist_sq = dx*dx + dy*dy + dz*dz + 1.0;  // Avoid division by zero
                    double force = mass[i] * mass[j] / dist_sq;
                    fx += force * dx;
                    fy += force * dy;
                    fz += force * dz;
                }
            }
            vx[i] += fx * 0.01;
            vy[i] += fy * 0.01;
            vz[i] += fz * 0.01;
        }
    }
    
    double result = 0.0;
    for (int i = 0; i < n; i++) {
        result += sqrt(vx[i]*vx[i] + vy[i]*vy[i] + vz[i]*vz[i]);
    }

    auto end = high_resolution_clock::now();
    auto duration = duration_cast<microseconds>(end - start);
    double exec_time = duration.count() / 1000000.0;
    
    cout << "Execution time: " << exec_time << " seconds" << endl;
    return 0;
}
