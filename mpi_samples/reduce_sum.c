#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

static long long min_ll(long long a, long long b) {
    return a < b ? a : b;
}

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);

    int rank = 0;
    int size = 0;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    long long n = 1000000LL;
    if (argc > 1) {
        n = atoll(argv[1]);
    }

    if (n < 0) {
        if (rank == 0) {
            fprintf(stderr, "N must be non-negative\n");
        }
        MPI_Finalize();
        return 2;
    }

    long long base = n / size;
    long long rem = n % size;
    long long local_count = base + (rank < rem ? 1 : 0);
    long long start = rank * base + min_ll(rank, rem) + 1;
    long long end = start + local_count - 1;
    long long local_sum = 0;

    if (local_count > 0) {
        local_sum = (start + end) * local_count / 2;
    }

    long long mpi_sum = 0;
    MPI_Reduce(&local_sum, &mpi_sum, 1, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        long long expected = n * (n + 1) / 2;
        printf("N=%lld expected=%lld mpi_sum=%lld Correct? %s\n",
               n, expected, mpi_sum, expected == mpi_sum ? "YES" : "NO");
    }

    MPI_Finalize();
    return 0;
}

