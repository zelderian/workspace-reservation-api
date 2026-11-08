import argparse
import csv
import signal
import time

import psutil


def find_processes(pattern: str) -> list[psutil.Process]:
    result = []
    for proc in psutil.process_iter(["cmdline", "name"]):
        cmd = " ".join(proc.info["cmdline"] or [])
        if pattern in cmd and "monitor.py" not in cmd and "locust" not in cmd:
            result.append(proc)
            result.extend(proc.children(recursive=True))
    return list({p.pid: p for p in result}.values())


_db_cache: dict[int, psutil.Process] = {}


def postgres_processes() -> list[psutil.Process]:
    alive = set()
    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] == "postgres":
            alive.add(proc.pid)
            _db_cache.setdefault(proc.pid, proc)
    for pid in list(_db_cache):
        if pid not in alive:
            del _db_cache[pid]
    return list(_db_cache.values())


def sample(procs: list[psutil.Process]) -> tuple[float, float]:
    cpu, rss = 0.0, 0.0
    for proc in procs:
        try:
            cpu += proc.cpu_percent(None)
            rss += proc.memory_info().rss
        except psutil.Error:
            continue
    return cpu / psutil.cpu_count(), rss / 2**20


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pattern", default="uvicorn app.main:app")
    parser.add_argument("--out", required=True)
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, signal.default_int_handler)

    app_procs = find_processes(args.pattern)
    db_procs = postgres_processes()
    psutil.cpu_percent(None)
    sample(app_procs)
    sample(db_procs)

    with open(args.out, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "timestamp",
                "sys_cpu",
                "sys_mem_mb",
                "app_cpu",
                "app_rss_mb",
                "db_cpu",
                "db_rss_mb",
            ]
        )
        try:
            while True:
                time.sleep(args.interval)
                db_procs = postgres_processes()
                app_cpu, app_rss = sample(app_procs)
                db_cpu, db_rss = sample(db_procs)
                mem = psutil.virtual_memory()
                writer.writerow(
                    [
                        round(time.time(), 1),
                        psutil.cpu_percent(None),
                        round((mem.total - mem.available) / 2**20, 1),
                        round(app_cpu, 1),
                        round(app_rss, 1),
                        round(db_cpu, 1),
                        round(db_rss, 1),
                    ]
                )
                fh.flush()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
