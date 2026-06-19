#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define HOSTNAME_LEN 128
#define LINE_LEN 512

static long long min_ll(long long a, long long b) {
    return a < b ? a : b;
}

static void block_range(long long n, int rank, int size, long long *start, long long *count) {
    long long base = n / size;
    long long rem = n % size;
    *count = base + (rank < rem ? 1 : 0);
    *start = rank * base + min_ll(rank, rem);
}

static void ordered_print(MPI_Comm comm, int rank, int size, const char *line) {
    for (int r = 0; r < size; r++) {
        MPI_Barrier(comm);
        if (r == rank) {
            printf("%s\n", line);
            fflush(stdout);
        }
    }
    MPI_Barrier(comm);
}

static int test_rank_placement(int rank, int size, const char *hostname) {
    char *all_hosts = NULL;
    if (rank == 0) {
        all_hosts = calloc((size_t)size, HOSTNAME_LEN);
        if (all_hosts == NULL) {
            fprintf(stderr, "calloc failed\n");
            MPI_Abort(MPI_COMM_WORLD, 10);
        }
    }

    MPI_Gather(hostname, HOSTNAME_LEN, MPI_CHAR, all_hosts, HOSTNAME_LEN, MPI_CHAR, 0, MPI_COMM_WORLD);

    int pass = 1;
    if (rank == 0) {
        int unique = 0;
        printf("\n[TEST rank_placement]\n");
        for (int i = 0; i < size; i++) {
            const char *host_i = all_hosts + i * HOSTNAME_LEN;
            int seen = 0;
            for (int j = 0; j < i; j++) {
                const char *host_j = all_hosts + j * HOSTNAME_LEN;
                if (strncmp(host_i, host_j, HOSTNAME_LEN) == 0) {
                    seen = 1;
                    break;
                }
            }
            if (!seen) {
                unique++;
            }
            printf("rank=%d host=%s\n", i, host_i);
        }
        pass = (size >= 3 && unique >= 3);
        printf("unique_hosts=%d expected_at_least=3 status=%s\n", unique, pass ? "PASS" : "FAIL");
        free(all_hosts);
    }

    MPI_Bcast(&pass, 1, MPI_INT, 0, MPI_COMM_WORLD);
    return pass;
}

static int test_distributed_sum(int rank, int size, const char *hostname, long long n) {
    long long start0 = 0;
    long long count = 0;
    block_range(n, rank, size, &start0, &count);

    long long first = start0 + 1;
    long long last = start0 + count;
    long long local_sum = 0;
    if (count > 0) {
        local_sum = (first + last) * count / 2;
    }

    long long global_sum = 0;
    MPI_Reduce(&local_sum, &global_sum, 1, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        printf("\n[TEST distributed_sum]\n");
    }

    char line[LINE_LEN];
    snprintf(line, sizeof(line),
             "rank=%d host=%s range=[%lld,%lld] local_sum=%lld",
             rank, hostname, count > 0 ? first : 0, count > 0 ? last : -1, local_sum);
    ordered_print(MPI_COMM_WORLD, rank, size, line);

    int pass = 1;
    if (rank == 0) {
        long long expected = n * (n + 1) / 2;
        pass = (global_sum == expected);
        printf("N=%lld expected=%lld mpi_sum=%lld status=%s\n",
               n, expected, global_sum, pass ? "PASS" : "FAIL");
    }
    MPI_Bcast(&pass, 1, MPI_INT, 0, MPI_COMM_WORLD);
    return pass;
}

static long long matrix_value(long long row, long long col) {
    return (row + 1) * 10 + (col + 1);
}

static long long vector_value(long long col) {
    return col + 1;
}

static int test_matrix_vector(int rank, int size, const char *hostname, long long rows, long long cols) {
    long long start_row = 0;
    long long row_count = 0;
    block_range(rows, rank, size, &start_row, &row_count);

    long long local_checksum = 0;
    for (long long r = start_row; r < start_row + row_count; r++) {
        long long y = 0;
        for (long long c = 0; c < cols; c++) {
            y += matrix_value(r, c) * vector_value(c);
        }
        local_checksum += y;
    }

    long long checksum = 0;
    MPI_Reduce(&local_checksum, &checksum, 1, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        printf("\n[TEST matrix_vector_checksum]\n");
    }

    char line[LINE_LEN];
    snprintf(line, sizeof(line),
             "rank=%d host=%s rows=[%lld,%lld] local_checksum=%lld",
             rank,
             hostname,
             row_count > 0 ? start_row : 0,
             row_count > 0 ? start_row + row_count - 1 : -1,
             local_checksum);
    ordered_print(MPI_COMM_WORLD, rank, size, line);

    int pass = 1;
    if (rank == 0) {
        long long expected = 0;
        for (long long r = 0; r < rows; r++) {
            for (long long c = 0; c < cols; c++) {
                expected += matrix_value(r, c) * vector_value(c);
            }
        }
        pass = (checksum == expected);
        printf("rows=%lld cols=%lld expected_checksum=%lld mpi_checksum=%lld status=%s\n",
               rows, cols, expected, checksum, pass ? "PASS" : "FAIL");
    }
    MPI_Bcast(&pass, 1, MPI_INT, 0, MPI_COMM_WORLD);
    return pass;
}

static unsigned long long lcg_next(unsigned long long *state) {
    *state = (*state * 6364136223846793005ULL) + 1442695040888963407ULL;
    return *state;
}

static double unit_random(unsigned long long *state) {
    unsigned long long x = lcg_next(state) >> 11;
    return (double)x * (1.0 / 9007199254740992.0);
}

static int test_monte_carlo_pi(int rank, int size, const char *hostname, long long samples_total) {
    long long start = 0;
    long long samples = 0;
    block_range(samples_total, rank, size, &start, &samples);

    unsigned long long state = 0x9e3779b97f4a7c15ULL ^ (unsigned long long)(rank + 1) * 0xbf58476d1ce4e5b9ULL;
    long long inside = 0;
    for (long long i = 0; i < samples; i++) {
        double x = unit_random(&state);
        double y = unit_random(&state);
        if (x * x + y * y <= 1.0) {
            inside++;
        }
    }

    long long total_inside = 0;
    MPI_Reduce(&inside, &total_inside, 1, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        printf("\n[TEST monte_carlo_pi]\n");
    }

    char line[LINE_LEN];
    snprintf(line, sizeof(line),
             "rank=%d host=%s samples=%lld inside=%lld",
             rank, hostname, samples, inside);
    ordered_print(MPI_COMM_WORLD, rank, size, line);

    int pass = 1;
    if (rank == 0) {
        double pi = 4.0 * (double)total_inside / (double)samples_total;
        pass = (pi > 3.10 && pi < 3.18);
        printf("samples=%lld inside=%lld pi_estimate=%.6f accepted_range=[3.10,3.18] status=%s\n",
               samples_total, total_inside, pi, pass ? "PASS" : "FAIL");
    }
    MPI_Bcast(&pass, 1, MPI_INT, 0, MPI_COMM_WORLD);
    return pass;
}

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);

    int rank = 0;
    int size = 0;
    char hostname[HOSTNAME_LEN];
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    int hostname_len = 0;
    MPI_Get_processor_name(hostname, &hostname_len);
    hostname[sizeof(hostname) - 1] = '\0';

    long long sum_n = argc > 1 ? atoll(argv[1]) : 1000000LL;
    long long matrix_rows = argc > 2 ? atoll(argv[2]) : 12LL;
    long long matrix_cols = argc > 3 ? atoll(argv[3]) : 8LL;
    long long pi_samples = argc > 4 ? atoll(argv[4]) : 300000LL;

    if (rank == 0) {
        printf("PARALLEL_UNIT_TESTS_START size=%d\n", size);
        printf("args sum_n=%lld matrix_rows=%lld matrix_cols=%lld pi_samples=%lld\n",
               sum_n, matrix_rows, matrix_cols, pi_samples);
    }

    int pass_rank = test_rank_placement(rank, size, hostname);
    int pass_sum = test_distributed_sum(rank, size, hostname, sum_n);
    int pass_matrix = test_matrix_vector(rank, size, hostname, matrix_rows, matrix_cols);
    int pass_pi = test_monte_carlo_pi(rank, size, hostname, pi_samples);

    int overall = pass_rank && pass_sum && pass_matrix && pass_pi;
    if (rank == 0) {
        printf("\nPARALLEL_UNIT_TESTS_OVERALL=%s\n", overall ? "PASS" : "FAIL");
    }

    MPI_Finalize();
    return overall ? 0 : 1;
}
