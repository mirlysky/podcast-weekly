(() => {
  const select = document.querySelector('#workout-week');
  const status = document.querySelector('#workout-status');
  const body = document.querySelector('#workout-body');
  const tables = document.querySelector('#workout-tables');
  const tabs = [...document.querySelectorAll('[role="tab"]')];
  const categories = {
    functionalStrengthTraining: '力量训练',
    skatingSports: '花样滑冰',
    outdoorWalking: '户外步行',
  };
  const number = new Intl.NumberFormat('zh-CN', {maximumFractionDigits: 1});
  const minutes = seconds => number.format(seconds / 60) + ' 分钟';
  let weeks;

  function render() {
    const week = weeks.find(item => item.start === select.value);
    const totals = {count: 0, seconds: 0, kcal: 0, missingEnergy: 0};
    tables.replaceChildren();
    for (const [key, label] of Object.entries(categories)) {
      const item = week.activities[key];
      for (const field of Object.keys(totals)) totals[field] += item[field];
      const table = document.createElement('table');
      table.createCaption().textContent = label;
      const header = table.createTHead().insertRow();
      for (const name of ['次数', '时长']) {
        const cell = document.createElement('th');
        cell.scope = 'col';
        cell.textContent = name;
        header.append(cell);
      }
      const row = table.createTBody().insertRow();
      const unconfirmedOutdoor = key === 'outdoorWalking' && week.outdoorIncomplete && !item.count;
      row.insertCell().textContent = unconfirmedOutdoor ? '待确认' : item.count + ' 次';
      row.insertCell().textContent = unconfirmedOutdoor ? '—' : minutes(item.seconds);
      tables.append(table);
    }
    document.querySelector('#workout-count').textContent = totals.count + ' 次';
    document.querySelector('#workout-duration').textContent = minutes(totals.seconds);
    document.querySelector('#workout-energy').textContent = totals.count && totals.missingEnergy === totals.count
      ? '暂无记录' : number.format(totals.kcal) + ' kcal';
    const notes = [];
    if (week.outdoorIncomplete) notes.push('部分步行缺少户外标记，合计仅包含已确认的运动。');
    if (totals.missingEnergy) notes.push(totals.missingEnergy + ' 次运动缺少活动消耗记录。');
    status.textContent = notes.join('');
    body.hidden = false;
  }

  async function load() {
    status.textContent = '正在加载…';
    try {
      const data = await getJSON('./workouts.json');
      weeks = data.weeks;
      document.querySelector('#workout-meta').textContent =
        '周一至周日 · ' + data.timeZone + ' · 已统计至 ' + data.through;
      if (!weeks.length) {
        status.textContent = '暂无已导入的运动统计。';
        return;
      }
      select.replaceChildren(...weeks.map(item =>
        new Option(item.start + ' 至 ' + item.end, item.start)));
      select.disabled = false;
      render();
    } catch {
      weeks = undefined;
      select.disabled = true;
      body.hidden = true;
      status.textContent = '运动统计加载失败，请刷新后重试。';
    }
  }

  function activate(tab) {
    for (const item of tabs) {
      const active = item === tab;
      item.setAttribute('aria-selected', String(active));
      item.tabIndex = active ? 0 : -1;
      document.getElementById(item.getAttribute('aria-controls')).hidden = !active;
    }
    if (tab.id === 'workout-tab' && !weeks && status.textContent !== '正在加载…') load();
  }

  for (const tab of tabs) {
    tab.addEventListener('click', () => activate(tab));
    tab.addEventListener('keydown', event => {
      const targets = {ArrowLeft: tabs[1 - tabs.indexOf(tab)], ArrowRight: tabs[1 - tabs.indexOf(tab)],
        Home: tabs[0], End: tabs.at(-1)};
      const target = targets[event.key];
      if (!target) return;
      event.preventDefault();
      activate(target);
      target.focus();
    });
  }
  select.addEventListener('change', render);
})();
