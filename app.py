import matplotlib
matplotlib.use('Agg')

from flask import Flask, render_template, request, redirect, url_for, Response, jsonify
import mysql.connector
import matplotlib.pyplot as plt
import io
import base64
import csv
from decimal import Decimal
from datetime import date, datetime, timedelta
import numpy as np
from scrape_farmer_news import get_farmer_news

app = Flask(__name__)

def get_connection(city):
    db_name = "market"
    if city == 'Gondal':
        db_name = "gondalmarket"
    elif city == 'Ahmedabad':
        db_name = "apmc_ahmedabad"
        
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database=db_name,
        charset="utf8mb4",
        collation="utf8mb4_general_ci"
    )

@app.route('/')
def login():
    return render_template("login.html")

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    if username == "atmiya" and password == "123":
        return redirect(url_for('city'))
    else:
        return render_template("login.html", error="Invalid username or password. Please try again.")

@app.route('/city')
def city():
    return render_template("home.html")

@app.route('/api/items')
def get_items():
    city = request.args.get('city', 'Rajkot')
    items = []
    try:
        conn = get_connection(city)
        cursor = conn.cursor()
        if city == 'Rajkot':
            cursor.execute("""
                SELECT DISTINCT 
                    COALESCE(NULLIF(TRIM(jm.jansi_gujarati_name), ''), jm.jansi_english_name),
                    jm.jansi_english_name
                FROM jansi_master jm
                ORDER BY jm.jansi_english_name
            """)
        elif city == 'Gondal':
            cursor.execute("SELECT DISTINCT commodity_name, commodity_name FROM commodities ORDER BY commodity_name")
        elif city == 'Ahmedabad':
            cursor.execute("""
                SELECT c.commodity_name, c.commodity_name
                FROM commodities c
                WHERE c.id > 0 AND EXISTS (
                    SELECT 1 FROM daily_rates d WHERE d.commodity_id = c.id
                )
                ORDER BY c.commodity_name
            """)
        items = cursor.fetchall()
        conn.close()
        return jsonify([{"name": row[0], "val": row[1]} for row in items])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/setup_city', methods=['POST'])
def setup_city():
    city = request.form.get('city', 'Rajkot')
    try:
        conn = get_connection(city)
        cursor = conn.cursor()
        
        if city == 'Rajkot':
            cursor.execute("""
                SELECT DISTINCT 
                    COALESCE(NULLIF(TRIM(jm.jansi_gujarati_name), ''), jm.jansi_english_name),
                    jm.jansi_english_name
                FROM jansi_master jm
                ORDER BY jm.jansi_english_name
            """)
        elif city == 'Gondal':
            cursor.execute("SELECT DISTINCT commodity_name, commodity_name FROM commodities ORDER BY commodity_name")
        elif city == 'Ahmedabad':
            cursor.execute("""
                SELECT c.commodity_name, c.commodity_name
                FROM commodities c
                WHERE c.id > 0 AND EXISTS (
                    SELECT 1 FROM daily_rates d WHERE d.commodity_id = c.id
                )
                ORDER BY c.commodity_name
            """)
            
        items = cursor.fetchall()
        conn.close()
        return render_template("index.html", items=items, selected_city=city)
    except Exception as e:
        return f"<h2>Database Connection Error</h2><p>{e}</p><p>Make sure MySQL (XAMPP) is running and the {city} database exists.</p>"

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        return redirect(url_for('city'))

    city = request.form.get('city', 'Rajkot')
    item = request.form.get('item', '')
    from_date = request.form.get('from_date', '')
    to_date = request.form.get('to_date', '')
    chart_month = request.form.get('chart_month', 'all')
    
    current_year = None
    prev_year = None
    next_year = None

    data = []
    error_msg = None
    conn = None
    cursor = None

    try:
        conn = get_connection(city)
        cursor = conn.cursor()

        if city == 'Rajkot':
            query = """
                SELECT mp.date, mp.lowrate, mp.highrate, mp.arrival
                FROM market_prices mp
                JOIN jansi_master jm ON mp.id = jm.id
                WHERE jm.jansi_english_name=%s
                AND mp.date BETWEEN %s AND %s
                ORDER BY mp.date ASC
            """
            fallback_query = """
                SELECT mp.date, mp.lowrate, mp.highrate, mp.arrival
                FROM market_prices mp
                JOIN jansi_master jm ON mp.id = jm.id
                WHERE jm.jansi_english_name=%s AND mp.date >= %s
                ORDER BY mp.date ASC
            """
        elif city == 'Gondal':
            query = """
                SELECT p.price_date, p.min_price, p.max_price, 0
                FROM prices p JOIN commodities c_tbl ON p.commodity_id = c_tbl.id
                WHERE c_tbl.commodity_name=%s AND p.price_date BETWEEN %s AND %s
                ORDER BY p.price_date ASC
            """
            fallback_query = """
                SELECT p.price_date, p.min_price, p.max_price, 0
                FROM prices p JOIN commodities c_tbl ON p.commodity_id = c_tbl.id
                WHERE c_tbl.commodity_name=%s AND p.price_date >= %s
                ORDER BY p.price_date ASC
            """
        elif city == 'Ahmedabad':
            cursor.execute("""
                SELECT d.date, d.min_rate, d.max_rate, d.arrival
                FROM daily_rates d
                WHERE d.commodity_id = (
                    SELECT MIN(id) FROM commodities
                    WHERE commodity_name=%s AND id > 0
                )
                ORDER BY d.date ASC
            """, (item,))
            data = cursor.fetchall()
            if data:
                from_date = str(data[0][0])
                to_date   = str(data[-1][0])
            else:
                error_msg = f"No data found for {item} in Ahmedabad database."

        if city != 'Ahmedabad':
            cursor.execute(query, (item, str(from_date), str(to_date)))
            data = cursor.fetchall()

        if not data and city != 'Ahmedabad':
            if city == 'Rajkot':
                cursor.execute("""
                    SELECT mp.date, mp.lowrate, mp.highrate, mp.arrival
                    FROM market_prices mp
                    JOIN jansi_master jm ON mp.id = jm.id
                    WHERE jm.jansi_english_name=%s
                    ORDER BY mp.date ASC
                """, (item,))
            elif city == 'Gondal':
                cursor.execute("""
                    SELECT p.price_date, p.min_price, p.max_price, 0
                    FROM prices p JOIN commodities c_tbl ON p.commodity_id = c_tbl.id
                    WHERE c_tbl.commodity_name=%s
                    ORDER BY p.price_date ASC
                """, (item,))
            data = cursor.fetchall()

            if data:
                error_msg = f"No data found between {from_date} and {to_date}. Showing all available records for {item} ({data[0][0]} to {data[-1][0]})."
            else:
                error_msg = "Data not found for this commodity in the database."

    except Exception as e:
        error_msg = f"Database error: {e}"
        data = []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
        
    template_name = "result.html"
    if not data:
        return render_template(template_name, city=city, item=item, error=error_msg,
                               min_price=0, max_price=0, avg_price=0, total_arrival=0,
                               record_count=0, daily_data=[],
                               from_date=from_date, to_date=to_date)
    
    warning = error_msg if 'error_msg' in locals() and data else None


    # Processing results
    dates, date_objects, low, high, arrival = [], [], [], [], []

    for row in data:
        d = row[0]
        if isinstance(d, (date, datetime)):
            dates.append(d.strftime('%Y-%m-%d'))
            date_objects.append(d)
        else:
            dates.append(str(d))
            try: date_objects.append(datetime.strptime(str(d), '%Y-%m-%d').date())
            except: date_objects.append(date.today())

        low.append(float(row[1]) if row[1] is not None else 0)
        high.append(float(row[2]) if row[2] is not None else 0)
        arrival.append(float(row[3]) if row[3] is not None else 0)

    non_zero_low = [l for l in low if l > 0 and not np.isnan(l)]
    min_price = min(non_zero_low) if non_zero_low else 0
    valid_high = [h for h in high if not np.isnan(h)]
    max_price = max(valid_high) if valid_high else 0
    
    valid_pairs = [(l, h) for l, h in zip(low, high) if not np.isnan(l) and not np.isnan(h)]
    avg_price = sum([(l+h)/2 for l, h in valid_pairs]) / len(valid_pairs) if len(valid_pairs) > 0 else 0
        
    valid_arrival = [a for a in arrival if not np.isnan(a)]
    total_arrival = sum(valid_arrival)
    record_count = len(data)

    # Build a dict from actual DB data keyed by date string
    db_data_map = {}
    for i in range(len(dates)):
        lv = low[i] if not np.isnan(low[i]) else None
        hv = high[i] if not np.isnan(high[i]) else None
        av = arrival[i] if not np.isnan(arrival[i]) else 0
        db_data_map[dates[i]] = {
            'min': round(lv, 2) if lv is not None else None,
            'max': round(hv, 2) if hv is not None else None,
            'avg': round((lv + hv) / 2, 2) if (lv is not None and hv is not None) else None,
            'arrival': int(av)
        }

    # Generate ALL days in the selected range and fill missing ones with None
    daily_data = []
    try:
        start_d = datetime.strptime(str(from_date), '%Y-%m-%d').date()
        end_d   = datetime.strptime(str(to_date), '%Y-%m-%d').date()
        
        # If fallback query actually fetched data beyond end_d, extend end_d
        if date_objects and date_objects[-1] > end_d:
            end_d = date_objects[-1]
            to_date = end_d.strftime('%Y-%m-%d') # Update to_date so UI template shows correct range
            
        current = start_d
        while current <= end_d:
            ds = current.strftime('%Y-%m-%d')
            if ds in db_data_map:
                daily_data.append({'date': ds, 'has_data': True, **db_data_map[ds]})
            else:
                daily_data.append({'date': ds, 'has_data': False, 'min': None, 'max': None, 'avg': None, 'arrival': 0})
            current += timedelta(days=1)
    except Exception:
        # Fallback: just use DB data
        for i in range(len(dates)):
            lv = low[i] if not np.isnan(low[i]) else 0
            hv = high[i] if not np.isnan(high[i]) else 0
            av = arrival[i] if not np.isnan(arrival[i]) else 0
            daily_data.append({'date': dates[i], 'has_data': True,
                                'min': round(lv, 2), 'max': round(hv, 2),
                                'avg': round((lv+hv)/2, 2), 'arrival': int(av)})

    if from_date and len(dates) > 0:
        try:
            start_date_obj = datetime.strptime(str(from_date), '%Y-%m-%d').date()
            if start_date_obj < date_objects[0]:
                dates.insert(0, start_date_obj.strftime('%Y-%m-%d'))
                date_objects.insert(0, start_date_obj)
                low.insert(0, np.nan); high.insert(0, np.nan); arrival.insert(0, np.nan)
        except: pass

    # Price Prediction
    predictions = None
    prediction_dates_str, predicted_low, predicted_high = [], [], []

    if len(date_objects) >= 1:
        try:
            last_date, predictions = date_objects[-1], []
            prediction_days = [7, 14, 30]
            valid_x, valid_low, valid_high = [], [], []
            base_date = date_objects[0]
            
            for i in range(len(date_objects)):
                if not np.isnan(low[i]):
                    valid_x.append((date_objects[i] - base_date).days)
                    valid_low.append(low[i]); valid_high.append(high[i])
            
            is_poly = False
            if len(valid_x) >= 2 and len(set(valid_x)) > 1:
                poly_low = np.poly1d(np.polyfit(valid_x, valid_low, 1))
                poly_high = np.poly1d(np.polyfit(valid_x, valid_high, 1))
                coeffs_low, coeffs_high = np.polyfit(valid_x, valid_low, 1), np.polyfit(valid_x, valid_high, 1)
                is_poly = True
            
            for days_ahead in prediction_days:
                future_date = last_date + timedelta(days=days_ahead)
                if is_poly:
                    future_x = (future_date - base_date).days
                    pred_low, pred_high = max(0, round(poly_low(future_x), 2)), max(0, round(poly_high(future_x), 2))
                    if coeffs_low[0] > 0 and coeffs_high[0] > 0:
                        trend, trend_class = "📈 Rising", "rising"
                    elif coeffs_low[0] < 0 and coeffs_high[0] < 0:
                        trend, trend_class = "📉 Falling", "falling"
                    else:
                        trend, trend_class = "➡️ Stable", "stable"
                else:
                    pred_low, pred_high = max(0, round(valid_low[-1], 2)) if valid_low else 0, max(0, round(valid_high[-1], 2)) if valid_high else 0
                    trend, trend_class = "➡️ Stable", "stable"

                pred_avg = round((pred_low + pred_high) / 2, 2)
                predictions.append({'days': days_ahead, 'date': future_date.strftime('%Y-%m-%d'), 'low': pred_low, 'high': pred_high, 'avg': pred_avg, 'trend': trend, 'trend_class': trend_class})
                prediction_dates_str.append(future_date.strftime('%Y-%m-%d'))
                predicted_low.append(pred_low); predicted_high.append(pred_high)
        except Exception as e:
            predictions = None

    available_months_dict = {}
    for d_str in dates:
        m_key = d_str[:7]
        if m_key not in available_months_dict:
            try: available_months_dict[m_key] = datetime.strptime(m_key + '-01', '%Y-%m-%d').strftime('%B %Y')
            except: pass
    available_months = sorted(available_months_dict.items(), key=lambda x: x[0])

    has_arrival_data = False
    season_data = []
    year_data = []

    try:
        plt.switch_backend('Agg')
        plt.close('all')
        if not dates: raise ValueError("No plot data")

        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor('#FAFAFA'); ax.set_facecolor('#FAFAFA')

        from collections import defaultdict
        season_map = {
            '11': 'Winter', '12': 'Winter', '01': 'Winter', '02': 'Winter',
            '03': 'Summer', '04': 'Summer', '05': 'Summer', '06': 'Summer',
            '07': 'Monsoon', '08': 'Monsoon', '09': 'Monsoon', '10': 'Monsoon'
        }

        # --- Season totals (summary cards) ---
        season_totals = defaultdict(lambda: {'count': 0, 'arrival': 0, 'price_sum': 0})
        for d_str, l_val, h_val, a_val in zip(dates, low, high, arrival):
            m_str = d_str[5:7]
            season = season_map.get(m_str, 'Unknown')
            season_totals[season]['count'] += 1
            if not np.isnan(a_val):
                season_totals[season]['arrival'] += a_val
            if not np.isnan(l_val) and not np.isnan(h_val):
                season_totals[season]['price_sum'] += (l_val + h_val) / 2

        m_labels = ['Winter', 'Summer', 'Monsoon']
        for s in m_labels:
            cnt = season_totals[s]['count']
            season_data.append({
                'season': s,
                'arrival': int(season_totals[s]['arrival']),
                'count': cnt,
                'avg_price': round(season_totals[s]['price_sum'] / cnt, 2) if cnt > 0 else 0
            })

        has_arrival_data = sum([s['arrival'] for s in season_data]) > 0

        # --- Year-wise breakdown ---
        year_totals = defaultdict(lambda: {'count': 0, 'arrival': 0, 'price_sum': 0,
                                            'season_counts': defaultdict(int)})
        for d_str, l_val, h_val, a_val in zip(dates, low, high, arrival):
            yr = d_str[:4]
            m_str = d_str[5:7]
            season = season_map.get(m_str, 'Unknown')
            year_totals[yr]['count'] += 1
            year_totals[yr]['season_counts'][season] += 1
            if not np.isnan(a_val):
                year_totals[yr]['arrival'] += a_val
            if not np.isnan(l_val) and not np.isnan(h_val):
                year_totals[yr]['price_sum'] += (l_val + h_val) / 2

        year_data = []
        for yr in sorted(year_totals.keys()):
            yt = year_totals[yr]
            cnt = yt['count']
            best_season = max(yt['season_counts'], key=yt['season_counts'].get) if yt['season_counts'] else '—'
            year_data.append({
                'year': yr,
                'avg_price': round(yt['price_sum'] / cnt, 2) if cnt > 0 else 0,
                'arrival': int(yt['arrival']),
                'days': cnt,
                'best_season': best_season
            })

        if chart_month == 'intersect':
            from collections import defaultdict
            
            all_years = sorted(list(set(d_str[:4] for d_str in dates)))
            current_year = request.form.get('chart_year')
            if not current_year or current_year not in all_years:
                current_year = all_years[-1] if all_years else None
                
            prev_year = None
            next_year = None
            if current_year and current_year in all_years:
                idx = all_years.index(current_year)
                prev_year = all_years[idx-1] if idx > 0 else None
                next_year = all_years[idx+1] if idx < len(all_years)-1 else None
                
            intersect_year = prev_year if prev_year else current_year

            monthly_groups_y1 = defaultdict(list)
            monthly_groups_y2 = defaultdict(list)
            
            for d_str, l_val, h_val in zip(dates, low, high):
                yr = str(d_str)[:4]
                mo = str(d_str)[5:7]
                avg = (float(l_val) + float(h_val)) / 2 if not np.isnan(l_val) and not np.isnan(h_val) else None
                if avg is not None and avg > 0:
                    if yr == current_year:
                        monthly_groups_y1[mo].append(avg)
                    elif yr == str(intersect_year):
                        monthly_groups_y2[mo].append(avg)
                        
            months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
            month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            y1_avgs = []
            y2_avgs = []
            for mo in months:
                y1_avgs.append(sum(monthly_groups_y1[mo])/len(monthly_groups_y1[mo]) if monthly_groups_y1[mo] else 0)
                y2_avgs.append(sum(monthly_groups_y2[mo])/len(monthly_groups_y2[mo]) if monthly_groups_y2[mo] else 0)
            
            x = np.arange(12)
            ax.plot(x, y1_avgs, label=f'{current_year} (Avg)', color='#689F38', linewidth=3, marker='o')
            if str(intersect_year) != str(current_year):
                ax.plot(x, y2_avgs, label=f'{intersect_year} (Avg)', color='#D4A017', linewidth=3, marker='o', linestyle='--')
            
            ax.set_xlabel('Month', color='#8D6E63', labelpad=10)
            ax.set_ylabel('Average Price (₹)', color='#8D6E63', labelpad=10)
            ax.set_title(f'{item} — {city} Year-over-Year Intersection', color='#4E342E', fontsize=14, fontweight='bold', pad=15)
            ax.set_xticks(x)
            ax.set_xticklabels(month_labels)

        elif chart_month == 'all':
            from collections import defaultdict
            
            all_years = sorted(list(set(d_str[:4] for d_str in dates)))
            current_year = request.form.get('chart_year')
            if not current_year or current_year not in all_years:
                current_year = all_years[-1] if all_years else None
                
            prev_year = None
            next_year = None
            if current_year and current_year in all_years:
                idx = all_years.index(current_year)
                prev_year = all_years[idx-1] if idx > 0 else None
                next_year = all_years[idx+1] if idx < len(all_years)-1 else None

            monthly_groups = defaultdict(lambda: {'min': [], 'max': []})
            for d_str, l_val, h_val in zip(dates, low, high):
                if current_year and not str(d_str).startswith(str(current_year)):
                    continue
                month_key = str(d_str)[:7]
                if not np.isnan(l_val) and l_val > 0:
                    monthly_groups[month_key]['min'].append(float(l_val))
                if not np.isnan(h_val) and h_val > 0:
                    monthly_groups[month_key]['max'].append(float(h_val))
                    
            month_keys = sorted(monthly_groups.keys())
            if not month_keys:
                # Fallback to current_year or current month if empty
                month_keys = [f"{current_year}-01" if current_year else "2024-01"]
                monthly_groups[month_keys[0]] = {'min': [], 'max': []}
                    
            month_keys = sorted(monthly_groups.keys())
            month_labels, month_mins, month_maxs = [], [], []
            
            for mk in month_keys:
                dt = datetime.strptime(mk + '-01', '%Y-%m-%d')
                month_labels.append(dt.strftime('%b %Y'))
                mins = monthly_groups[mk]['min']
                maxs = monthly_groups[mk]['max']
                month_mins.append(min(mins) if mins else 0)
                month_maxs.append(max(maxs) if maxs else 0)

            x = np.arange(len(month_keys))
            width = 0.35

            ax.bar(x - width/2, month_maxs, width, label='Max Price (Up Side)', color='#689F38', edgecolor='#689F38', alpha=0.9)
            ax.bar(x + width/2, month_mins, width, label='Min Price (Down Side)', color='#D32F2F', edgecolor='#D32F2F', alpha=0.9)

            ax.set_xlabel('Month', color='#8D6E63', labelpad=10)
            ax.set_ylabel('Price (₹)', color='#8D6E63', labelpad=10)
            title_year = f"({current_year})" if current_year else ""
            ax.set_title(f'{item} — {city} Month-by-Month Trend {title_year}', color='#4E342E', fontsize=14, fontweight='bold', pad=15)
            ax.set_xticks(x)
            ax.set_xticklabels(month_labels, rotation=45, ha='right')
        else:
            m_dates, m_lows, m_highs = [], [], []
            for d_str, l_val, h_val in zip(dates, low, high):
                if d_str.startswith(chart_month):
                    m_dates.append(d_str[-2:])
                    m_lows.append(l_val if not np.isnan(l_val) else 0)
                    m_highs.append(h_val if not np.isnan(h_val) else 0)

            x_pos = list(range(len(m_dates)))
            ax.plot(x_pos, m_highs, label='Max Price (Up Side)', color='#689F38', linewidth=2, marker='o')
            ax.plot(x_pos, m_lows, label='Min Price (Down Side)', color='#D32F2F', linewidth=2, marker='o')
            ax.fill_between(x_pos, m_lows, m_highs, alpha=0.15, color='#D4A017')

            ax.set_xlabel('Day of Month', color='#8D6E63', labelpad=10)
            ax.set_ylabel('Price (₹)', color='#8D6E63', labelpad=10)
            m_name = available_months_dict.get(chart_month, chart_month)
            ax.set_title(f'{item} — {city} Daily Trend ({m_name})', color='#4E342E', fontsize=14, fontweight='bold', pad=15)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(m_dates)

        ax.legend(facecolor='#FFF8E1', edgecolor='#CCCCCC', labelcolor='#4E342E', loc='upper left')
        ax.tick_params(colors='#8D6E63', which='both')
        ax.spines['bottom'].set_color('#CCCCCC')
        ax.spines['left'].set_color('#CCCCCC')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
            
        fig.tight_layout()
        img = io.BytesIO()
        fig.savefig(img, format='png', dpi=100, bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close(fig)
        img.seek(0)
        graph_url = base64.b64encode(img.getvalue()).decode()
    except Exception as e:
        print(f"Chart generation error: {e}")
        import traceback
        traceback.print_exc()
        plt.close('all')
        graph_url = ""

    return render_template(template_name, city=city, item=item, error=warning,
                           min_price=min_price, max_price=max_price, avg_price=round(avg_price, 2),
                           total_arrival=int(total_arrival), record_count=record_count,
                           daily_data=daily_data,
                           from_date=from_date, to_date=to_date, graph_url=graph_url,
                           available_months=available_months, selected_chart_month=chart_month,
                           season_data=season_data, has_arrival_data=has_arrival_data,
                           year_data=year_data,
                           predictions=predictions,
                           current_year=current_year, prev_year=prev_year, next_year=next_year)


@app.route('/chart', methods=['GET', 'POST'])
def chart_view():
    city         = request.args.get('city', request.form.get('city', 'Rajkot'))
    item         = request.args.get('item', request.form.get('item', ''))
    from_date    = request.args.get('from_date', request.form.get('from_date', ''))
    to_date      = request.args.get('to_date', request.form.get('to_date', ''))
    chart_month  = request.args.get('chart_month', request.form.get('chart_month', 'all'))
    chart_year   = request.args.get('chart_year', request.form.get('chart_year', ''))

    if not item:
        return redirect(url_for('city'))

    data, error_msg, conn, cursor = [], None, None, None
    try:
        conn = get_connection(city)
        cursor = conn.cursor()

        if city == 'Rajkot':
            if from_date and to_date:
                cursor.execute("""
                    SELECT mp.date, mp.lowrate, mp.highrate, mp.arrival
                    FROM market_prices mp
                    JOIN jansi_master jm ON mp.id = jm.id
                    WHERE jm.jansi_english_name=%s AND mp.date BETWEEN %s AND %s
                    ORDER BY mp.date ASC
                """, (item, from_date, to_date))
            else:
                cursor.execute("""
                    SELECT mp.date, mp.lowrate, mp.highrate, mp.arrival
                    FROM market_prices mp
                    JOIN jansi_master jm ON mp.id = jm.id
                    WHERE jm.jansi_english_name=%s ORDER BY mp.date ASC
                """, (item,))
        elif city == 'Gondal':
            if from_date and to_date:
                cursor.execute("""
                    SELECT p.price_date, p.min_price, p.max_price, 0
                    FROM prices p JOIN commodities c_tbl ON p.commodity_id = c_tbl.id
                    WHERE c_tbl.commodity_name=%s AND p.price_date BETWEEN %s AND %s
                    ORDER BY p.price_date ASC
                """, (item, from_date, to_date))
            else:
                cursor.execute("""
                    SELECT p.price_date, p.min_price, p.max_price, 0
                    FROM prices p JOIN commodities c_tbl ON p.commodity_id = c_tbl.id
                    WHERE c_tbl.commodity_name=%s ORDER BY p.price_date ASC
                """, (item,))
        elif city == 'Ahmedabad':
            cursor.execute("""
                SELECT d.date, d.min_rate, d.max_rate, d.arrival
                FROM daily_rates d
                WHERE d.commodity_id = (SELECT MIN(id) FROM commodities WHERE commodity_name=%s AND id > 0)
                ORDER BY d.date ASC
            """, (item,))

        data = cursor.fetchall()
        if data:
            if not from_date: from_date = str(data[0][0])
            if not to_date:   to_date   = str(data[-1][0])
        else:
            error_msg = f"No data found for {item} in {city}."
    except Exception as e:
        error_msg = f"Database error: {e}"
        data = []
    finally:
        if cursor: cursor.close()
        if conn:   conn.close()

    if not data:
        return render_template("chart.html", city=city, item=item, error=error_msg,
                               from_date=from_date, to_date=to_date, graph_url="",
                               available_months=[], selected_chart_month=chart_month,
                               current_year=None, prev_year=None, next_year=None)

    # -- Process dates / low / high / arrival --
    dates, date_objects, low, high, arrival = [], [], [], [], []
    for row in data:
        d = row[0]
        if isinstance(d, (date, datetime)):
            dates.append(d.strftime('%Y-%m-%d')); date_objects.append(d)
        else:
            dates.append(str(d))
            try:    date_objects.append(datetime.strptime(str(d), '%Y-%m-%d').date())
            except: date_objects.append(date.today())
        low.append(float(row[1])   if row[1]   is not None else 0)
        high.append(float(row[2])  if row[2]   is not None else 0)
        arrival.append(float(row[3]) if row[3] is not None else 0)

    available_months_dict = {}
    for d_str in dates:
        m_key = d_str[:7]
        if m_key not in available_months_dict:
            try: available_months_dict[m_key] = datetime.strptime(m_key + '-01', '%Y-%m-%d').strftime('%B %Y')
            except: pass
    available_months = sorted(available_months_dict.items(), key=lambda x: x[0])

    # -- Build chart (mirrors /search logic) --
    current_year_val, prev_year_val, next_year_val = None, None, None
    graph_url = ""
    try:
        plt.switch_backend('Agg')
        plt.close('all')
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor('#FAFAFA'); ax.set_facecolor('#FAFAFA')

        all_years = sorted(list(set(d_str[:4] for d_str in dates)))
        current_year_val = chart_year if chart_year in all_years else (all_years[-1] if all_years else None)
        if current_year_val and current_year_val in all_years:
            idx = all_years.index(current_year_val)
            prev_year_val = all_years[idx - 1] if idx > 0 else None
            next_year_val = all_years[idx + 1] if idx < len(all_years) - 1 else None

        if chart_month == 'intersect':
            from collections import defaultdict
            intersect_year = prev_year_val if prev_year_val else current_year_val
            monthly_groups_y1 = defaultdict(list)
            monthly_groups_y2 = defaultdict(list)
            for d_str, l_val, h_val in zip(dates, low, high):
                yr = str(d_str)[:4]; mo = str(d_str)[5:7]
                avg = (float(l_val) + float(h_val)) / 2 if not np.isnan(l_val) and not np.isnan(h_val) else None
                if avg and avg > 0:
                    if yr == current_year_val: monthly_groups_y1[mo].append(avg)
                    elif yr == str(intersect_year): monthly_groups_y2[mo].append(avg)
            months_list  = ['01','02','03','04','05','06','07','08','09','10','11','12']
            month_labels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
            y1 = [sum(monthly_groups_y1[m])/len(monthly_groups_y1[m]) if monthly_groups_y1[m] else 0 for m in months_list]
            y2 = [sum(monthly_groups_y2[m])/len(monthly_groups_y2[m]) if monthly_groups_y2[m] else 0 for m in months_list]
            x = np.arange(12)
            ax.plot(x, y1, label=f'{current_year_val} (Avg)', color='#689F38', linewidth=3, marker='o')
            if str(intersect_year) != str(current_year_val):
                ax.plot(x, y2, label=f'{intersect_year} (Avg)', color='#D4A017', linewidth=3, marker='o', linestyle='--')
            ax.set_xlabel('Month', color='#8D6E63', labelpad=10)
            ax.set_ylabel('Average Price (₹)', color='#8D6E63', labelpad=10)
            ax.set_title(f'{item} — {city} Year-over-Year Intersection', color='#4E342E', fontsize=14, fontweight='bold', pad=15)
            ax.set_xticks(x); ax.set_xticklabels(month_labels)

        elif chart_month == 'all':
            from collections import defaultdict
            monthly_groups = defaultdict(lambda: {'min': [], 'max': []})
            for d_str, l_val, h_val in zip(dates, low, high):
                if current_year_val and not str(d_str).startswith(str(current_year_val)): continue
                mk = str(d_str)[:7]
                if not np.isnan(l_val) and l_val > 0: monthly_groups[mk]['min'].append(float(l_val))
                if not np.isnan(h_val) and h_val > 0: monthly_groups[mk]['max'].append(float(h_val))
            month_keys = sorted(monthly_groups.keys())
            month_labels, month_mins, month_maxs = [], [], []
            for mk in month_keys:
                dt = datetime.strptime(mk + '-01', '%Y-%m-%d')
                month_labels.append(dt.strftime('%b %Y'))
                month_mins.append(min(monthly_groups[mk]['min']) if monthly_groups[mk]['min'] else 0)
                month_maxs.append(max(monthly_groups[mk]['max']) if monthly_groups[mk]['max'] else 0)
            x = np.arange(len(month_keys)); width = 0.35
            ax.bar(x - width/2, month_maxs, width, label='Max Price (Up Side)',   color='#689F38', edgecolor='#689F38', alpha=0.9)
            ax.bar(x + width/2, month_mins, width, label='Min Price (Down Side)', color='#D32F2F', edgecolor='#D32F2F', alpha=0.9)
            ax.set_xlabel('Month', color='#8D6E63', labelpad=10)
            ax.set_ylabel('Price (₹)', color='#8D6E63', labelpad=10)
            ax.set_title(f'{item} — {city} Month-by-Month Trend ({current_year_val})', color='#4E342E', fontsize=14, fontweight='bold', pad=15)
            ax.set_xticks(x); ax.set_xticklabels(month_labels, rotation=45, ha='right')

        else:
            m_dates, m_lows, m_highs = [], [], []
            for d_str, l_val, h_val in zip(dates, low, high):
                if d_str.startswith(chart_month):
                    m_dates.append(d_str[-2:])
                    m_lows.append(l_val  if not np.isnan(l_val)  else 0)
                    m_highs.append(h_val if not np.isnan(h_val) else 0)
            x_pos = list(range(len(m_dates)))
            ax.plot(x_pos, m_highs, label='Max Price (Up Side)',   color='#689F38', linewidth=2, marker='o')
            ax.plot(x_pos, m_lows,  label='Min Price (Down Side)', color='#D32F2F', linewidth=2, marker='o')
            ax.fill_between(x_pos, m_lows, m_highs, alpha=0.15, color='#D4A017')
            ax.set_xlabel('Day of Month', color='#8D6E63', labelpad=10)
            ax.set_ylabel('Price (₹)', color='#8D6E63', labelpad=10)
            m_name = available_months_dict.get(chart_month, chart_month)
            ax.set_title(f'{item} — {city} Daily Trend ({m_name})', color='#4E342E', fontsize=14, fontweight='bold', pad=15)
            ax.set_xticks(x_pos); ax.set_xticklabels(m_dates)

        ax.legend(facecolor='#FFF8E1', edgecolor='#CCCCCC', labelcolor='#4E342E', loc='upper left')
        ax.tick_params(colors='#8D6E63', which='both')
        ax.spines['bottom'].set_color('#CCCCCC'); ax.spines['left'].set_color('#CCCCCC')
        ax.spines['top'].set_visible(False);      ax.spines['right'].set_visible(False)
        fig.tight_layout()
        img = io.BytesIO()
        fig.savefig(img, format='png', dpi=100, bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close(fig); img.seek(0)
        graph_url = base64.b64encode(img.getvalue()).decode()
    except Exception as e:
        print(f"Chart error: {e}")
        plt.close('all')
        graph_url = ""

    return render_template("chart.html",
                           city=city, item=item,
                           from_date=from_date, to_date=to_date,
                           graph_url=graph_url,
                           available_months=available_months,
                           selected_chart_month=chart_month,
                           current_year=current_year_val,
                           prev_year=prev_year_val,
                           next_year=next_year_val)


@app.route('/season')
def season_view():
    city = request.args.get('city', 'Rajkot')
    item = request.args.get('item', '')
    
    if not item:
        return redirect(url_for('city'))

    data, error_msg, conn, cursor = [], None, None, None
    try:
        conn = get_connection(city)
        cursor = conn.cursor()

        if city == 'Rajkot':
            cursor.execute("""
                SELECT mp.date, mp.lowrate, mp.highrate, mp.arrival
                FROM market_prices mp
                JOIN jansi_master jm ON mp.id = jm.id
                WHERE jm.jansi_english_name=%s
                ORDER BY mp.date ASC
            """, (item,))
        elif city == 'Gondal':
            cursor.execute("""
                SELECT p.price_date, p.min_price, p.max_price, 0
                FROM prices p JOIN commodities c_tbl ON p.commodity_id = c_tbl.id
                WHERE c_tbl.commodity_name=%s
                ORDER BY p.price_date ASC
            """, (item,))
        elif city == 'Ahmedabad':
            cursor.execute("""
                SELECT d.date, d.min_rate, d.max_rate, d.arrival
                FROM daily_rates d
                WHERE d.commodity_id = (SELECT MIN(id) FROM commodities WHERE commodity_name=%s AND id > 0)
                ORDER BY d.date ASC
            """, (item,))

        data = cursor.fetchall()
    except Exception as e:
        error_msg = f"Database error: {e}"
        data = []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    if not data:
        return render_template("season.html", city=city, item=item, error=error_msg or "No data found.")

    # Processing dates / prices
    dates, low, high, arrival = [], [], [], []
    for row in data:
        d = row[0]
        dates.append(d.strftime('%Y-%m-%d') if isinstance(d, (date, datetime)) else str(d))
        low.append(float(row[1]) if row[1] is not None else 0)
        high.append(float(row[2]) if row[2] is not None else 0)
        arrival.append(float(row[3]) if row[3] is not None else 0)

    season_map = {
        '11': 'Winter', '12': 'Winter', '01': 'Winter', '02': 'Winter',
        '03': 'Summer', '04': 'Summer', '05': 'Summer', '06': 'Summer',
        '07': 'Monsoon', '08': 'Monsoon', '09': 'Monsoon', '10': 'Monsoon'
    }

    from collections import defaultdict
    season_totals = defaultdict(lambda: {'count': 0, 'arrival': 0, 'price_sum': 0})
    for d_str, l_val, h_val, a_val in zip(dates, low, high, arrival):
        m_str = d_str[5:7]
        season = season_map.get(m_str, 'Unknown')
        season_totals[season]['count'] += 1
        if a_val > 0: season_totals[season]['arrival'] += a_val
        if l_val > 0 and h_val > 0: season_totals[season]['price_sum'] += (l_val + h_val) / 2

    season_data = []
    for s in ['Winter', 'Summer', 'Monsoon']:
        st = season_totals[s]
        season_data.append({
            'season': s,
            'arrival': int(st['arrival']),
            'avg_price': round(st['price_sum'] / st['count'], 2) if st['count'] > 0 else 0
        })

    year_totals = defaultdict(lambda: {'count': 0, 'arrival': 0, 'price_sum': 0, 'season_counts': defaultdict(int)})
    for d_str, l_val, h_val, a_val in zip(dates, low, high, arrival):
        yr = d_str[:4]
        m_str = d_str[5:7]
        season = season_map.get(m_str, 'Unknown')
        year_totals[yr]['count'] += 1
        year_totals[yr]['season_counts'][season] += 1
        if a_val > 0: year_totals[yr]['arrival'] += a_val
        if l_val > 0 and h_val > 0: year_totals[yr]['price_sum'] += (l_val + h_val) / 2

    year_data = []
    for yr in sorted(year_totals.keys(), reverse=True):
        yt = year_totals[yr]
        best_s = max(yt['season_counts'], key=yt['season_counts'].get) if yt['season_counts'] else '—'
        year_data.append({
            'year': yr,
            'avg_price': round(yt['price_sum'] / yt['count'], 2) if yt['count'] > 0 else 0,
            'arrival': int(yt['arrival']),
            'best_season': best_s
        })

    return render_template("season.html", city=city, item=item, season_data=season_data, year_data=year_data)


@app.route('/download_csv', methods=['POST'])
def download_csv():
    city = request.form.get('city', 'Rajkot')
    item = request.form.get('item', '')
    from_date = request.form.get('from_date', '')
    to_date = request.form.get('to_date', '')

    try:
        conn = get_connection(city)
        cursor = conn.cursor()

        if city == 'Rajkot':
            query = "SELECT mp.date, mp.lowrate, mp.highrate, mp.arrival FROM market_prices mp JOIN jansi_master jm ON mp.id = jm.id WHERE jm.jansi_english_name=%s AND mp.date BETWEEN %s AND %s ORDER BY mp.date ASC"
            fallback = "SELECT mp.date, mp.lowrate, mp.highrate, mp.arrival FROM market_prices mp JOIN jansi_master jm ON mp.id = jm.id WHERE jm.jansi_english_name=%s ORDER BY mp.date ASC"
        elif city == 'Gondal':
            query = "SELECT p.price_date, p.min_price, p.max_price, 0 FROM prices p JOIN commodities c_tbl ON p.commodity_id = c_tbl.id WHERE c_tbl.commodity_name=%s AND p.price_date BETWEEN %s AND %s ORDER BY p.price_date ASC"
            fallback = "SELECT p.price_date, p.min_price, p.max_price, 0 FROM prices p JOIN commodities c_tbl ON p.commodity_id = c_tbl.id WHERE c_tbl.commodity_name=%s ORDER BY p.price_date ASC"

        if city == 'Ahmedabad':
            # Always return all data (no date filter) due to data gap in 2021-2025
            cursor.execute("""SELECT d.date, d.min_rate, d.max_rate, d.arrival FROM daily_rates d WHERE d.commodity_id = (SELECT MIN(id) FROM commodities WHERE commodity_name=%s AND id > 0) ORDER BY d.date ASC""", (item,))
            data = cursor.fetchall()
        else:
            cursor.execute(query, (item, str(from_date), str(to_date)))
            data = cursor.fetchall()
            if not data:
                cursor.execute(fallback, (item,))
                data = cursor.fetchall()
        conn.close()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Date', 'Low Price', 'High Price', 'Arrival'])
        for row in data: writer.writerow(row)
        output.seek(0)
        
        return Response(output.getvalue(), mimetype="text/csv", headers={"Content-disposition": f"attachment; filename={city}_{item}_prices.csv"})
    except Exception as e:
        return f"Error gathering CSV data: {e}"

@app.route('/news')
def news_view():
    news_items = get_farmer_news()
    return render_template("news.html", news=news_items)

@app.route('/history')
def history_view():
    return render_template("history.html")

if __name__ == "__main__":
    app.run(debug=True, port=5001)
