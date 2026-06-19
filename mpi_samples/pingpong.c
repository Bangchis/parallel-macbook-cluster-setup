#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);

    int rank = 0;
    int size = 0;
    int value = 42;
    int iters = 10000;

    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (argc > 1) {
        iters = atoi(argv[1]);
    }
    if (iters <= 0) {
        iters = 10000;
    }

    if (size < 2) {
        if (rank == 0) {
            printf("pingpong needs at least 2 ranks; got %d\n", size);
        }
        MPI_Finalize();
        return 0;
    }

    MPI_Barrier(MPI_COMM_WORLD);
    double start = MPI_Wtime();

    for (int i = 0; i < iters; ++i) {
        if (rank == 0) {
            MPI_Send(&value, 1, MPI_INT, 1, 0, MPI_COMM_WORLD);
            MPI_Recv(&value, 1, MPI_INT, 1, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        } else if (rank == 1) {
            MPI_Recv(&value, 1, MPI_INT, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            MPI_Send(&value, 1, MPI_INT, 0, 0, MPI_COMM_WORLD);
        }
    }

    double end = MPI_Wtime();

    if (rank == 0) {
        double avg_us = (end - start) * 1000000.0 / iters;
        printf("iters=%d average_round_trip_us=%.3f\n", iters, avg_us);
    }

    MPI_Finalize();
    return 0;
}

