#pragma once
#include <zephyr/kernel.h>

#ifdef __cplusplus
extern "C" {
#endif

struct sched_stats {
    uint64_t context_switches;
    uint64_t preemptions;
    uint32_t readyq_len_max;
    uint32_t readyq_len_cur;
};

/* Reset counters to zero */
void sched_diag_reset(void);

/* Copy current counters to *out (thread-safe snapshot) */
void sched_diag_get(struct sched_stats *out);

/* Internal hooks (no-ops when CONFIG_SCHED_DIAG=n). */
void sched_diag_on_context_switch(const struct k_thread *from,
                                  const struct k_thread *to);
void sched_diag_on_enqueue(void);
void sched_diag_on_dequeue(void);

#ifdef __cplusplus
}
#endif

