from django.db import models


class Market(models.Model):
    """15-минутный рынок бинарных опционов BTC на Polymarket"""
    slug = models.CharField(max_length=100, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('analyzed', 'Analyzed'),
        ('not_analyzed', 'Not Analyzed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_analyzed')
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.slug


class MarketTick(models.Model):
    """Тик данных рынка (~1 запись/секунду)"""
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name='ticks')

    # Время
    timestamp_ms = models.BigIntegerField(db_index=True)
    timestamp_et = models.DateTimeField()
    time_till_end = models.CharField(max_length=10)
    seconds_till_end = models.IntegerField(db_index=True)

    # Цены и лаг (Chainlink / Binance)
    oracle_btc_price = models.FloatField(null=True, blank=True)
    binance_btc_price = models.FloatField(null=True, blank=True)
    lag = models.FloatField(null=True, blank=True)

    # Моментум (Returns)
    binance_ret1s_x100 = models.FloatField(null=True, blank=True)
    binance_ret5s_x100 = models.FloatField(null=True, blank=True)

    # Объёмы
    binance_volume_1s = models.FloatField(null=True, blank=True)
    binance_volume_5s = models.FloatField(null=True, blank=True)
    binance_volma_30s = models.FloatField(null=True, blank=True)
    binance_volume_spike = models.FloatField(null=True, blank=True)

    # Волатильность
    binance_atr_5s = models.FloatField(null=True, blank=True)
    binance_atr_30s = models.FloatField(null=True, blank=True)
    binance_rvol_30s = models.FloatField(null=True, blank=True)

    # VWAP
    binance_vwap_30s = models.FloatField(null=True, blank=True)
    binance_p_vwap_5s = models.FloatField(null=True, blank=True)
    binance_p_vwap_30s = models.FloatField(null=True, blank=True)

    # Latency Direction
    lat_dir_raw_x1000 = models.FloatField(null=True, blank=True)
    lat_dir_norm_x1000 = models.FloatField(null=True, blank=True)

    # Orderbook UP (JSON для 5 уровней)
    up_bids = models.JSONField(default=list)  # [{price, size}, ...]
    up_asks = models.JSONField(default=list)

    # Orderbook DOWN
    down_bids = models.JSONField(default=list)
    down_asks = models.JSONField(default=list)

    # Глубина UP
    pm_up_bid_depth5 = models.FloatField(null=True, blank=True)
    pm_up_ask_depth5 = models.FloatField(null=True, blank=True)
    pm_up_total_depth5 = models.FloatField(null=True, blank=True)

    # Глубина DOWN
    pm_down_bid_depth5 = models.FloatField(null=True, blank=True)
    pm_down_ask_depth5 = models.FloatField(null=True, blank=True)
    pm_down_total_depth5 = models.FloatField(null=True, blank=True)

    # Микроструктура
    pm_up_spread = models.FloatField(null=True, blank=True)
    pm_down_spread = models.FloatField(null=True, blank=True)
    pm_up_imbalance = models.FloatField(null=True, blank=True)
    pm_down_imbalance = models.FloatField(null=True, blank=True)
    pm_up_microprice = models.FloatField(null=True, blank=True)
    pm_down_microprice = models.FloatField(null=True, blank=True)

    # Slope
    pm_up_bid_slope = models.FloatField(null=True, blank=True)
    pm_up_ask_slope = models.FloatField(null=True, blank=True)
    pm_down_bid_slope = models.FloatField(null=True, blank=True)
    pm_down_ask_slope = models.FloatField(null=True, blank=True)

    # Eat-Flow
    pm_up_bid_eatflow = models.FloatField(null=True, blank=True)
    pm_up_ask_eatflow = models.FloatField(null=True, blank=True)
    pm_down_bid_eatflow = models.FloatField(null=True, blank=True)
    pm_down_ask_eatflow = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp_ms']
        indexes = [
            models.Index(fields=['market', 'timestamp_ms']),
            models.Index(fields=['market', 'seconds_till_end']),
        ]

    def __str__(self):
        return f"{self.market.slug} @ {self.seconds_till_end}s"
