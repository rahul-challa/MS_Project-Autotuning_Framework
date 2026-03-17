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

    // Particle filter workload
    const int n_particles = 10000;
    vector<double> particles(n_particles);
    vector<double> weights(n_particles);
    
    random_device rd;
    mt19937 gen(rd());
    uniform_real_distribution<double> pos_dis(-10.0, 10.0);
    uniform_real_distribution<double> weight_dis(0.0, 1.0);
    
    for (int i = 0; i < n_particles; i++) {
        particles[i] = pos_dis(gen);
        weights[i] = weight_dis(gen);
    }
    
    // Normalize weights
    double sum_weights = 0.0;
    for (int i = 0; i < n_particles; i++) {
        sum_weights += weights[i];
    }
    for (int i = 0; i < n_particles; i++) {
        weights[i] /= sum_weights;
    }
    
    // Resample
    vector<double> new_particles(n_particles);
    uniform_real_distribution<double> u_dis(0.0, 1.0);
    for (int i = 0; i < n_particles; i++) {
        double u = u_dis(gen);
        double cumsum = 0.0;
        for (int j = 0; j < n_particles; j++) {
            cumsum += weights[j];
            if (u <= cumsum) {
                new_particles[i] = particles[j];
                break;
            }
        }
    }
    
    double result = 0.0;
    for (int i = 0; i < n_particles; i++) {
        result += new_particles[i];
    }

    auto end = high_resolution_clock::now();
    auto duration = duration_cast<microseconds>(end - start);
    double exec_time = duration.count() / 1000000.0;
    
    cout << "Execution time: " << exec_time << " seconds" << endl;
    return 0;
}
