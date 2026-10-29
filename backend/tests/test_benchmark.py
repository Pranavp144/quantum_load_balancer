
from app.benchmark import run_benchmark


def test_benchmark_compares_all_policies():
    report = run_benchmark(num_jobs=3, seed=42)

    assert set(report["results"]) == {
        "random",
        "greedy",
        "predictive",
    }

    for result in report["results"].values():
        assert result["total_jobs"] == 3
        assert result["total_cost"] >= 0
        assert result["wall_clock_seconds"] > 0


def test_benchmark_saves_json(tmp_path):
    output = tmp_path / "benchmark.json"

    run_benchmark(
        num_jobs=2,
        seed=42,
        output_path=str(output),
    )

    assert output.exists()
    assert '"results"' in output.read_text(encoding="utf-8")
