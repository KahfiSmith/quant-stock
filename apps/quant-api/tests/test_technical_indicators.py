"""Unit tests for pure technical indicators calculation."""

from app.technical.indicators import atr, bollinger, ema, macd, rsi, sma


def test_sma_calculation():
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    res = sma(values, 3)
    assert res == [None, None, 20.0, 30.0, 40.0]


def test_ema_calculation():
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    res = ema(values, 3)
    assert res[0] is None
    assert res[1] is None
    assert res[2] == 20.0  # Seeded with SMA
    # alpha = 2 / (3 + 1) = 0.5
    # 40 * 0.5 + 20 * 0.5 = 30.0
    assert res[3] == 30.0
    # 50 * 0.5 + 30 * 0.5 = 40.0
    assert res[4] == 40.0


def test_rsi_calculation():
    # 15 closes needed for 14-period RSI
    closes = [44.0 + i for i in range(15)]
    res = rsi(closes, period=14)
    assert len(res) == 15
    assert all(r is None for r in res[:14])
    # Monotonically increasing prices -> RSI should be 100.0
    assert res[14] == 100.0


def test_bollinger_bands():
    closes = [10.0] * 25
    middle, upper, lower = bollinger(closes, period=20, num_std=2)
    assert len(middle) == 25
    assert middle[19] == 10.0
    assert upper[19] == 10.0
    assert lower[19] == 10.0


def test_macd_and_atr_insufficient_data():
    closes = [10.0, 11.0, 12.0]
    line, signal, hist = macd(closes)
    assert all(x is None for x in line)
    assert all(x is None for x in signal)
    assert all(x is None for x in hist)

    highs = [12.0, 13.0, 14.0]
    lows = [9.0, 10.0, 11.0]
    res_atr = atr(highs, lows, closes, period=14)
    assert all(x is None for x in res_atr)
