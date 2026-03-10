# dashboard/app.py
# ─────────────────────────────────────────────
# Lightweight Flask dashboard to view live stock
# alerts and history in a browser
# Run: python dashboard/app.py
# ─────────────────────────────────────────────

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, render_template_string, jsonify
from data.stock_history import get_all_history
from config.config import PRODUCTS, ENABLED_RETAILERS

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🃏 TCG Fair-Access Monitor</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', sans-serif; background: #0d1117; color: #c9d1d9; min-height: 100vh; }
  header { background: linear-gradient(135deg, #cc0000, #0071ce 50%, #1d6f2b); padding: 24px 32px; }
  header h1 { font-size: 1.8rem; color: #fff; }
  header p  { color: rgba(255,255,255,0.8); margin-top: 4px; }
  .stats { display: flex; gap: 16px; padding: 24px 32px; flex-wrap: wrap; }
  .stat-card { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 16px 24px; min-width: 160px; }
  .stat-card .num { font-size: 2rem; font-weight: bold; color: #58a6ff; }
  .stat-card .label { font-size: 0.85rem; color: #8b949e; margin-top: 4px; }
  .section { padding: 0 32px 32px; }
  h2 { color: #e6edf3; margin-bottom: 16px; font-size: 1.1rem; border-bottom: 1px solid #30363d; padding-bottom: 8px; }
  table { width: 100%; border-collapse: collapse; background: #161b22; border-radius: 10px; overflow: hidden; }
  th { background: #21262d; padding: 12px 16px; text-align: left; font-size: 0.8rem; color: #8b949e; text-transform: uppercase; }
  td { padding: 12px 16px; border-top: 1px solid #21262d; font-size: 0.9rem; }
  tr:hover td { background: #1c2128; }
  .badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
  .badge-target   { background: #cc000033; color: #ff6b6b; border: 1px solid #cc000066; }
  .badge-walmart  { background: #0071ce33; color: #58a6ff; border: 1px solid #0071ce66; }
  .badge-gamestop { background: #e3193733; color: #ff8b94; border: 1px solid #e3193766; }
  .badge-bestbuy  { background: #ffe00033; color: #f0c040; border: 1px solid #ffe00066; }
  .badge-bn       { background: #1d6f2b33; color: #56d364; border: 1px solid #1d6f2b66; }
  a { color: #58a6ff; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .empty { text-align: center; padding: 48px; color: #8b949e; }
  .refresh { float: right; font-size: 0.8rem; color: #8b949e; }
  .products-grid { display: flex; flex-wrap: wrap; gap: 12px; }
  .product-chip { background: #21262d; border: 1px solid #30363d; border-radius: 8px; padding: 8px 14px; font-size: 0.85rem; }
</style>
</head>
<body>
<header>
  <h1>🃏 TCG Fair-Access Stock Monitor</h1>
  <p>Helping real fans find cards at retail price — not scalpers.</p>
</header>

<div class="stats">
  <div class="stat-card">
    <div class="num">{{ products }}</div>
    <div class="label">Products tracked</div>
  </div>
  <div class="stat-card">
    <div class="num">{{ retailers }}</div>
    <div class="label">Retailers monitored</div>
  </div>
  <div class="stat-card">
    <div class="num">{{ total_alerts }}</div>
    <div class="label">Total alerts fired</div>
  </div>
</div>

<div class="section">
  <h2>📋 Products Being Monitored</h2>
  <div class="products-grid">
    {% for p in product_list %}
    <div class="product-chip">{{ p }}</div>
    {% endfor %}
  </div>
</div>

<div class="section">
  <h2>📡 Recent Stock Alerts <span class="refresh" id="timer"></span></h2>
  {% if history %}
  <table>
    <thead>
      <tr>
        <th>Product</th>
        <th>Retailer</th>
        <th>Location</th>
        <th>Last Seen</th>
      </tr>
    </thead>
    <tbody>
      {% for row in history %}
      <tr>
        <td>{{ row.product }}</td>
        <td>
          {% set r = row.retailer | lower %}
          {% if 'target' in r %}
            <span class="badge badge-target">Target</span>
          {% elif 'walmart' in r %}
            <span class="badge badge-walmart">Walmart</span>
          {% elif 'gamestop' in r %}
            <span class="badge badge-gamestop">GameStop</span>
          {% elif 'best buy' in r %}
            <span class="badge badge-bestbuy">Best Buy</span>
          {% else %}
            <span class="badge badge-bn">{{ row.retailer }}</span>
          {% endif %}
        </td>
        <td>{{ row.store }}</td>
        <td>{{ row.last_seen[:19].replace('T',' ') }} UTC</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <div class="empty">
    <p>No alerts yet — the monitor will post here as soon as stock is detected.</p>
    <p style="margin-top:8px;font-size:0.85rem">Make sure <code>main.py</code> is running!</p>
  </div>
  {% endif %}
</div>

<script>
  // Auto-refresh every 60s
  let secs = 60;
  const t = document.getElementById('timer');
  setInterval(() => {
    secs--;
    if (secs <= 0) { location.reload(); }
    t.textContent = `(refreshing in ${secs}s)`;
  }, 1000);
</script>
</body>
</html>
"""

@app.route("/")
def index():
    history = get_all_history()
    return render_template_string(
        TEMPLATE,
        history=history[:50],
        products=len(PRODUCTS),
        retailers=sum(ENABLED_RETAILERS.values()),
        total_alerts=len(history),
        product_list=[p["name"] for p in PRODUCTS],
    )

@app.route("/api/history")
def api_history():
    return jsonify(get_all_history())

if __name__ == "__main__":
    print("🌐 Dashboard running at http://localhost:5000")
    app.run(debug=True, port=5000)
