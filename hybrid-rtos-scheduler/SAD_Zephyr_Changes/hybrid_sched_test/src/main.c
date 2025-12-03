#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>
#include <zephyr/sys/util.h>   // ARRAY_SIZE, MAX
#include <zephyr/sched_diag.h>
#include <zephyr/random/random.h>

#define MAX_TASKS 20
#define LOG_MAX   512

typedef struct {
    int      id;
    uint32_t period_ms;
    uint32_t wcet_ms;       // simulated compute per job
    uint32_t deadline_ms;   // relative to release
    int      critical;      // 1 = RT-ish, 0 = best-effort
} task_cfg_t;

typedef struct {
    int      task_id, job_id;
    uint32_t release_ms, start_ms, finish_ms, deadline_abs_ms;
    int      met_deadline;  // 1 if finish <= deadline_abs
} job_log_t;

static job_log_t g_logs[LOG_MAX];
static int       g_log_count = 0;
K_MUTEX_DEFINE(log_mutex);

static inline uint32_t now_ms(void) { return k_uptime_get_32(); }

/* Busy-wait loop to simulate CPU work. */
static void busy_ms(uint32_t ms) {
    uint32_t t0 = now_ms();
    while ((now_ms() - t0) < ms) {
        /* burn cycles */
    }
}

static void task_entry(void *p1, void *p2, void *p3) {
    task_cfg_t cfg = *(task_cfg_t *)p1;
    int job = 0;
    uint32_t next_release = now_ms();

    /* run a fixed number of jobs per task for now */
    while (job < 10) {
        /* Periodic release */
	uint32_t jitter = sys_rand32_get() % 10; // up to 10 ms
        //next_release += cfg.period_ms + jitter;
        next_release += cfg.period_ms;
        k_sleep(K_MSEC(jitter));                  // random offset


        /* Sleep until next release time */
        int32_t delay = (int32_t)next_release - (int32_t)now_ms();
        if (delay > 0) {
            k_sleep(K_MSEC(delay));
        }

        uint32_t release_ts  = next_release;
        uint32_t start_ts    = now_ms();

        /* Simulate CPU work (WCET) */
        busy_ms(cfg.wcet_ms);

        uint32_t finish_ts   = now_ms();
        uint32_t deadline_abs = release_ts + cfg.deadline_ms;
        int met = (finish_ts <= deadline_abs) ? 1 : 0;

        /* Append one record to the in-memory log (mutex to avoid races) */
        k_mutex_lock(&log_mutex, K_FOREVER);
        if (g_log_count < LOG_MAX) {
            g_logs[g_log_count++] = (job_log_t){
                .task_id = cfg.id,
                .job_id = job,
                .release_ms = release_ts,
                .start_ms = start_ts,
                .finish_ms = finish_ts,
                .deadline_abs_ms = deadline_abs,
                .met_deadline = met
            };
        }
        k_mutex_unlock(&log_mutex);

        job++;
    }
}

/* Stacks + thread objects */
K_THREAD_STACK_DEFINE(task_stacks[MAX_TASKS], 2048);
static struct k_thread task_threads[MAX_TASKS];

/* Initial workload (tweak freely) */
static task_cfg_t TASKS[] = {
    // id, period, wcet, deadline, critical
    { .id=0, .period_ms=50,  .wcet_ms=8,   .deadline_ms=50,  .critical=1 }, // RT
    { .id=1, .period_ms=60,  .wcet_ms=12,  .deadline_ms=60,  .critical=1 }, // RT
    { .id=2, .period_ms=400, .wcet_ms=250, .deadline_ms=400, .critical=0 }, // long BE
    { .id=3, .period_ms=420, .wcet_ms=260, .deadline_ms=420, .critical=0 }, // long BE
    { .id=4, .period_ms=400, .wcet_ms=250, .deadline_ms=400, .critical=0 }, // long BE
    { .id=5, .period_ms=420, .wcet_ms=260, .deadline_ms=420, .critical=0 }, // long BE
    { .id=6, .period_ms=400, .wcet_ms=250, .deadline_ms=400, .critical=0 }, // long BE
    { .id=7, .period_ms=420, .wcet_ms=260, .deadline_ms=420, .critical=0 }, // long BE
    { .id=6, .period_ms=400, .wcet_ms=250, .deadline_ms=400, .critical=0 }, // long BE
    { .id=7, .period_ms=420, .wcet_ms=260, .deadline_ms=420, .critical=0 }, // long BE
    { .id=8, .period_ms=50,  .wcet_ms=8,   .deadline_ms=50,  .critical=1 }, // RT
    { .id=9, .period_ms=60,  .wcet_ms=12,  .deadline_ms=60,  .critical=1 }, // RT
    { .id=10, .period_ms=50,  .wcet_ms=8,   .deadline_ms=50,  .critical=1 }, // RT
    { .id=11, .period_ms=60,  .wcet_ms=12,  .deadline_ms=6000,  .critical=1 }, // RT
    };

void main(void) {
    printk("*** hybrid_sched_test start ***\n");
    sched_diag_reset();

    int n = ARRAY_SIZE(TASKS);
    for (int i = 0; i < n; i++) {
        int prio = TASKS[i].critical ? 0 : 4;  /* Zephyr: lower (more negative) = higher priority */
        printk("*** Creating Thread ***\n");
        k_tid_t tid = k_thread_create(
            &task_threads[i],
            task_stacks[i], K_THREAD_STACK_SIZEOF(task_stacks[i]),
            task_entry, &TASKS[i], NULL, NULL,
            prio, 0, K_NO_WAIT
        );
        char name[16];
        snprintk(name, sizeof(name), "task_%d", TASKS[i].id);
        k_thread_name_set(tid, name);
	k_sleep(K_MSEC(20));  // stagger thread starts
    }
    printk("here\n");

    /* Allow jobs to finish. Rough upper bound; adjust as needed. */
    k_sleep(K_SECONDS(5));

    /* Emit CSV once to minimize runtime perturbation */
    printk("task_id,job_id,release_ms,start_ms,finish_ms,deadline_ms,met\n");
    k_mutex_lock(&log_mutex, K_FOREVER);
    for (int i = 0; i < g_log_count; i++) {
        job_log_t *r = &g_logs[i];
        printk("%d,%d,%u,%u,%u,%u,%d\n",
               r->task_id, r->job_id,
               r->release_ms, r->start_ms, r->finish_ms,
               r->deadline_abs_ms, r->met_deadline);
    }
    k_mutex_unlock(&log_mutex);

    struct sched_stats ks;
    sched_diag_get(&ks);
    printk("kstats,ctx=%llu,preempt=%llu,readyq_max=%u,readyq_cur=%u\n",
       ks.context_switches, ks.preemptions, ks.readyq_len_max, ks.readyq_len_cur);

    printk("*** hybrid_sched_test done (%d records) ***\n", g_log_count);
}

