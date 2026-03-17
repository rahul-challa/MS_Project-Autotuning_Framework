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

    // Image processing workload (convolution)
    const int width = 500, height = 500;
    vector<vector<double>> image(height, vector<double>(width));
    vector<vector<double>> kernel = {{0.1, 0.2, 0.1}, {0.2, 0.4, 0.2}, {0.1, 0.2, 0.1}};
    
    random_device rd;
    mt19937 gen(rd());
    uniform_real_distribution<double> dis(0.0, 1.0);
    
    for (int i = 0; i < height; i++) {
        for (int j = 0; j < width; j++) {
            image[i][j] = dis(gen);
        }
    }
    
    vector<vector<double>> result_img(height, vector<double>(width, 0.0));
    for (int i = 1; i < height - 1; i++) {
        for (int j = 1; j < width - 1; j++) {
            for (int ki = 0; ki < 3; ki++) {
                for (int kj = 0; kj < 3; kj++) {
                    result_img[i][j] += image[i + ki - 1][j + kj - 1] * kernel[ki][kj];
                }
            }
        }
    }
    
    double result = 0.0;
    for (int i = 0; i < height; i++) {
        for (int j = 0; j < width; j++) {
            result += result_img[i][j];
        }
    }

    auto end = high_resolution_clock::now();
    auto duration = duration_cast<microseconds>(end - start);
    double exec_time = duration.count() / 1000000.0;
    
    cout << "Execution time: " << exec_time << " seconds" << endl;
    return 0;
}
