# Update: stratagems.json — Full Stratagem List

## Файлы для изменения
- `data/stratagems.json`

## Контекст
Читай `CLAUDE.md` перед началом.

Текущий файл содержит ~59 стратагем (только базовые).
Нужно добавить все DLC/Warbond стратагемы по состоянию на март 2026.

## Требования к формату
Сохрани существующий формат JSON **полностью**:
- `version`, `icon_repo`, `categories` — не трогай
- Каждая стратагема: `id`, `name`, `keys`, `category`, `cooldown`, `verified`
- Добавь поле `"warbond": "Название варбонда"` для варбондовых стратагем
  (у базовых стратагем это поле отсутствует)
- `cooldown` в секундах (int); для Eagle — кулдаун реарма (не 8s между вызовами)
- Для стратагем с ограниченным числом использований: добавь поле `"uses": N`
- `verified: false` — если код не подтверждён (новые, ещё нет в вики)

## Полный список стратагем (замени существующий массив целиком)

### КАТЕГОРИЯ: orbital

```json
{"id":"orbital-precision-strike","name":"Orbital Precision Strike","keys":["right","right","up"],"category":"orbital","cooldown":100,"verified":true},
{"id":"orbital-gatling-barrage","name":"Orbital Gatling Barrage","keys":["right","down","left","up","up"],"category":"orbital","cooldown":70,"verified":true},
{"id":"orbital-airburst-strike","name":"Orbital Airburst Strike","keys":["right","right","right"],"category":"orbital","cooldown":100,"verified":true},
{"id":"orbital-120mm-he-barrage","name":"Orbital 120MM HE Barrage","keys":["right","right","down","left","right","down"],"category":"orbital","cooldown":180,"verified":true},
{"id":"orbital-380mm-he-barrage","name":"Orbital 380MM HE Barrage","keys":["right","down","up","up","left","down","down"],"category":"orbital","cooldown":240,"verified":true},
{"id":"orbital-walking-barrage","name":"Orbital Walking Barrage","keys":["right","down","right","down","right","down"],"category":"orbital","cooldown":240,"verified":true},
{"id":"orbital-laser","name":"Orbital Laser","keys":["right","down","up","right","down"],"category":"orbital","cooldown":300,"uses":3,"verified":true},
{"id":"orbital-railcannon-strike","name":"Orbital Railcannon Strike","keys":["right","up","down","down","right"],"category":"orbital","cooldown":210,"verified":true},
{"id":"orbital-napalm-barrage","name":"Orbital Napalm Barrage","keys":["right","right","down","left","right","up"],"category":"orbital","cooldown":240,"verified":true},
{"id":"orbital-gas-strike","name":"Orbital Gas Strike","keys":["right","right","down","right"],"category":"orbital","cooldown":75,"verified":true},
{"id":"orbital-ems-strike","name":"Orbital EMS Strike","keys":["right","right","left","down"],"category":"orbital","cooldown":75,"verified":true},
{"id":"orbital-smoke-strike","name":"Orbital Smoke Strike","keys":["right","right","down","up"],"category":"orbital","cooldown":100,"verified":true}
```

### КАТЕГОРИЯ: eagle

```json
{"id":"eagle-strafing-run","name":"Eagle Strafing Run","keys":["up","right","right"],"category":"eagle","cooldown":120,"uses":4,"verified":true},
{"id":"eagle-airstrike","name":"Eagle Airstrike","keys":["up","right","down","right"],"category":"eagle","cooldown":120,"uses":2,"verified":true},
{"id":"eagle-cluster-bomb","name":"Eagle Cluster Bomb","keys":["up","right","down","down","right"],"category":"eagle","cooldown":150,"uses":4,"verified":true},
{"id":"eagle-napalm-airstrike","name":"Eagle Napalm Airstrike","keys":["up","right","down","up"],"category":"eagle","cooldown":120,"uses":2,"verified":true},
{"id":"eagle-110mm-rocket-pods","name":"Eagle 110MM Rocket Pods","keys":["up","right","up","left"],"category":"eagle","cooldown":120,"uses":2,"verified":true},
{"id":"eagle-500kg-bomb","name":"Eagle 500kg Bomb","keys":["up","right","down","down","down"],"category":"eagle","cooldown":120,"uses":1,"verified":true},
{"id":"eagle-smoke-strike","name":"Eagle Smoke Strike","keys":["up","right","up","down"],"category":"eagle","cooldown":120,"uses":2,"verified":true}
```

### КАТЕГОРИЯ: support (Support Weapons — PAC + Warbonds)

```json
{"id":"machine-gun","name":"MG-43 Machine Gun","keys":["down","left","down","up","right"],"category":"support","cooldown":480,"verified":true},
{"id":"stalwart","name":"M-105 Stalwart","keys":["down","left","down","up","up","left"],"category":"support","cooldown":480,"verified":true},
{"id":"heavy-machine-gun","name":"MG-206 Heavy Machine Gun","keys":["down","left","up","down","down"],"category":"support","cooldown":480,"verified":true},
{"id":"anti-materiel-rifle","name":"APW-1 Anti-Materiel Rifle","keys":["down","left","right","up","down"],"category":"support","cooldown":480,"verified":true},
{"id":"grenade-launcher","name":"GL-21 Grenade Launcher","keys":["down","left","up","left","down"],"category":"support","cooldown":480,"verified":true},
{"id":"flamethrower","name":"FLAM-40 Flamethrower","keys":["down","left","up","down","up"],"category":"support","cooldown":480,"verified":true},
{"id":"autocannon","name":"AC-8 Autocannon","keys":["down","left","down","up","up","right"],"category":"support","cooldown":480,"verified":true},
{"id":"railgun","name":"RS-422 Railgun","keys":["down","right","down","up","left","right"],"category":"support","cooldown":480,"verified":true},
{"id":"spear","name":"FAF-14 Spear Launcher","keys":["down","down","up","down","down"],"category":"support","cooldown":480,"verified":true},
{"id":"recoilless-rifle","name":"GR-8 Recoilless Rifle","keys":["down","left","right","right","left"],"category":"support","cooldown":480,"verified":true},
{"id":"laser-cannon","name":"LAS-98 Laser Cannon","keys":["down","left","down","up","left"],"category":"support","cooldown":480,"verified":true},
{"id":"arc-thrower","name":"ARC-3 Arc Thrower","keys":["down","right","down","up","left","left"],"category":"support","cooldown":480,"verified":true},
{"id":"quasar-cannon","name":"LAS-99 Quasar Cannon","keys":["down","down","up","left","right"],"category":"support","cooldown":480,"verified":true},
{"id":"expendable-anti-tank","name":"EAT-17 Expendable Anti-Tank","keys":["down","down","left","up","right"],"category":"support","cooldown":70,"verified":true},
{"id":"commando","name":"MLS-4X Commando","keys":["down","left","up","down","right"],"category":"support","cooldown":120,"verified":true},
{"id":"airburst-rocket-launcher","name":"RL-77 Airburst Rocket Launcher","keys":["down","up","up","left","right"],"category":"support","cooldown":480,"verified":true},
{"id":"wasp-launcher","name":"StA-X3 W.A.S.P. Launcher","keys":["down","down","up","down","right"],"category":"support","cooldown":432,"verified":true,"warbond":"Truth Enforcers"},
{"id":"de-escalator","name":"GL-52 De-Escalator","keys":["down","right","up","left","right"],"category":"support","cooldown":480,"verified":true,"warbond":"Urban Legends"},
{"id":"sterilizer","name":"TX-41 Sterilizer","keys":["down","left","up","down","left"],"category":"support","cooldown":480,"verified":true,"warbond":"Chemical Agents"},
{"id":"one-true-flag","name":"CQC-1 One True Flag","keys":["down","left","right","right","up"],"category":"support","cooldown":480,"verified":true,"warbond":"Servants of Freedom"},
{"id":"solo-silo","name":"MS-11 Solo Silo","keys":["down","up","right","down","down"],"category":"support","cooldown":180,"uses":1,"verified":true,"warbond":"Dust Devils"},
{"id":"expendable-napalm","name":"EAT-700 Expendable Napalm","keys":["down","down","left","up","left"],"category":"support","cooldown":70,"verified":false,"warbond":"Dust Devils"},
{"id":"speargun","name":"S-11 Speargun","keys":["down","right","down","left","up","right"],"category":"support","cooldown":480,"verified":true,"warbond":"Dust Devils"},
{"id":"maxigun","name":"M-1000 Maxigun","keys":["down","left","down","up","right","right"],"category":"support","cooldown":480,"verified":false,"warbond":"Python Commandos"},
{"id":"epoch","name":"PLAS-45 Epoch","keys":["down","right","down","up","right","left"],"category":"support","cooldown":480,"verified":false,"warbond":"Control Group"},
{"id":"leveller","name":"EAT-411 Leveller","keys":["down","down","left","up","up"],"category":"support","cooldown":70,"verified":false,"warbond":"Masters of Ceremony"},
{"id":"belt-fed-grenade-launcher","name":"GL-28 Belt-Fed Grenade Launcher","keys":["down","left","up","left","left"],"category":"support","cooldown":480,"verified":false,"warbond":"Force of Law"},
{"id":"cremator","name":"B/FLAM-80 Cremator","keys":["down","left","up","down","down"],"category":"support","cooldown":480,"verified":false,"warbond":"Entrenched Division"}
```

### КАТЕГОРИЯ: backpack

```json
{"id":"supply-pack","name":"B-1 Supply Pack","keys":["down","left","down","up","up","down"],"category":"backpack","cooldown":480,"verified":true},
{"id":"jump-pack","name":"LIFT-850 Jump Pack","keys":["down","up","up","down","up"],"category":"backpack","cooldown":480,"verified":true},
{"id":"shield-generator-pack","name":"SH-32 Shield Generator Pack","keys":["down","up","left","right","left","right"],"category":"backpack","cooldown":480,"verified":true},
{"id":"ballistic-shield","name":"SH-20 Ballistic Shield Backpack","keys":["down","left","down","down","up","left"],"category":"backpack","cooldown":300,"verified":true},
{"id":"guard-dog-rover","name":"AX/LAS-5 Guard Dog Rover","keys":["down","up","left","up","right","right"],"category":"backpack","cooldown":480,"verified":true},
{"id":"guard-dog","name":"AX/AR-23 Guard Dog","keys":["down","up","left","up","right","down"],"category":"backpack","cooldown":480,"verified":true},
{"id":"guard-dog-dog-breath","name":"AX/TX-13 Guard Dog Dog Breath","keys":["down","up","left","up","right","up"],"category":"backpack","cooldown":480,"verified":true,"warbond":"Chemical Agents"},
{"id":"guard-dog-k9","name":"AX/ARC-3 Guard Dog K-9","keys":["down","up","left","up","right","left"],"category":"backpack","cooldown":480,"verified":true,"warbond":"Cutting Edge"},
{"id":"portable-hellbomb","name":"B-100 Portable Hellbomb","keys":["down","right","up","up","up"],"category":"backpack","cooldown":300,"verified":true,"warbond":"Democratic Detonation"},
{"id":"directional-shield","name":"SH-51 Directional Shield Backpack","keys":["down","up","left","right","up","up"],"category":"backpack","cooldown":300,"verified":true,"warbond":"Viper Commandos"},
{"id":"hover-pack","name":"LIFT-860 Hover Pack","keys":["down","up","up","down","left","right"],"category":"backpack","cooldown":480,"verified":true,"warbond":"Servants of Freedom"},
{"id":"warp-pack","name":"LIFT-182 Warp Pack","keys":["down","up","up","down","right","left"],"category":"backpack","cooldown":480,"verified":false,"warbond":"Borderline Justice"},
{"id":"hot-dog","name":"AX/FLAM-75 Hot Dog","keys":["down","up","left","up","right","right"],"category":"backpack","cooldown":480,"verified":false,"warbond":"Freedom's Flame"},
{"id":"c4-pack","name":"B/MD C4 Pack","keys":["down","right","up","left","up"],"category":"backpack","cooldown":300,"verified":false,"warbond":"Masters of Ceremony"}
```

### КАТЕГОРИЯ: defensive (Sentries, Emplacements, Mines)

```json
{"id":"machine-gun-sentry","name":"A/MG-43 Machine Gun Sentry","keys":["down","up","right","right","up"],"category":"defensive","cooldown":120,"verified":true},
{"id":"gatling-sentry","name":"A/G-16 Gatling Sentry","keys":["down","up","right","left"],"category":"defensive","cooldown":180,"verified":true},
{"id":"mortar-sentry","name":"A/M-12 Mortar Sentry","keys":["down","up","right","right","down"],"category":"defensive","cooldown":180,"verified":true},
{"id":"autocannon-sentry","name":"A/AC-8 Autocannon Sentry","keys":["down","up","right","up","left","up"],"category":"defensive","cooldown":180,"verified":true},
{"id":"rocket-sentry","name":"A/MLS-4X Rocket Sentry","keys":["down","up","right","right","left"],"category":"defensive","cooldown":180,"verified":true},
{"id":"ems-mortar-sentry","name":"A/M-23 EMS Mortar Sentry","keys":["down","up","right","down","right"],"category":"defensive","cooldown":180,"verified":true},
{"id":"tesla-tower","name":"A/ARC-3 Tesla Tower","keys":["down","up","right","up","left","right"],"category":"defensive","cooldown":150,"verified":true},
{"id":"flame-sentry","name":"E/FLAM-40 Flame Sentry","keys":["down","up","right","down","up","up"],"category":"defensive","cooldown":150,"verified":true,"warbond":"Freedom's Flame"},
{"id":"shield-generator-relay","name":"FX-12 Shield Generator Relay","keys":["down","down","left","right","left","right"],"category":"defensive","cooldown":90,"verified":true},
{"id":"hmg-emplacement","name":"E/MG-101 HMG Emplacement","keys":["down","up","left","right","right","left"],"category":"defensive","cooldown":180,"verified":true},
{"id":"anti-tank-emplacement","name":"E/AT-12 Anti-Tank Emplacement","keys":["down","up","left","right","right","right"],"category":"defensive","cooldown":180,"verified":true,"warbond":"Urban Legends"},
{"id":"grenadier-battlement","name":"E/GL-21 Grenadier Battlement","keys":["down","right","down","left","right"],"category":"defensive","cooldown":180,"verified":true,"warbond":"Obedient Democracy Support Troopers"},
{"id":"anti-personnel-minefield","name":"MD-6 Anti-Personnel Minefield","keys":["down","left","up","right"],"category":"defensive","cooldown":180,"verified":true},
{"id":"anti-tank-mines","name":"MD-17 Anti-Tank Mines","keys":["down","left","up","up"],"category":"defensive","cooldown":180,"verified":true},
{"id":"incendiary-mines","name":"MD-I4 Incendiary Mines","keys":["down","left","left","down"],"category":"defensive","cooldown":180,"verified":true},
{"id":"gas-mines","name":"MD-8 Gas Mines","keys":["down","left","left","right"],"category":"defensive","cooldown":180,"verified":true,"warbond":"Chemical Agents"},
{"id":"gas-mortar-sentry","name":"A/GM-17 Gas Mortar Sentry","keys":["down","up","right","down","left"],"category":"defensive","cooldown":180,"verified":false,"warbond":"Entrenched Division"}
```

### КАТЕГОРИЯ: vehicle

```json
{"id":"patriot-exosuit","name":"EXO-45 Patriot Exosuit","keys":["left","down","right","up","left","down","down"],"category":"vehicle","cooldown":600,"uses":3,"verified":true},
{"id":"emancipator-exosuit","name":"EXO-49 Emancipator Exosuit","keys":["left","down","right","up","left","down","up"],"category":"vehicle","cooldown":600,"uses":3,"verified":true,"warbond":"Polar Patriots"},
{"id":"fast-recon-vehicle","name":"M-102 Fast Recon Vehicle","keys":["left","down","right","down","right","down","up"],"category":"vehicle","cooldown":480,"verified":true,"warbond":"Servants of Freedom"},
{"id":"bastion","name":"TD-220 Bastion MK XVI","keys":["left","down","right","down","left","down","up"],"category":"vehicle","cooldown":600,"uses":3,"verified":false,"warbond":"Python Commandos"}
```

## Категории (категории не меняй, только убедись что все присутствуют)
Должны быть: `orbital`, `eagle`, `support`, `backpack`, `defensive`, `vehicle`

## Важные правила
- `id` — kebab-case, уникальный
- `keys` — только значения: `"up"`, `"down"`, `"left"`, `"right"`
- `cooldown` — в секундах, целое число
- `verified: false` — для стратагем с неподтверждёнными кодами (новые варбонды)
- Поле `warbond` — только у варбондовых, у базовых отсутствует
- Если у стратагемы есть поле `uses` — показывает количество зарядов до реарма

## После обновления
1. `python scripts/validate_json.py` — должен пройти без ошибок
2. `pytest tests/` — 82 теста, все зелёные
3. Запусти сервер, открой PWA — все стратагемы видны, категории работают
4. Обнови `docs/changelog.md` и `orchestrator_report.md`
5. Коммит: `data: expand stratagems.json to full list including DLC and warbonds`

## Примечание по иконкам
Иконки берутся из `icon_repo` на GitHub CDN (nvigneux/Helldivers-2-Stratagems-icons-svg).
Для новых варбондовых стратагем иконки могут отсутствовать в репозитории —
в этом случае PWA покажет fallback (буква). Это нормально, `verified: false` в JSON.
