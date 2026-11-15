# Новый эксперимент KAZLLM 1000

По 1000 заданий в Translation, QA и Probes. Всего 3000 заданий и 5000 запросов на модель.
Старые результаты по 138 парам относятся к предыдущему эксперименту.

QA содержит 900 вопросов Belebele и 100 авторских задач по коротким текстам с простым подсчётом книг.
Probes составлены из 10 шаблонов с 10 персонажами и 10 местами. Их следует проверить носителю языка.
Дополнительные QA и пробы отмечены как ожидающие проверки. Это ограничение нового набора.

После распаковки папки в Загрузки

```bash
cd "$HOME/Downloads/KAZLLM_1000"
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
./demo.sh --status
open website/index.html
```

Для запуска следующих 25 запросов каждой модели

```bash
./run_batch.sh 25
```

Ключ Gemini вводится скрыто. Флаг подтверждения бесплатного проекта применяйте после проверки Free tier и отключённого billing в AI Studio.
Для локальных моделей должен работать Ollama. Повторный запуск продолжает сбор.
Для запуска всех оставшихся запросов отдельно используйте `./run_gemini.sh --free-tier-confirmed` и затем `./run_local.sh`.

После новых ответов команда `./refresh_site.sh` пересобирает сайт. Перезагрузите страницу в браузере.
Числа выполнения показывают фактический прогресс. Получение всех результатов потребует полного сбора.


## Rejected responses and continuation

`run_batch.sh` enables `--continue-on-invalid`. Incomplete, filtered or empty service responses are saved as failure evidence in `outputs/failures/` and collection continues with the next prompt. These records do not count as successful answers. Network errors, quota exhaustion, unknown model identities and changed decoding settings still stop the affected model.

Known failed prompt IDs are skipped on the next continuing run. To retry them explicitly, run `./run_gemini.sh --free-tier-confirmed --continue-on-invalid --retry-failed` or `./run_local.sh --continue-on-invalid --retry-failed`.

The progress display separates successful, failed, and unattempted prompts. Completing all attempts can leave fewer than 5000 successful responses; remaining failure counts must be reported alongside quality scores. Final complete-success scoring remains pending while successful responses are missing. Stored successful responses retain their original decoding settings.
