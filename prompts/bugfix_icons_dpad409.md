# Bugfix: Icon Resolution + D-pad 409 Race Condition + README

## Файлы для изменения
- `web/app.js`
- `README.md`

## Контекст
Читай `CLAUDE.md` перед началом.

После расширения stratagems.json (~80 стратагем) видны два бага:
1. Новые варбондовые стратагемы показывают буквенный фоллбэк вместо иконки
2. Первый тап по D-pad иногда возвращает 409 CONFLICT

---

## Баг 1 — Иконки не загружаются для новых стратагем

### Причина
`resolveIconUrl()` строит URL вида:
```
https://raw.githubusercontent.com/nvigneux/Helldivers-2-Stratagems-icons-svg/main/<path>
```
где `<path>` берётся из поля `icon` в JSON **или** угадывается по имени.

Репозиторий nvigneux содержит иконки только для части стратагем.
Новые варбондовые (Solo Silo, Warp Pack, Maxigun и т.д.) могут отсутствовать.

### Исправление

В функции `resolveIconUrl(stratagem, iconRepo)` добавь проверку через
`fetch` с `{ method: 'HEAD' }` — если 404, сразу используй fallback.

**Реализуй так:**

```js
async function resolveIconUrl(stratagem, iconRepo) {
  // Если в JSON уже есть поле icon — используем его
  if (stratagem.icon) {
    return `${iconRepo}/${stratagem.icon}`;
  }

  // Список путей для перебора (от специфичного к общему)
  const candidates = buildIconCandidates(stratagem, iconRepo);

  for (const url of candidates) {
    try {
      const res = await fetch(url, { method: 'HEAD' });
      if (res.ok) return url;
    } catch (_) {
      // сетевая ошибка — идём дальше
    }
  }
  return null; // нет иконки → буквенный фоллбэк
}

function buildIconCandidates(stratagem, iconRepo) {
  const base = iconRepo; // e.g. https://raw.githubusercontent.com/...
  const name = stratagem.name; // "MS-11 Solo Silo"

  // Папки по категории
  const folderMap = {
    orbital:   'Bridge',
    eagle:     'Hangar',
    support:   'Patriotic Administration Center',
    backpack:  'Patriotic Administration Center',
    defensive: 'Engineering Bay / Robotic Workshop',
    vehicle:   'Patriotic Administration Center',
  };

  // Более точная карта папок по конкретным стратагемам
  const knownFolders = {
    'Gatling Sentry':        'Robotics Workshop',
    'Machine Gun Sentry':    'Robotics Workshop',
    'Autocannon Sentry':     'Robotics Workshop',
    'Rocket Sentry':         'Robotics Workshop',
    'Mortar Sentry':         'Robotics Workshop',
    'EMS Mortar Sentry':     'Robotics Workshop',
    'Tesla Tower':           'Robotics Workshop',
    'Flame Sentry':          'Robotics Workshop',
    'Gas Mortar Sentry':     'Robotics Workshop',
    'Grenadier Battlement':  'Robotics Workshop',
    'Shield Generator Relay':'Engineering Bay',
    'HMG Emplacement':       'Engineering Bay',
    'Anti-Tank Emplacement': 'Engineering Bay',
    'Anti-Personnel Minefield': 'Engineering Bay',
    'Anti-Tank Mines':       'Engineering Bay',
    'Incendiary Mines':      'Engineering Bay',
    'Gas Mines':             'Engineering Bay',
    'Patriot Exosuit':       'Patriotic Administration Center',
    'Emancipator Exosuit':   'Patriotic Administration Center',
    'Fast Recon Vehicle':    'Patriotic Administration Center',
    'Bastion MK XVI':        'Patriotic Administration Center',
  };

  const folder = knownFolders[name]
    ?? folderMap[stratagem.category]
    ?? 'Patriotic Administration Center';

  // Варианты имени файла
  const baseName = name.replace(/^(A\/|E\/|AX\/|AX\/AR-23 |AX\/LAS-5 |AX\/ARC-3 |AX\/TX-13 |AX\/FLAM-75 |A\/M-\d+ |A\/MG-\d+ |A\/G-\d+ |A\/MLS-\d+ |A\/AC-\d+ |A\/ARC-\d+ |E\/MG-\d+ |E\/AT-\d+ |E\/GL-\d+ |E\/FLAM-\d+ |FX-\d+ )/i, '').trim();

  const encode = s => encodeURIComponent(s).replace(/%20/g, '%20');

  return [
    `${base}/${encode(folder)}/${encode(name)}.svg`,
    `${base}/${encode(folder)}/${encode(baseName)}.svg`,
    // Пробуем все стандартные папки если не нашли
    `${base}/Bridge/${encode(name)}.svg`,
    `${base}/Hangar/${encode(name)}.svg`,
    `${base}/Patriotic%20Administration%20Center/${encode(name)}.svg`,
    `${base}/Engineering%20Bay/${encode(name)}.svg`,
    `${base}/Robotics%20Workshop/${encode(name)}.svg`,
  ];
}
```

**Важно:** `resolveIconUrl` становится `async`. Обнови все места где она вызывается — используй `await` или `.then()`.

В `makeCard()` / `renderGrid()` где создаётся `<img>`:
```js
resolveIconUrl(s, iconRepo).then(url => {
  if (url) {
    img.src = url;
    img.onerror = () => img.replaceWith(makeLetterIcon(s.name));
  } else {
    img.replaceWith(makeLetterIcon(s.name));
  }
});
```

Это позволяет рендерить карточки немедленно (с буквой), а иконку подставить когда HEAD-запрос вернётся.

---

## Баг 2 — 409 CONFLICT на `/api/manual/key`

### Причина
В `dpadTap()` при первом нажатии вызывается `/api/manual/start` и **сразу** (не дожидаясь ответа) `/api/manual/key`. Сервер возвращает 409 потому что `manual_active` ещё `false`.

### Исправление

Найди в `dpadTap()` место где вызывается `start` при `!_manualActive`:

```js
// БЫЛО (упрощённо):
if (!_manualActive) {
  apiFetch('/api/manual/start', 'POST');  // fire-and-forget
}
apiFetch('/api/manual/key', 'POST', { direction: dir });
```

**ИСПРАВЬ** так:
```js
async function dpadTap(dir) {
  if (!_manualActive) {
    _manualActive = true;
    try {
      await apiFetch('/api/manual/start', 'POST');
    } catch (e) {
      _manualActive = false;
      return;
    }
    _scheduleAutoRelease();
  }
  // Теперь гарантированно активно — отправляем ключ
  try {
    await apiFetch('/api/manual/key', 'POST', { direction: dir });
  } catch (e) {
    if (e?.status === 409) {
      // Рассинхрон — сбрасываем состояние
      _manualActive = false;
      setDpadStatus('inactive');
    }
  }
  renderDpadSequence(dir);
  _scheduleAutoRelease();
}
```

Убедись что `apiFetch` возвращает Promise (throws on non-2xx).

---

## Баг 3 — README устарел

В `README.md` найди и замени:
- `"59 stratagems"` → `"80+ stratagems"`
- В секции "All Stratagems view": `Browse all 59 stratagems` → `Browse all stratagems`

---

## Что НЕ трогать
- `stratagems.json` — уже обновлён
- Серверный код — только `app.js` и `README.md`
- Тесты — `pytest tests/` должен остаться 82 зелёных

## После правок
1. Открой PWA в браузере (WiFi режим)
2. Убедись: большинство иконок загружается (особенно базовые стратагемы)
3. Новые варбондовые с отсутствующими иконками → буква — это нормально
4. Зайди в D-pad, несколько раз тапни → нет 409 в консоли
5. Обнови `docs/changelog.md` и `orchestrator_report.md`
6. Коммит: `fix: icon HEAD-check fallback, dpad 409 race condition, readme count`
