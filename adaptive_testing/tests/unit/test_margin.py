def test_margin_positive():
    from src.margin.calculator import calc_margin
    assert calc_margin(1000) == 120.0

def test_margin_zero():
    from src.margin.calculator import calc_margin
    assert calc_margin(0) == 0

def test_margin_negative():
    from src.margin.calculator import calc_margin
    assert calc_margin(-500) == -60.0