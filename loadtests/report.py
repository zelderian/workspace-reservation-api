import csv
import statistics
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RAW = Path("loadtests/results/raw")
OUT = Path("docs/report/lab4")

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
CRITICAL = "#d03b3b"
INK, INK_2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def num(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def read_csv(path: Path) -> list[dict]:
    with path.open() as fh:
        return list(csv.DictReader(fh))


def summary_table(name: str, source: Path) -> str:
    rows = read_csv(source / f"{name}_stats.csv")
    lines = [
        "| Ендпоінт | Запитів | Помилок | RPS | Avg, мс | Min, мс | "
        "Max, мс | p50, мс | p95, мс | p99, мс |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        label = "**Усього**" if r["Name"] == "Aggregated" else f"`{r['Name']}`"
        total, fails = int(r["Request Count"]), int(r["Failure Count"])
        rate = fails / total * 100 if total else 0
        lines.append(
            f"| {label} | {total} | {fails} ({rate:.2f}%) | "
            f"{float(r['Requests/s']):.1f} | {float(r['Average Response Time']):.0f} | "
            f"{float(r['Min Response Time']):.0f} | "
            f"{float(r['Max Response Time']):.0f} | {r['50%']} | {r['95%']} | "
            f"{r['99%']} |"
        )
    return "\n".join(lines)


def resources_table(name: str, source: Path, start: float, end: float) -> str:
    rows = [
        r
        for r in read_csv(source / f"{name}_resources.csv")
        if start <= float(r["timestamp"]) <= end
    ]
    labels = {
        "sys_cpu": "CPU машини, %",
        "app_cpu": "CPU API (uvicorn), %",
        "db_cpu": "CPU PostgreSQL, %",
        "app_rss_mb": "RAM API, МБ",
        "db_rss_mb": "RAM PostgreSQL, МБ",
        "sys_mem_mb": "RAM машини (зайнято), МБ",
    }
    lines = ["| Показник | Середнє | Максимум |", "|---|---:|---:|"]
    for key, label in labels.items():
        values = [float(r[key]) for r in rows]
        lines.append(f"| {label} | {statistics.mean(values):.1f} | {max(values):.1f} |")
    return "\n".join(lines)


def style(ax, title: str, ylabel: str) -> None:
    ax.set_facecolor(SURFACE)
    ax.set_title(title, loc="left", fontsize=11, color=INK, pad=6)
    ax.set_ylabel(ylabel, color=INK_2, fontsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.tick_params(colors=INK_2, labelsize=8, length=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)


def plot(name: str, source: Path, out_name: str) -> tuple[float, float]:
    hist = [r for r in read_csv(source / f"{name}_stats_history.csv")]
    hist = [r for r in hist if r["Name"] == "Aggregated" and int(r["User Count"]) > 0]
    t0 = float(hist[0]["Timestamp"])
    t_end = float(hist[-1]["Timestamp"])
    t = [float(r["Timestamp"]) - t0 for r in hist]
    users = [int(r["User Count"]) for r in hist]
    rps = [float(r["Requests/s"]) for r in hist]
    fails = [float(r["Failures/s"]) for r in hist]
    p50 = [num(r["50%"]) for r in hist]
    p95 = [num(r["95%"]) for r in hist]

    res = [
        r
        for r in read_csv(source / f"{name}_resources.csv")
        if t0 <= float(r["timestamp"]) <= t_end
    ]
    rt = [float(r["timestamp"]) - t0 for r in res]

    fig, axes = plt.subplots(4, 1, figsize=(10, 11), sharex=True)
    fig.patch.set_facecolor(SURFACE)
    fig.suptitle(f"Прогін: {out_name}", x=0.01, ha="left", fontsize=13, color=INK)

    ax = axes[0]
    ax.step(t, users, where="post", color=INK_2, linewidth=2)
    style(ax, "Віртуальні користувачі", "VUsers")

    ax = axes[1]
    ax.plot(t, p50, color=BLUE, linewidth=2, label="p50 (медіана)")
    ax.plot(t, p95, color=ORANGE, linewidth=2, label="p95")
    ax.set_yscale("log")
    style(ax, "Час відповіді (логарифмічна шкала)", "мс")
    ax.legend(frameon=False, fontsize=8, loc="upper left")

    ax = axes[2]
    ax.plot(t, rps, color=BLUE, linewidth=2, label="Запитів/с (RPS)")
    ax.plot(t, fails, color=CRITICAL, linewidth=2, label="Помилок/с")
    style(ax, "Пропускна здатність", "запитів/с")
    ax.legend(frameon=False, fontsize=8, loc="upper left")

    ax = axes[3]
    ax.plot(
        rt,
        [float(r["app_cpu"]) for r in res],
        color=BLUE,
        linewidth=2,
        label="API (uvicorn, 2 воркери)",
    )
    ax.plot(
        rt,
        [float(r["db_cpu"]) for r in res],
        color=AQUA,
        linewidth=2,
        label="PostgreSQL",
    )
    ax.plot(
        rt,
        [float(r["sys_cpu"]) for r in res],
        color=INK_2,
        linewidth=1,
        linestyle="--",
        label="Уся машина (з Locust)",
    )
    ax.set_ylim(0, 105)
    style(ax, "Завантаження CPU (100% = усі ядра)", "%")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_xlabel("Час від початку тесту, с", color=INK_2, fontsize=9)

    fig.tight_layout(rect=(0, 0, 1, 0.97))
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{out_name}.png", dpi=110, facecolor=SURFACE)
    plt.close(fig)
    return t0, t_end


def main() -> None:
    runs = sys.argv[1:] or ["baseline", "step"]
    for run in runs:
        source = RAW
        name = run
        if "/" in run:
            sub, name = run.rsplit("/", 1)
            source = RAW / sub
        out_name = run.replace("/", "_")
        t0, t_end = plot(name, source, out_name)
        text = (
            f"### {out_name}\n\n{summary_table(name, source)}\n\n"
            f"Ресурси сервера:\n\n{resources_table(name, source, t0, t_end)}\n"
        )
        (OUT / f"{out_name}_summary.md").write_text(text, encoding="utf-8")
        print(text)


if __name__ == "__main__":
    main()
