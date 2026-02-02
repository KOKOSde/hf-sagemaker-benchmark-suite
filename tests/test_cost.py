from benchmark.cost_calculator import monthly_cost


def test_monthly_cost_default_hours():
    assert monthly_cost(1.0) == 730.0


def test_monthly_cost_custom_hours():
    assert monthly_cost(2.0, 10.0) == 20.0

