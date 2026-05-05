const STORAGE_KEY = 'tw-watchlist';
const API_BASE = 'https://mis.twse.com.tw/stock/api/getStockInfo.jsp?json=1&delay=0&ex_ch=';

const stockListEl = document.getElementById('stockList');
const addBtn = document.getElementById('addStockBtn');
const dlg = document.getElementById('stockDialog');
const form = document.getElementById('stockForm');
const cancelBtn = document.getElementById('cancelBtn');
const updateTime = document.getElementById('updateTime');
const tpl = document.getElementById('stockItemTpl');

let stocks = loadStocks();

function loadStocks() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) ?? [];
  } catch {
    return [];
  }
}

function saveStocks() { localStorage.setItem(STORAGE_KEY, JSON.stringify(stocks)); }

function exCode(code) { return `tse_${code}.tw`; }

async function fetchStock(code) {
  const res = await fetch(`${API_BASE}${encodeURIComponent(exCode(code))}`);
  const data = await res.json();
  const info = data.msgArray?.[0];
  if (!info) throw new Error('查無資料');
  const name = info.n || '未知名稱';
  const now = Number(info.z || info.b || 0);
  const prev = Number(info.y || 0);
  const diff = now - prev;
  return { code, name, now, diff };
}

function renderItems(items) {
  stockListEl.innerHTML = '';
  for (const item of items) {
    const node = tpl.content.firstElementChild.cloneNode(true);
    node.querySelector('.code').textContent = item.code;
    node.querySelector('.name').textContent = item.name;
    node.querySelector('.price').textContent = Number.isFinite(item.now) ? item.now.toFixed(2) : '--';

    const changeEl = node.querySelector('.change');
    const diff = Number.isFinite(item.diff) ? item.diff : 0;
    changeEl.textContent = `${diff >= 0 ? '+' : ''}${diff.toFixed(2)}`;
    changeEl.classList.add(diff > 0 ? 'up' : diff < 0 ? 'down' : 'flat');

    node.querySelector('.remove-btn').addEventListener('click', () => {
      stocks = stocks.filter((s) => s !== item.code);
      saveStocks();
      refresh();
    });

    stockListEl.appendChild(node);
  }
}

async function refresh() {
  if (!stocks.length) {
    stockListEl.innerHTML = '<li class="stock-item">目前尚未新增股票，按下 ＋ 開始。</li>';
    updateTime.textContent = '尚未設定追蹤股';
    return;
  }
  const results = await Promise.allSettled(stocks.map(fetchStock));
  const items = results.map((res, i) => res.status === 'fulfilled' ? res.value : ({ code: stocks[i], name: '讀取失敗', now: NaN, diff: NaN }));
  renderItems(items);
  updateTime.textContent = `更新時間：${new Date().toLocaleTimeString('zh-TW', { hour12: false })}`;
}

addBtn.addEventListener('click', () => dlg.showModal());
cancelBtn.addEventListener('click', () => dlg.close());
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const code = form.stockCode.value.trim();
  if (!/^\d{4}$/.test(code)) return;
  if (stocks.includes(code)) {
    dlg.close();
    form.reset();
    return;
  }
  stocks.push(code);
  saveStocks();
  form.reset();
  dlg.close();
  await refresh();
});

refresh();
setInterval(refresh, 5000);
