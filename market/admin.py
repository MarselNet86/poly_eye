from django.contrib import admin
from .models import Market, MarketTick


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ['slug', 'created_at', 'tick_count']
    search_fields = ['slug']
    readonly_fields = ['created_at']

    def tick_count(self, obj):
        return obj.ticks.count()
    tick_count.short_description = 'Тиков'


@admin.register(MarketTick)
class MarketTickAdmin(admin.ModelAdmin):
    list_display = [
        'market', 'timestamp_et', 'seconds_till_end',
        'oracle_btc_price', 'binance_btc_price', 'lag',
        'binance_ret1s_x100', 'binance_volume_spike',
        'pm_up_spread', 'pm_down_spread',
    ]
    list_filter = ['market', 'seconds_till_end']
    search_fields = ['market__slug']

    fieldsets = (
        ('Время', {
            'fields': ('market', 'timestamp_ms', 'timestamp_et', 'time_till_end', 'seconds_till_end')
        }),
        ('Цены и лаг (Группа 1)', {
            'fields': ('oracle_btc_price', 'binance_btc_price', 'lag')
        }),
        ('Моментум (Группа 2)', {
            'fields': ('binance_ret1s_x100', 'binance_ret5s_x100')
        }),
        ('Объёмы (Группа 3)', {
            'fields': ('binance_volume_1s', 'binance_volume_5s', 'binance_volma_30s', 'binance_volume_spike')
        }),
        ('Волатильность (Группа 4)', {
            'fields': ('binance_atr_5s', 'binance_atr_30s', 'binance_rvol_30s')
        }),
        ('VWAP (Группа 5)', {
            'fields': ('binance_vwap_30s', 'binance_p_vwap_5s', 'binance_p_vwap_30s')
        }),
        ('Latency Direction (Группа 6)', {
            'fields': ('lat_dir_raw_x1000', 'lat_dir_norm_x1000')
        }),
        ('Orderbook UP (Группа 7)', {
            'fields': ('up_bids', 'up_asks'),
            'classes': ('collapse',)
        }),
        ('Orderbook DOWN (Группа 7)', {
            'fields': ('down_bids', 'down_asks'),
            'classes': ('collapse',)
        }),
        ('Глубина и баланс UP (Группа 8)', {
            'fields': ('pm_up_bid_depth5', 'pm_up_ask_depth5', 'pm_up_total_depth5', 'pm_up_imbalance')
        }),
        ('Глубина и баланс DOWN (Группа 8)', {
            'fields': ('pm_down_bid_depth5', 'pm_down_ask_depth5', 'pm_down_total_depth5', 'pm_down_imbalance')
        }),
        ('Микроструктура UP (Группа 9)', {
            'fields': ('pm_up_spread', 'pm_up_microprice', 'pm_up_bid_slope', 'pm_up_ask_slope')
        }),
        ('Микроструктура DOWN (Группа 9)', {
            'fields': ('pm_down_spread', 'pm_down_microprice', 'pm_down_bid_slope', 'pm_down_ask_slope')
        }),
        ('Eat-Flow UP (Группа 10)', {
            'fields': ('pm_up_bid_eatflow', 'pm_up_ask_eatflow')
        }),
        ('Eat-Flow DOWN (Группа 10)', {
            'fields': ('pm_down_bid_eatflow', 'pm_down_ask_eatflow')
        }),
    )
