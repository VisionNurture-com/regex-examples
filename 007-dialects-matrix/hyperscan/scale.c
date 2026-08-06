/*
 * パターン数を増やしたときにスキャン時間がどう変わるかを測る。
 *
 * 一般的な正規表現エンジンは「1 つのパターンを 1 回ずつ」当てる設計なので、
 * パターンが 1000 個あれば 1000 回まわすことになる。
 * Hyperscan 系（ここでは Vectorscan）は全パターンを 1 つのオートマトンにまとめ、
 * 入力を 1 回なめるだけで全部を同時に照合する。
 *
 * ここでは同じ入力に対してパターン数を 1 / 10 / 100 / 1000 と増やし、
 * スキャン時間が比例して増えるかどうかを見る。
 *
 * ビルド:
 *   cc scale.c -o scale -I/opt/homebrew/include -L/opt/homebrew/lib -lhs
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <hs/hs.h>

static int on_match(unsigned int id, unsigned long long from,
                    unsigned long long to, unsigned int flags, void *ctx) {
    (*(unsigned long *)ctx)++;
    return 0;
}

static double now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1e9;
}

static char *build_input(size_t size) {
    char *buf = malloc(size + 1);
    const char *seed = "user login status=ok id=12345 path=/api/v1/items ";
    size_t seed_len = strlen(seed);
    for (size_t i = 0; i < size; i++) buf[i] = seed[i % seed_len];
    buf[size] = '\0';
    return buf;
}

static void run_case(unsigned int count, const char *input, size_t input_len) {
    const char **patterns = malloc(sizeof(char *) * count);
    unsigned int *ids = malloc(sizeof(unsigned int) * count);
    unsigned int *flags = malloc(sizeof(unsigned int) * count);

    for (unsigned int i = 0; i < count; i++) {
        char *p = malloc(64);
        /* 入力に現れない文字列を探させる。
         * 一致してしまうとコールバックの呼び出し費用が測定を支配し、
         * 「パターン数を増やしたときのスキャン費用」を見られなくなる
         * （一致するパターンで測ったところ、件数が 85 万〜205 万件と条件ごとに
         *   桁違いになり比較が成立しなかった）。 */
        snprintf(p, 64, "qqzz%u[0-9]*", i);
        patterns[i] = p;
        ids[i] = i;
        flags[i] = 0;
    }

    hs_database_t *db = NULL;
    hs_compile_error_t *err = NULL;
    double compile_start = now_sec();
    if (hs_compile_multi(patterns, flags, ids, count, HS_MODE_BLOCK, NULL, &db, &err) != HS_SUCCESS) {
        printf("  コンパイル失敗（%u 個）: %s\n", count, err->message);
        return;
    }
    double compile_sec = now_sec() - compile_start;

    hs_scratch_t *scratch = NULL;
    hs_alloc_scratch(db, &scratch);

    unsigned long hits = 0;
    double scan_start = now_sec();
    hs_scan(db, input, input_len, 0, scratch, on_match, &hits);
    double scan_sec = now_sec() - scan_start;

    double mb = input_len / (1024.0 * 1024.0);
    printf("  %5u 個   コンパイル %7.3f s   スキャン %8.3f ms   %7.1f MB/s   一致 %lu 件\n",
           count, compile_sec, scan_sec * 1000, mb / scan_sec, hits);

    hs_free_scratch(scratch);
    hs_free_database(db);
    for (unsigned int i = 0; i < count; i++) free((void *)patterns[i]);
    free(patterns); free(ids); free(flags);
}

int main(void) {
    const size_t INPUT_SIZE = 8 * 1024 * 1024; /* 8 MB */
    char *input = build_input(INPUT_SIZE);

    printf("Vectorscan %s\n", hs_version());
    printf("入力サイズ: %.1f MB\n\n", INPUT_SIZE / (1024.0 * 1024.0));
    printf("パターン数を増やしても、入力をなめる回数は 1 回のままです。\n\n");

    for (unsigned int count = 1; count <= 1000; count *= 10) {
        run_case(count, input, INPUT_SIZE);
    }

    free(input);
    return 0;
}
