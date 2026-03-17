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

    // Tree traversal workload
    struct TreeNode {
        int val;
        TreeNode* left;
        TreeNode* right;
        TreeNode(int v) : val(v), left(nullptr), right(nullptr) {}
    };
    
    // Build a binary tree
    const int n = 10000;
    vector<TreeNode*> nodes;
    for (int i = 0; i < n; i++) {
        nodes.push_back(new TreeNode(i));
    }
    
    for (int i = 0; i < n; i++) {
        if (2*i + 1 < n) nodes[i]->left = nodes[2*i + 1];
        if (2*i + 2 < n) nodes[i]->right = nodes[2*i + 2];
    }
    
    // In-order traversal
    function<int(TreeNode*)> traverse = [&](TreeNode* node) -> int {
        if (!node) return 0;
        return traverse(node->left) + node->val + traverse(node->right);
    };
    
    int result = traverse(nodes[0]);
    
    // Cleanup
    for (auto node : nodes) delete node;

    auto end = high_resolution_clock::now();
    auto duration = duration_cast<microseconds>(end - start);
    double exec_time = duration.count() / 1000000.0;
    
    cout << "Execution time: " << exec_time << " seconds" << endl;
    return 0;
}
