#include <zephyr/kernel.h>
#include <zephyr/spinlock.h>
#include <zephyr/sched_diag.h>

#if defined(CONFIG_SCHED_DIAG)

static struct sched_stats g_stats;
static struct k_spinlock g_lock;

void sched_diag_reset(void)
{
    k_spinlock_key_t key = k_spin_lock(&g_lock);
    g_stats.context_switches = 0;
    g_stats.preemptions      = 0;
    g_stats.readyq_len_max   = 0;
    g_stats.readyq_len_cur   = 0;
    k_spin_unlock(&g_lock, key);
}

void sched_diag_get(struct sched_stats *out)
{
    if (!out) return;
    k_spinlock_key_t key = k_spin_lock(&g_lock);
    *out = g_stats; /* struct copy */
    k_spin_unlock(&g_lock, key);
}

/* Called at the point a thread becomes ready/runnable */
void sched_diag_on_enqueue(void)
{
    k_spinlock_key_t key = k_spin_lock(&g_lock);
    uint32_t cur = ++g_stats.readyq_len_cur;
    if (cur > g_stats.readyq_len_max) g_stats.readyq_len_max = cur;
    k_spin_unlock(&g_lock, key);
}

/* Called at the point a ready thread leaves the run-queue */
void sched_diag_on_dequeue(void)
{
    k_spinlock_key_t key = k_spin_lock(&g_lock);
    if (g_stats.readyq_len_cur > 0) g_stats.readyq_len_cur--;
    k_spin_unlock(&g_lock, key);
}

/* Called on every context switch decision */
void sched_diag_on_context_switch(const struct k_thread *from,
                                  const struct k_thread *to)
{
    ARG_UNUSED(from);
    ARG_UNUSED(to);
    k_spinlock_key_t key = k_spin_lock(&g_lock);
    g_stats.context_switches++;
    /* Preemption heuristic: 'to' outranks 'from' by priority value. */
    if (from && to) {
        /* Lower base.prio means higher priority in Zephyr */
        if (to->base.prio < from->base.prio) {
            g_stats.preemptions++;
        }
    }
    k_spin_unlock(&g_lock, key);
}

#else /* !CONFIG_SCHED_DIAG */

void sched_diag_reset(void) {}
void sched_diag_get(struct sched_stats *out) { if (out) { out->context_switches=0; out->preemptions=0; out->readyq_len_max=0; out->readyq_len_cur=0; } }
void sched_diag_on_context_switch(const struct k_thread *from, const struct k_thread *to) { ARG_UNUSED(from); ARG_UNUSED(to); }
void sched_diag_on_enqueue(void) {}
void sched_diag_on_dequeue(void) {}

#endif

