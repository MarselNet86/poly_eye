import csv
import io
from datetime import datetime

from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .models import Market, MarketTick


def index(request):
    return render(request, 'market/index.html')


@require_POST
def upload_csv(request):
    files = request.FILES.getlist('files')
    results = []
    total_ticks = 0

    for uploaded_file in files:
        result = process_csv_file(uploaded_file)
        results.append(result)
        if result['success']:
            total_ticks += result['ticks_count']

    return render(request, 'market/partials/upload_result.html', {
        'results': results,
        'total_ticks': total_ticks,
    })


def process_csv_file(uploaded_file):
    """Process a single CSV file and import data to database."""
    filename = uploaded_file.name

    try:
        content = uploaded_file.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        if not rows:
            return {'filename': filename, 'success': False, 'error': 'Empty file'}

        market_slug = rows[0].get('market_slug', '')
        if not market_slug:
            return {'filename': filename, 'success': False, 'error': 'Missing market_slug'}

        market, _ = Market.objects.get_or_create(slug=market_slug)

        ticks = []
        for row in rows:
            tick = parse_row(market, row)
            if tick:
                ticks.append(tick)

        with transaction.atomic():
            MarketTick.objects.bulk_create(ticks, batch_size=5000, ignore_conflicts=True)

        return {
            'filename': filename,
            'success': True,
            'market_slug': market_slug,
            'ticks_count': len(ticks),
        }

    except Exception as e:
        return {'filename': filename, 'success': False, 'error': str(e)}


def parse_row(market, row):
    """Parse a CSV row into MarketTick object."""
    try:
        timestamp_et_str = row.get('timestamp_et', '')
        timestamp_et = datetime.strptime(timestamp_et_str, '%Y-%m-%d %H:%M:%S.%f')

        up_bids = parse_orderbook(row, 'up_bid')
        up_asks = parse_orderbook(row, 'up_ask')
        down_bids = parse_orderbook(row, 'down_bid')
        down_asks = parse_orderbook(row, 'down_ask')

        return MarketTick(
            market=market,
            timestamp_ms=parse_int(row.get('timestamp_ms')),
            timestamp_et=timestamp_et,
            time_till_end=row.get('time_till_end', ''),
            seconds_till_end=parse_int(row.get('seconds_till_end')) or 0,

            oracle_btc_price=parse_float(row.get('oracle_btc_price')),
            binance_btc_price=parse_float(row.get('binance_btc_price')),
            lag=parse_float(row.get('lag')),

            binance_ret1s_x100=parse_float(row.get('binance_ret1s_x100')),
            binance_ret5s_x100=parse_float(row.get('binance_ret5s_x100')),

            binance_volume_1s=parse_float(row.get('binance_volume_1s')),
            binance_volume_5s=parse_float(row.get('binance_volume_5s')),
            binance_volma_30s=parse_float(row.get('binance_volma_30s')),
            binance_volume_spike=parse_float(row.get('binance_volume_spike')),

            binance_atr_5s=parse_float(row.get('binance_atr_5s')),
            binance_atr_30s=parse_float(row.get('binance_atr_30s')),
            binance_rvol_30s=parse_float(row.get('binance_rvol_30s')),

            binance_vwap_30s=parse_float(row.get('binance_vwap_30s')),
            binance_p_vwap_5s=parse_float(row.get('binance_p_vwap_5s')),
            binance_p_vwap_30s=parse_float(row.get('binance_p_vwap_30s')),

            lat_dir_raw_x1000=parse_float(row.get('lat_dir_raw_x1000')),
            lat_dir_norm_x1000=parse_float(row.get('lat_dir_norm_x1000')),

            up_bids=up_bids,
            up_asks=up_asks,
            down_bids=down_bids,
            down_asks=down_asks,

            pm_up_bid_depth5=parse_float(row.get('pm_up_bid_depth5')),
            pm_up_ask_depth5=parse_float(row.get('pm_up_ask_depth5')),
            pm_up_total_depth5=parse_float(row.get('pm_up_total_depth5')),

            pm_down_bid_depth5=parse_float(row.get('pm_down_bid_depth5')),
            pm_down_ask_depth5=parse_float(row.get('pm_down_ask_depth5')),
            pm_down_total_depth5=parse_float(row.get('pm_down_total_depth5')),

            pm_up_spread=parse_float(row.get('pm_up_spread')),
            pm_down_spread=parse_float(row.get('pm_down_spread')),
            pm_up_imbalance=parse_float(row.get('pm_up_imbalance')),
            pm_down_imbalance=parse_float(row.get('pm_down_imbalance')),
            pm_up_microprice=parse_float(row.get('pm_up_microprice')),
            pm_down_microprice=parse_float(row.get('pm_down_microprice')),

            pm_up_bid_slope=parse_float(row.get('pm_up_bid_slope')),
            pm_up_ask_slope=parse_float(row.get('pm_up_ask_slope')),
            pm_down_bid_slope=parse_float(row.get('pm_down_bid_slope')),
            pm_down_ask_slope=parse_float(row.get('pm_down_ask_slope')),

            pm_up_bid_eatflow=parse_float(row.get('pm_up_bid_eatflow')),
            pm_up_ask_eatflow=parse_float(row.get('pm_up_ask_eatflow')),
            pm_down_bid_eatflow=parse_float(row.get('pm_down_bid_eatflow')),
            pm_down_ask_eatflow=parse_float(row.get('pm_down_ask_eatflow')),
        )
    except Exception:
        return None


def parse_orderbook(row, prefix):
    """Parse 5 orderbook levels into list of {price, size}."""
    levels = []
    for i in range(1, 6):
        price = parse_float(row.get(f'{prefix}_{i}_price'))
        size = parse_float(row.get(f'{prefix}_{i}_size'))
        if price is not None and size is not None:
            levels.append({'price': price, 'size': size})
    return levels


def parse_float(value):
    if value is None or value == '':
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_int(value):
    if value is None or value == '':
        return None
    try:
        return int(value)
    except ValueError:
        return None
