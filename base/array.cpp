#include <iostream>
#include <vector>
#include <algorithm>
#include <string>
#include "fun.h"
using namespace std;
int main()
{
    string a;
    int b;
    cin >> a >> b;
    vector<int> A, B;
    for (int i = a.size() - 1; i >= 0; i--)
        A.push_back(a[i] - '0'); //将a的每一位存入A 例如a=1234  A={4,3,2,1} 减去'0'的ASCII码转为成整数
    // for (int i = b.size() - 1; i >= 0; i--)
    //     B.push_back(b[i] - '0');
    auto C = mul(A, b);
    for (int i = C.size() - 1; i >= 0; i--)
        cout << C[i];
    return 0;
}