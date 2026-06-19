#include <mpi.h>
#include <stdio.h>
#include <unistd.h>

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);

    int rank = 0;
    int size = 0;
    int token = 0;
    char hostname[256];

    gethostname(hostname, sizeof(hostname));
    hostname[sizeof(hostname) - 1] = '\0';

    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (size < 2) {
        if (rank == 0) {
            printf("ring needs at least 2 ranks; got %d\n", size);
        }
        MPI_Finalize();
        return 0;
    }

    if (rank == 0) {
        token = 1;
        printf("rank %d on %s starts token=%d\n", rank, hostname, token);
        MPI_Send(&token, 1, MPI_INT, 1, 0, MPI_COMM_WORLD);
        MPI_Recv(&token, 1, MPI_INT, size - 1, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        printf("rank %d on %s received final token=%d\n", rank, hostname, token);
    } else {
        MPI_Recv(&token, 1, MPI_INT, rank - 1, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        token += rank;
        printf("rank %d on %s forwarded token=%d\n", rank, hostname, token);
        MPI_Send(&token, 1, MPI_INT, (rank + 1) % size, 0, MPI_COMM_WORLD);
    }

    MPI_Finalize();
    return 0;
}

