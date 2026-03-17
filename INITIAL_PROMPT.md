# INITIAL_PROMPT.md
# Стартовый промпт для Claude Code при новой сессии.
# Скопируй секцию PROMPT ниже и вставь в Claude Code.

---

## PROMPT (скопировать отсюда и до конца файла)

Ты — разработчик проекта **Stratagem Launcher**. Фазы 1–7 завершены, 67 тестов проходят.

### Контекст
- Ты работаешь **в WSL**. Сервер запускается **на Windows** (PowerShell) — pynput не работает из WSL.
- Файлы общие: `/mnt/c/Users/arsup/Desktop/claude_playground/stratagem_launcher`
- keypress.py использует `KeyCode.from_vk()` (VK codes, WM_KEYDOWN)

### Твой рабочий процесс

1. **Сначала** прочитай:
   - `CLAUDE.md` (правила проекта, ⚠️ два окружения)
   - `orchestrator_report.md` (полный отчёт: архитектура, API, файлы)
   - `docs/progress.md` (текущий прогресс)

2. **Перед каждой фазой/фичей** — составь план задач, покажи мне, жди "ок".

3. **После каждой задачи**:
   - Обнови `docs/progress.md`
   - Обнови `docs/changelog.md`
   - Покажи итог, жди подтверждения

4. **Не делай несколько фаз за раз.**

### Следующие фазы

- **Phase 8: Cooldown Modifier** → прочитай `prompts/feature_cooldowns.md`
- **Phase 9: Desktop EXE** → прочитай `prompts/feature_exe_manager.md`

### Начало

Прочитай файлы проекта, сверься с progress.md, предложи план для следующей фазы.
