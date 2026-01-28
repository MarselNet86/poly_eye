import json
import datetime
import io
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as ticker
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

# CONFIG
STYLES = {
    ("Buy", "Up"):   ("#008f00", "x", "Buy YES"),
    ("Sell", "Up"):  ("#00c800", "o", "Sell YES"),
    ("Buy", "Down"): ("#d000d0", "x", "Buy NO"),
    ("Sell", "Down"):("#d40000", "o", "Sell NO")
}

SEARCH_URL = "https://gamma-api.polymarket.com/public-search"
TRADES_URL = "https://data-api.polymarket.com/trades"
PRICE_RESOLUTION_THRESHOLD = 0.5


def index(request):
    """Главная страница"""
    return render(request, 'analyzer/index.html')


@require_http_methods(["GET"])
def search_market(request):
    """Поиск рынков через API"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'error': 'Query is required'}, status=400)
    
    try:
        resp = requests.get(SEARCH_URL, params={"q": query}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        return JsonResponse({'error': f'API Error: {str(exc)}'}, status=500)
    
    events = data.get("events", []) if isinstance(data, dict) else []
    results = []
    
    for event in events:
        markets = event.get("markets") or []
        for market in markets:
            results.append({
                'event_title': event.get('title', 'Unknown Event'),
                'market_title': market.get('question') or market.get('title', 'Unknown Market'),
                'condition_id': market.get('conditionId', '')
            })
    
    return render(request, 'analyzer/partials/market_results.html', {'results': results})


@require_http_methods(["POST"])
def fetch_trades(request):
    """Загрузка сделок через API"""
    condition_id = request.POST.get('condition_id', '').strip()
    user_address = request.POST.get('user_address', '').strip()
    
    if not condition_id or not user_address:
        return JsonResponse({'error': 'Condition ID and User Address are required'}, status=400)
    
    all_trades = []
    offset = 0
    page_limit = 500
    
    try:
        while True:
            params = {
                "limit": page_limit,
                "offset": offset,
                "takerOnly": "false",
                "market": condition_id,
                "user": user_address,
            }
            
            resp = requests.get(TRADES_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            if isinstance(data, dict):
                batch = data.get("trades", [])
            elif isinstance(data, list):
                batch = data
            else:
                batch = []
            
            all_trades.extend(batch)
            
            if len(batch) < page_limit:
                break
            offset += page_limit
            
    except requests.RequestException as exc:
        return JsonResponse({'error': f'Error fetching trades: {str(exc)}'}, status=500)
    
    if not all_trades:
        return JsonResponse({'error': 'No trades found for this user/market'}, status=404)
    
    # Сохраняем в сессию
    request.session['raw_trades'] = all_trades
    request.session['market_title'] = all_trades[0].get('title', 'Unknown Market')
    request.session['condition_id'] = condition_id
    
    # Автоматически определяем resolved_side
    inferred, _ = infer_resolved_side_from_trades(all_trades)
    if inferred:
        request.session['resolved_side'] = inferred

    return render(request, 'analyzer/partials/trades_loaded.html', {
        'trade_count': len(all_trades),
        'market_title': request.session['market_title']
    })


@csrf_exempt
@require_http_methods(["POST"])
def upload_trades(request):
    """Загрузка сделок из JSON файла"""
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    file = request.FILES['file']
    
    try:
        content = file.read().decode('utf-8')
        raw_data = json.loads(content)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON file'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error reading file: {str(e)}'}, status=500)
    
    if not raw_data or not isinstance(raw_data, list):
        return JsonResponse({'error': 'File must contain a list of trades'}, status=400)
    
    # Сохраняем в сессию
    request.session['raw_trades'] = raw_data
    request.session['market_title'] = raw_data[0].get('title', 'Unknown Market')
    request.session['condition_id'] = raw_data[0].get('conditionId', '')
    
    # Автоматически определяем resolved_side
    inferred, _ = infer_resolved_side_from_trades(raw_data)
    if inferred:
        request.session['resolved_side'] = inferred

    return render(request, 'analyzer/partials/trades_loaded.html', {
        'trade_count': len(raw_data),
        'market_title': request.session['market_title']
    })


@require_http_methods(["POST"])
def set_resolved_side(request):
    """Установка стороны разрешения"""
    resolved_side = request.POST.get('resolved_side', '').strip().upper()
    
    if resolved_side == 'AUTO':
        # Автоматический вывод
        raw_trades = request.session.get('raw_trades', [])
        if not raw_trades:
            return JsonResponse({'error': 'No trades data found'}, status=400)
        
        inferred, latest = infer_resolved_side_from_trades(raw_trades)
        if not inferred:
            return JsonResponse({'error': 'Could not infer resolved side automatically'}, status=400)
        
        request.session['resolved_side'] = inferred
        price = float(latest.get("price", 0))
        outcome = latest.get("outcome", "")
        
        return render(request, 'analyzer/partials/resolved_set.html', {
            'resolved_side': inferred,
            'auto_inferred': True,
            'price': price,
            'outcome': outcome
        })
    
    elif resolved_side in {'YES', 'NO'}:
        request.session['resolved_side'] = resolved_side
        return render(request, 'analyzer/partials/resolved_set.html', {
            'resolved_side': resolved_side,
            'auto_inferred': False
        })
    
    else:
        return JsonResponse({'error': 'Invalid resolved side. Must be YES, NO, or AUTO'}, status=400)


@require_http_methods(["GET"])
def generate_analysis(request):
    """Генерация анализа и визуализации"""
    raw_trades = request.session.get('raw_trades')
    resolved_side = request.session.get('resolved_side')
    market_title = request.session.get('market_title', 'Unknown Market')
    
    if not raw_trades:
        return JsonResponse({'error': 'No trades data found'}, status=400)
    
    if not resolved_side:
        return JsonResponse({'error': 'Resolved side not set'}, status=400)
    
    # Сортировка по timestamp
    raw_trades.sort(key=lambda x: x.get("timestamp", 0))
    
    # Парсинг сделок
    parsed = parse_trades(raw_trades)
    
    if not parsed:
        return JsonResponse({'error': 'No valid trades found'}, status=400)
    
    # Вычисление метрик
    metrics = calculate_metrics(parsed, resolved_side)
    
    # Сохранение метрик в сессию
    request.session['metrics'] = metrics
    request.session['parsed_trades'] = parsed
    
    # Генерация графика
    chart_path = generate_chart(parsed, metrics, market_title, resolved_side)
    request.session['chart_path'] = chart_path
    
    # Генерация текстового отчета
    report_content = generate_text_report(market_title, resolved_side, parsed, metrics)
    request.session['report_content'] = report_content
    
    return render(request, 'analyzer/partials/analysis_complete.html', {
        'metrics': metrics,
        'market_title': market_title,
        'resolved_side': resolved_side
    })


@require_http_methods(["GET"])
def view_chart(request):
    """Отображение графика"""
    chart_path = request.session.get('chart_path')
    
    if not chart_path:
        return HttpResponse('Chart not found', status=404)
    
    try:
        return FileResponse(open(chart_path, 'rb'), content_type='image/png')
    except FileNotFoundError:
        return HttpResponse('Chart file not found', status=404)


@require_http_methods(["GET"])
def download_report(request):
    """Скачивание текстового отчета"""
    report_content = request.session.get('report_content')
    
    if not report_content:
        return HttpResponse('Report not found', status=404)
    
    response = HttpResponse(report_content, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="polymarket_report.txt"'
    return response


# HELPER FUNCTIONS

def infer_resolved_side_from_trades(trades, threshold=PRICE_RESOLUTION_THRESHOLD):
    """Вывод resolved side из последней сделки"""
    if not trades:
        return None, None
    
    latest = max(trades, key=lambda t: t.get("timestamp", 0))
    price = float(latest.get("price", 0))
    outcome = latest.get("outcome", "").lower()
    
    if outcome not in {"up", "down"}:
        return None, latest
    
    if price >= threshold:
        inferred = "YES" if outcome == "up" else "NO"
    else:
        inferred = "NO" if outcome == "up" else "YES"
    
    return inferred, latest


def parse_trades(raw_data):
    """Парсинг сырых данных сделок"""
    parsed = []
    
    for item in raw_data:
        entry = {}
        raw_side = item.get("side", "BUY").upper()
        entry["type"] = "Buy" if raw_side == "BUY" else "Sell"
        entry["market"] = item.get("title", "")
        entry["side"] = item.get("outcome", "Up")
        entry["price"] = float(item.get("price", 0)) * 100.0  # Convert to cents
        entry["shares"] = float(item.get("size", 0))
        entry["cost"] = float(item.get("price", 0)) * entry["shares"]
        entry["timestamp"] = int(item.get("timestamp", 0))
        parsed.append(entry)
    
    return parsed


def calculate_metrics(parsed, resolved_side):
    """Вычисление всех метрик"""
    prices = [e["price"] for e in parsed]
    
    # Exposure curves
    yes_curve = []
    no_curve = []
    net_curve = []
    yes_sh_curve = []
    no_sh_curve = []
    net_sh_curve = []
    
    yes_exp = no_exp = 0
    yes_sh_exp = no_sh_exp = 0
    
    for e in parsed:
        # Dollar exposure
        if e["side"] == "Up":
            yes_exp += e["cost"] if e["type"] == "Buy" else -e["cost"]
        else:
            no_exp += e["cost"] if e["type"] == "Buy" else -e["cost"]
        
        # Shares exposure
        if e["side"] == "Up":
            yes_sh_exp += e["shares"] if e["type"] == "Buy" else -e["shares"]
        else:
            no_sh_exp += e["shares"] if e["type"] == "Buy" else -e["shares"]
        
        yes_curve.append(yes_exp)
        no_curve.append(no_exp)
        net_curve.append(yes_exp + no_exp)
        yes_sh_curve.append(yes_sh_exp)
        no_sh_curve.append(no_sh_exp)
        net_sh_curve.append(yes_sh_exp + no_sh_exp)
    
    # Final PNL
    remaining_yes = yes_sh_curve[-1] if yes_sh_curve else 0
    remaining_no = no_sh_curve[-1] if no_sh_curve else 0
    total_spent = net_curve[-1] if net_curve else 0
    
    # YES Outcome
    final_value_yes = remaining_yes * 1.0
    pnl_yes = final_value_yes - total_spent
    
    # NO Outcome
    final_value_no = remaining_no * 1.0
    pnl_no = final_value_no - total_spent
    
    # Current (Mark-to-Market) PnL
    # Find latest price for YES (Up) and NO (Down)
    last_up_price = 0
    last_down_price = 0
    for e in reversed(parsed):
        if not last_up_price and e["side"] == "Up":
            last_up_price = e["price"]
        if not last_down_price and e["side"] == "Down":
            last_down_price = e["price"]
        if last_up_price and last_down_price:
            break
            
    # If one side is missing, infer it (YES price + NO price = 100 cents)
    if last_up_price and not last_down_price:
        last_down_price = 100.0 - last_up_price
    elif last_down_price and not last_up_price:
        last_up_price = 100.0 - last_down_price
        
    current_value = (remaining_yes * (last_up_price/100.0)) + (remaining_no * (last_down_price/100.0))
    current_pnl = current_value - total_spent
    
    # Buy/Sell totals
    yes_buy_sh = yes_buy_cost = 0
    yes_sell_sh = yes_sell_cost = 0
    no_buy_sh = no_buy_cost = 0
    no_sell_sh = no_sell_cost = 0
    
    raw_vol_yes = []
    raw_vol_no = []
    raw_cost_yes = []
    raw_cost_no = []
    
    for e in parsed:
        is_yes = (e["side"] == "Up")
        is_buy = (e["type"] == "Buy")
        
        if is_buy:
            if is_yes:
                yes_buy_sh += e["shares"]
                yes_buy_cost += e["cost"]
                raw_vol_yes.append(e["shares"])
                raw_vol_no.append(0)
                raw_cost_yes.append(e["cost"])
                raw_cost_no.append(0)
            else:
                no_buy_sh += e["shares"]
                no_buy_cost += e["cost"]
                raw_vol_yes.append(0)
                raw_vol_no.append(e["shares"])
                raw_cost_yes.append(0)
                raw_cost_no.append(e["cost"])
        else:
            raw_vol_yes.append(0)
            raw_vol_no.append(0)
            raw_cost_yes.append(0)
            raw_cost_no.append(0)
            if is_yes:
                yes_sell_sh += e["shares"]
                yes_sell_cost += e["cost"]
            else:
                no_sell_sh += e["shares"]
                no_sell_cost += e["cost"]
    
    cum_yes = np.cumsum(raw_vol_yes)
    cum_no = np.cumsum(raw_vol_no)
    cum_yes_cost = np.cumsum(raw_cost_yes)
    cum_no_cost = np.cumsum(raw_cost_no)
    
    cum_yes_total = float(cum_yes[-1]) if len(cum_yes) > 0 else 0
    cum_no_total = float(cum_no[-1]) if len(cum_no) > 0 else 0
    cum_yes_cost_total = float(cum_yes_cost[-1]) if len(cum_yes_cost) > 0 else 0
    cum_no_cost_total = float(cum_no_cost[-1]) if len(cum_no_cost) > 0 else 0
    
    # Peaks
    if len(yes_curve) > 0:
        yes_peak_idx = int(np.argmax(yes_curve))
        no_peak_idx = int(np.argmax(no_curve))
        yes_sh_peak_idx = int(np.argmax(yes_sh_curve))
        no_sh_peak_idx = int(np.argmax(no_sh_curve))
        
        yes_peak_val = yes_curve[yes_peak_idx]
        no_peak_val = no_curve[no_peak_idx]
        yes_sh_peak_val = yes_sh_curve[yes_sh_peak_idx]
        no_sh_peak_val = no_sh_curve[no_sh_peak_idx]
    else:
        yes_peak_idx = no_peak_idx = 0
        yes_sh_peak_idx = no_sh_peak_idx = 0
        yes_peak_val = no_peak_val = 0
        yes_sh_peak_val = no_sh_peak_val = 0
    
    return {
        'trade_count': len(parsed),
        'remaining_yes': remaining_yes,
        'remaining_no': remaining_no,
        'final_value_yes': final_value_yes,
        'final_value_no': final_value_no,
        'total_spent': total_spent,
        'current_value': current_value,
        'current_pnl': current_pnl,
        'pnl_yes': pnl_yes,
        'pnl_no': pnl_no,
        'yes_buy_sh': yes_buy_sh,
        'yes_buy_cost': yes_buy_cost,
        'yes_sell_sh': yes_sell_sh,
        'yes_sell_cost': yes_sell_cost,
        'no_buy_sh': no_buy_sh,
        'no_buy_cost': no_buy_cost,
        'no_sell_sh': no_sell_sh,
        'no_sell_cost': no_sell_cost,
        'cum_yes_total': cum_yes_total,
        'cum_no_total': cum_no_total,
        'cum_yes_cost_total': cum_yes_cost_total,
        'cum_no_cost_total': cum_no_cost_total,
        'yes_peak_idx': yes_peak_idx,
        'no_peak_idx': no_peak_idx,
        'yes_sh_peak_idx': yes_sh_peak_idx,
        'no_sh_peak_idx': no_sh_peak_idx,
        'yes_peak_val': yes_peak_val,
        'no_peak_val': no_peak_val,
        'yes_sh_peak_val': yes_sh_peak_val,
        'no_sh_peak_val': no_sh_peak_val,
        'yes_curve': yes_curve,
        'no_curve': no_curve,
        'net_curve': net_curve,
        'yes_sh_curve': yes_sh_curve,
        'no_sh_curve': no_sh_curve,
        'net_sh_curve': net_sh_curve,
        'prices': prices,
        'cum_yes': cum_yes.tolist(),
        'cum_no': cum_no.tolist(),
        'cum_yes_cost': cum_yes_cost.tolist(),
        'cum_no_cost': cum_no_cost.tolist(),
    }


def generate_chart(parsed, metrics, market_title, resolved_side):
    """Генерация графика"""
    unique_timestamps = sorted(list(set(t['timestamp'] for t in parsed)))
    ts_map = {ts: i for i, ts in enumerate(unique_timestamps)}
    x_indices = [ts_map[e['timestamp']] for e in parsed]
    
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(
        4, 1, figsize=(16, 14.5),
        gridspec_kw={'height_ratios': [3, 1.3, 1.1, 1.1]}
    )
    fig.subplots_adjust(hspace=0.45, bottom=0.2)
    
    # График 1: Scatter plot сделок
    grouped_trades = {}
    for i, e in enumerate(parsed):
        x_idx = ts_map[e['timestamp']]
        if x_idx not in grouped_trades:
            grouped_trades[x_idx] = []
        grouped_trades[x_idx].append(e)
    
    next_up = True
    
    for x_idx in sorted(grouped_trades.keys()):
        group = grouped_trades[x_idx]
        avg_price = sum(t["price"] for t in group) / len(group)
        
        if len(group) == 1:
            e = group[0]
            style_key = (e["type"], e["side"])
            if style_key in STYLES:
                color, marker, label = STYLES[style_key]
            else:
                color, marker, label = ("gray", "o", "Unknown")
            
            ax1.scatter(x_idx, e["price"], color=color, marker=marker,
                        s=60, linewidths=2.5 if marker=="x" else 1.0,
                        alpha=0.9, zorder=5)
            
            direction = 1 if next_up else -1
            next_up = not next_up
            candle_len = 15 * 0.7
            end_y = e["price"] + direction * candle_len
            
            ax1.vlines(x_idx, e["price"], end_y, colors=color, linewidth=1.5, alpha=0.6)
            
            label_text = f"{e['shares']:.2f}sh\n${e['cost']:.2f}"
            
            ax1.annotate(
                label_text,
                xy=(x_idx, end_y),
                xytext=(0, direction * 2),
                textcoords="offset points",
                ha="center", va="bottom" if direction > 0 else "top",
                fontsize=7,
                bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.7, ec="none")
            )
        else:
            count = len(group)
            first_e = group[0]
            same_side = all((t["type"] == first_e["type"] and t["side"] == first_e["side"]) for t in group)
            
            if same_side:
                style_key = (first_e["type"], first_e["side"])
                color, _, _ = STYLES.get(style_key, ("gray", "o", ""))
            else:
                color = "#1f77b4"
            
            ax1.scatter(x_idx, avg_price, color="white", marker="o", s=300, edgecolors=color, linewidth=2, zorder=5)
            ax1.text(x_idx, avg_price, str(count), ha="center", va="center", fontsize=9, fontweight="bold", color=color, zorder=6)
            
            direction = 1 if next_up else -1
            next_up = not next_up
            
            info_lines = []
            for idx, t in enumerate(group):
                if idx < 5:
                    info_lines.append(f"{t['shares']:.2f}sh ${t['cost']:.2f} ({t['side']})")
                else:
                    remaining = len(group) - 5
                    info_lines.append(f"...+ {remaining} more")
                    break
            
            box_text = "\n".join(info_lines)
            raw_len = 25 + (len(info_lines) * 5)
            candle_len = raw_len * 0.7
            end_y = avg_price + direction * candle_len
            
            ax1.vlines(x_idx, avg_price, end_y, colors=color, linewidth=2, alpha=0.6, linestyles="dotted")
            
            ax1.annotate(
                box_text,
                xy=(x_idx, end_y),
                xytext=(0, direction * 2),
                textcoords="offset points",
                ha="center", va="bottom" if direction > 0 else "top",
                fontsize=6,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.85, ec=color)
            )
    
    ax1.set_title(f"Trades for {market_title}")
    ax1.set_ylabel("Price (cents)")
    
    def time_formatter(x, pos):
        idx = int(x)
        if 0 <= idx < len(unique_timestamps):
            ts = unique_timestamps[idx]
            return datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        return ""
    
    ax1.xaxis.set_major_locator(ticker.MaxNLocator(nbins=12))
    ax1.xaxis.set_major_formatter(ticker.FuncFormatter(time_formatter))
    ax1.set_yticks(range(0, 101, 10))
    ax1.grid(axis='y', linestyle='--', alpha=0.3)
    
    # Volume bars
    vol_yes_per_ts = [0.0] * len(unique_timestamps)
    vol_no_per_ts = [0.0] * len(unique_timestamps)
    
    for x_idx, group in grouped_trades.items():
        for t in group:
            if t["type"] == "Buy":
                if t["side"] == "Up":
                    vol_yes_per_ts[x_idx] += t["shares"]
                else:
                    vol_no_per_ts[x_idx] += t["shares"]
    
    x_range = np.arange(len(unique_timestamps))
    vol_ax = ax1.inset_axes([0, 0.0, 1.0, 0.2], sharex=ax1)
    vol_ax.patch.set_alpha(0)
    vol_ax.bar(x_range - 0.35/2, vol_yes_per_ts, width=0.35,
               color="green", alpha=0.18, label="Buy YES volume")
    vol_ax.bar(x_range + 0.35/2, vol_no_per_ts, width=0.35,
               color="red", alpha=0.18, label="Buy NO volume")
    vol_ax.set_yticks([])
    vol_ax.set_xticks([])
    vol_ax.set_xlim(-0.5, len(unique_timestamps) - 0.5)
    
    # График 2: Cumulative Buys
    cum_yes = np.array(metrics['cum_yes'])
    cum_no = np.array(metrics['cum_no'])
    cum_yes_cost = np.array(metrics['cum_yes_cost'])
    cum_no_cost = np.array(metrics['cum_no_cost'])
    
    ax2.plot(x_indices, cum_yes, color="green", alpha=0.3, linewidth=1, label="Cum Buy YES (sh)")
    ax2.fill_between(x_indices, cum_yes, color="green", alpha=0.1)
    ax2.plot(x_indices, cum_no, color="red", alpha=0.3, linewidth=1, label="Cum Buy NO (sh)")
    ax2.fill_between(x_indices, cum_no, color="red", alpha=0.1)
    
    ax2.set_ylabel("Cumulative buy volume (sh)")
    ax2.grid(axis='y', alpha=0.2)
    ax2.set_xticks([])
    ax2.set_title("Cumulative Buys (shares + dollars)")
    
    max_cum = max(cum_yes.max() if len(cum_yes) else 0, cum_no.max() if len(cum_no) else 0)
    ax2.set_ylim(0, max_cum * 1.15 + 1e-6)
    
    ax2_cost = ax2.twinx()
    ax2_cost.plot(x_indices, cum_yes_cost, color="green", linewidth=1.8,
                  linestyle="--", alpha=0.7, label="Cumulative Buy YES ($)")
    ax2_cost.plot(x_indices, cum_no_cost, color="red", linewidth=1.8,
                  linestyle="--", alpha=0.7, label="Cumulative Buy NO ($)")
    ax2_cost.set_ylabel("Cumulative buy cost ($)", color="gray", fontsize=9)
    ax2_cost.tick_params(axis='y', labelsize=8, colors="gray")
    ax2_cost.spines['right'].set_alpha(0.3)
    handles2, labels2 = ax2_cost.get_legend_handles_labels()
    handles1, labels1 = ax2.get_legend_handles_labels()
    ax2.legend(handles1 + handles2, labels1 + labels2, loc="upper left")
    
    cum_stats_text = (
        f"YES: {metrics['cum_yes_total']:.2f} sh / $ {metrics['cum_yes_cost_total']:.2f}\n"
        f"NO:  {metrics['cum_no_total']:.2f} sh / $ {metrics['cum_no_cost_total']:.2f}"
    )
    ax2.text(
        0.01, 0.02, cum_stats_text,
        transform=ax2.transAxes,
        ha="left", va="bottom",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8, ec="gray")
    )
    
    # График 3: Dollar Exposure
    yes_curve = metrics['yes_curve']
    no_curve = metrics['no_curve']
    net_curve = metrics['net_curve']
    
    ax3.grid(alpha=0.3)
    ax3.plot(x_indices, yes_curve, color="green", linewidth=2, label="YES Exposure ($)")
    ax3.plot(x_indices, no_curve, color="red", linewidth=2, label="NO Exposure ($)")
    ax3.plot(x_indices, net_curve, color="blue", linewidth=2, label="NET Exposure ($ total)")
    
    if len(yes_curve) > 0:
        yes_peak = metrics['yes_peak_idx']
        no_peak = metrics['no_peak_idx']
        ax3.annotate("YES peak $", (x_indices[yes_peak], yes_curve[yes_peak]), xytext=(0, -20),
                     textcoords="offset points", ha='center', arrowprops=dict(arrowstyle="->", color="green"), color="green")
        ax3.annotate("NO peak $", (x_indices[no_peak], no_curve[no_peak]), xytext=(0, -20),
                     textcoords="offset points", ha='center', arrowprops=dict(arrowstyle="->", color="red"), color="red")
        
        last_x = x_indices[-1]
        ax3.annotate(f"$ {yes_curve[-1]:.2f}", (last_x, yes_curve[-1]), xytext=(15, 0), textcoords="offset points", color="green")
        ax3.annotate(f"$ {no_curve[-1]:.2f}", (last_x, no_curve[-1]), xytext=(15, 0), textcoords="offset points", color="red")
        ax3.annotate(f"$ {net_curve[-1]:.2f}", (last_x, net_curve[-1]), xytext=(15, 0), textcoords="offset points", color="blue")
    
    ax3.set_title("Dollar Exposure")
    ax3.set_ylabel("Exposure ($)")
    ax3.set_xticks([])
    ax3.legend(loc="upper left")
    
    summary = (
        f"YES (Up)  Buy: {metrics['yes_buy_sh']:.2f} sh ($ {metrics['yes_buy_cost']:.2f}) "
        f" | Sell: {metrics['yes_sell_sh']:.2f} sh ($ {metrics['yes_sell_cost']:.2f})\n"
        f"NO  (Down) Buy: {metrics['no_buy_sh']:.2f} sh ($ {metrics['no_buy_cost']:.2f}) "
        f" | Sell: {metrics['no_sell_sh']:.2f} sh ($ {metrics['no_sell_cost']:.2f})"
    )
    
    pnl_text = (
        f"IF RESOLVED YES:\n"
        f"Final Value: $ {metrics['final_value_yes']:.2f}\n"
        f"PNL: $ {metrics['pnl_yes']:.2f}\n\n"
        f"IF RESOLVED NO:\n"
        f"Final Value: $ {metrics['final_value_no']:.2f}\n"
        f"PNL: $ {metrics['pnl_no']:.2f}\n\n"
        f"Total Spent: $ {metrics['total_spent']:.2f}"
    )
    
    fig.text(0.01, 0.01, summary, ha="left", va="bottom", fontsize=11,
             bbox=dict(facecolor="white", alpha=0.75, edgecolor="black"))
    fig.text(0.99, 0.06, pnl_text, ha="right", va="top", fontsize=12,
             bbox=dict(facecolor="white", alpha=0.75, edgecolor="black"))
    
    # График 4: Shares Exposure
    yes_sh_curve = metrics['yes_sh_curve']
    no_sh_curve = metrics['no_sh_curve']
    net_sh_curve = metrics['net_sh_curve']
    
    ax4.grid(alpha=0.3)
    ax4.plot(x_indices, yes_sh_curve, color="green", linewidth=2, label="YES Exposure (shares)")
    ax4.plot(x_indices, no_sh_curve, color="red", linewidth=2, label="NO Exposure (shares)")
    ax4.plot(x_indices, net_sh_curve, color="blue", linewidth=2, label="NET Exposure (shares)")
    
    if len(yes_sh_curve) > 0:
        yes_sh_peak = metrics['yes_sh_peak_idx']
        no_sh_peak = metrics['no_sh_peak_idx']
        ax4.annotate("YES peak sh", (x_indices[yes_sh_peak], yes_sh_curve[yes_sh_peak]), xytext=(0, -20),
                     textcoords="offset points", ha='center', arrowprops=dict(arrowstyle="->", color="green"), color="green")
        ax4.annotate("NO peak sh", (x_indices[no_sh_peak], no_sh_curve[no_sh_peak]), xytext=(0, -20),
                     textcoords="offset points", ha='center', arrowprops=dict(arrowstyle="->", color="red"), color="red")
        
        ax4.annotate(f"{yes_sh_curve[-1]:.2f} sh", (last_x, yes_sh_curve[-1]), xytext=(15, 0), textcoords="offset points", color="green")
        ax4.annotate(f"{no_sh_curve[-1]:.2f} sh", (last_x, no_sh_curve[-1]), xytext=(15, 0), textcoords="offset points", color="red")
        ax4.annotate(f"{net_sh_curve[-1]:.2f} sh", (last_x, net_sh_curve[-1]), xytext=(15, 0), textcoords="offset points", color="blue")
    
    ax4.set_title("Shares Exposure")
    ax4.set_ylabel("Shares")
    ax4.xaxis.set_major_locator(ticker.MaxNLocator(nbins=12))
    ax4.xaxis.set_major_formatter(ticker.FuncFormatter(time_formatter))
    plt.setp(ax4.get_xticklabels(), rotation=30, ha='right')
    ax4.legend(loc="upper left")
    
    # Sync X limits
    xlim_range = (-0.5, len(unique_timestamps) - 0.5)
    for axis in (ax1, ax2, ax3, ax4):
        axis.set_xlim(*xlim_range)
    
    plt.tight_layout()
    
    # Сохранение
    import tempfile
    import os
    fd, path = tempfile.mkstemp(suffix='.png', prefix='chart_')
    os.close(fd)
    plt.savefig(path, dpi=200, bbox_inches="tight")
    plt.close('all')
    
    return path


def generate_text_report(market_title, resolved_side, parsed, metrics):
    """Генерация текстового отчета"""
    start_time = "N/A"
    end_time = "N/A"
    if parsed:
        start_time = datetime.datetime.fromtimestamp(parsed[0]['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        end_time = datetime.datetime.fromtimestamp(parsed[-1]['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
    
    min_price = min(metrics['prices']) if metrics['prices'] else 0
    max_price = max(metrics['prices']) if metrics['prices'] else 0
    
    yes_curve = metrics['yes_curve']
    no_curve = metrics['no_curve']
    net_curve = metrics['net_curve']
    yes_sh_curve = metrics['yes_sh_curve']
    no_sh_curve = metrics['no_sh_curve']
    net_sh_curve = metrics['net_sh_curve']
    
    final_yes_exp = yes_curve[-1] if yes_curve else 0
    final_yes_sh = yes_sh_curve[-1] if yes_sh_curve else 0
    final_no_exp = no_curve[-1] if no_curve else 0
    final_no_sh = no_sh_curve[-1] if no_sh_curve else 0
    final_net_exp = net_curve[-1] if net_curve else 0
    final_net_sh = net_sh_curve[-1] if net_sh_curve else 0
    
    lines = [
        f"MARKET: {market_title}",
        f"RESOLUTION: {resolved_side}",
        f"TRADES: {metrics['trade_count']}",
        f"TIME RANGE: {start_time} to {end_time}",
        f"PRICE RANGE: {min_price:.2f} - {max_price:.2f}",
        f"CURRENT PNL (MtM): $ {metrics['current_pnl']:.2f}",
        f"CURRENT VALUE:     $ {metrics['current_value']:.2f}",
        "",
        "--- Position at resolution ---",
        f"Remaining YES shares: {metrics['remaining_yes']:.2f}",
        f"Remaining NO shares:  {metrics['remaining_no']:.2f}",
        f"Total spent (net exposure): $ {metrics['total_spent']:.2f}",
        "",
        f"IF RESOLVED YES:",
        f"  Final value: $ {metrics['final_value_yes']:.2f}",
        f"  PnL:         $ {metrics['pnl_yes']:.2f}",
        "",
        f"IF RESOLVED NO:",
        f"  Final value: $ {metrics['final_value_no']:.2f}",
        f"  PnL:         $ {metrics['pnl_no']:.2f}",
        "",
        "--- Buy/Sell totals ---",
        f"YES buys:  {metrics['yes_buy_sh']:.2f} sh / $ {metrics['yes_buy_cost']:.2f}",
        f"YES sells: {metrics['yes_sell_sh']:.2f} sh / $ {metrics['yes_sell_cost']:.2f}",
        f"NO buys:   {metrics['no_buy_sh']:.2f} sh / $ {metrics['no_buy_cost']:.2f}",
        f"NO sells:  {metrics['no_sell_sh']:.2f} sh / $ {metrics['no_sell_cost']:.2f}",
        "",
        "--- Cumulative buys ---",
        f"YES cumulative: {metrics['cum_yes_total']:.2f} sh / $ {metrics['cum_yes_cost_total']:.2f}",
        f"NO cumulative:  {metrics['cum_no_total']:.2f} sh / $ {metrics['cum_no_cost_total']:.2f}",
        "",
        "--- Exposure peaks (trade index: earliest → latest) ---",
        f"YES dollar peak: $ {metrics['yes_peak_val']:.2f} at trade #{metrics['yes_peak_idx'] + 1}",
        f"NO dollar peak:  $ {metrics['no_peak_val']:.2f} at trade #{metrics['no_peak_idx'] + 1}",
        f"YES share peak:  {metrics['yes_sh_peak_val']:.2f} sh at trade #{metrics['yes_sh_peak_idx'] + 1}",
        f"NO share peak:   {metrics['no_sh_peak_val']:.2f} sh at trade #{metrics['no_sh_peak_idx'] + 1}",
        "",
        "--- Final exposure ---",
        f"YES exposure: $ {final_yes_exp:.2f} | {final_yes_sh:.2f} sh",
        f"NO exposure:  $ {final_no_exp:.2f} | {final_no_sh:.2f} sh",
        f"NET exposure: $ {final_net_exp:.2f} | {final_net_sh:.2f} sh",
        "",
        "--- Trades (Sorted by Timestamp) ---",
        "Idx | Time                | Type | Side | Price(c) |   Shares   |    Cost($)",
        "----+---------------------+------+-----+----------+------------+------------"
    ]
    
    for i, t in enumerate(parsed):
        dt_str = datetime.datetime.fromtimestamp(t['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        lines.append(
            f"{i+1:3d} | {dt_str} | {t['type']:<4} | {t['side']:<4} | "
            f"{t['price']:8.2f} | {t['shares']:10.2f} | $ {t['cost']:9.2f}"
        )
    
    return "\n".join(lines)