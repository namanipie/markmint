#include <stdio.h>

int main() {
    int n, i = 0, j, temp;
    scanf("%d", &n);

    int a[n];

    while (i < n)
        scanf("%d", &a[i++]);

    i = 0;
    while (i < n - 1) {
        j = 0;
        while (j < n - i - 1) {
            if (a[j] % 2 > a[j + 1] % 2) {
                temp = a[j];
                a[j] = a[j + 1];
                a[j + 1] = temp;
            }
            j++;
        }
        i++;
    }

    i = 0;
    while (i < n)
        printf("%d ", a[i++]);

    return 0;
}