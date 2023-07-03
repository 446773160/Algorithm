#include <vector>
#include <string>
#include <algorithm>
using namespace std;

// 交换函数
void swap(int &a, int &b)
{
    int temp = a;
    a = b;
    b = temp;
}
// 快速排序 A为数组，l为左边界，r为右边界
void quicksort(int *A, int l, int r)
{
    if (l >= r)
        return;
    int i = l, j = r;
    int pivot = A[(l + r) >> 1];
    while (i < j)
    {
        while (A[i] < pivot)
            i++;
        while (A[j] > pivot)
            j--;
        if (i < j)
            swap(A[i], A[j]);
    }
    quicksort(A, l, j);
    quicksort(A, j + 1, r);
}
//归并排序
void merge_sort(int *A, int l, int r)
{
    if (l >= r)
        return;
    int mid = (l + r) >> 1; // mid = (l+r)/2
    merge_sort(A, l, mid);
    merge_sort(A, mid + 1, r);
    int i = l, j = mid + 1, k = 0; // i为左边数组的起点，j为右边数组的起点，k为临时数组的起点
    int temp[r - l + 1];           //临时数组
    while (i <= mid && j <= r)
    {
        if (A[i] <= A[j])
            temp[k++] = A[i++]; //将左边数组的值赋给临时数组
        else
            temp[k++] = A[j++]; //将右边数组的值赋给临时数组
    }
    while (i <= mid)
        temp[k++] = A[i++]; //将左边数组剩余的值赋给临时数组
    while (j <= r)
        temp[k++] = A[j++]; //将右边数组剩余的值赋给临时数组
    for (int i = l, j = 0; i <= r; i++, j++)
        A[i] = temp[j]; //将临时数组的值赋给原数组
}
//堆排序
void downAdjust(int *A, int low, int high)
{
    int i = low, j = i * 2; // i为父节点，j为左孩子
    while (j <= high)
    {
        if (j + 1 <= high && A[j + 1] > A[j]) //如果右孩子存在且大于左孩子
            j = j + 1;                        // j指向右孩子
        if (A[j] > A[i])                      //如果孩子大于父节点
        {
            swap(A[i], A[j]); //交换父节点和孩子
            i = j;            // i指向孩子
            j = i * 2;        // j指向孩子的左孩子
        }
        else
            break;
    }
}
//高精度加法  A和B都是倒序存储的 0 <= A.size() <= 10000 0为表示个位
vector<int> add(vector<int> &A, vector<int> &B)
{
    if (A.size() < B.size())
        return add(B, A);
    vector<int> C;
    int t = 0;
    for (int i = 0; i < A.size(); i++)
    {
        t += A[i];
        if (i < B.size())
            t += B[i];
        C.push_back(t % 10);
        t /= 10;
    }
    if (t)
        C.push_back(1);
    return C;
}

//高精度减法
vector<int> sub(vector<int> &A, vector<int> &B)
{
    vector<int> C;
    for (int i = 0, t = 0; i < A.size(); i++)
    {
        t = A[i] - t;
        if (i < B.size())
            t -= B[i];
        C.push_back((t + 10) % 10);
        if (t < 0)
            t = 1;
        else
            t = 0;
    }
    //去除前导0
    while (C.size() > 1 && C.back() == 0)
        C.pop_back();
    return C;
}
//高精度乘法
vector<int> mul(vector<int> &A, int b)
{
    vector<int> C; // C存放结果
    int t = 0;
    for (int i = 0; i < A.size() || t; i++)
    {
        if (i < A.size())
            t += A[i] * b;
        C.push_back(t % 10);
        t = t / 10;
    }
    return C;
}

//高精度除法 A/b = C...r   余数r通过引用传递
vector<int> div(vector<int> &A, int b, int &r)
{
    vector<int> C; // C存放结果
    r = 0;
    for (int i = A.size() - 1; i >= 0; i--)
    {
        r = r * 10 + A[i]; //余数
        C.push_back(r / b);
        r %= b;
    }
    reverse(C.begin(), C.end());
    //去除前导0
    while (C.size() > 1 && C.back() == 0)
        C.pop_back();
    return C;
}
