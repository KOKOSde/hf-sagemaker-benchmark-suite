from benchmark.common import percentile


def test_percentile_single_value():
    assert percentile([5.0], 50) == 5.0


def test_percentile_known_values():
    xs = [0.0, 10.0, 20.0, 30.0]
    assert percentile(xs, 0) == 0.0
    assert percentile(xs, 100) == 30.0
    # 50th percentile between 10 and 20 -> 15 with linear interpolation
    assert percentile(xs, 50) == 15.0

