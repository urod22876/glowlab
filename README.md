# Glow Lab

Сайт **glow-lub.com**: ИИ-анализ пропорций лица, личный план улучшения и подписка Glow Lab Pro.

## Как устроено
- `site/` — готовый сайт, который публикуется на Cloudflare Pages (проект `glowlab`).
  - `index.html` — весь сайт одним файлом (картинки и модели внутри).
  - `_worker.js` — сервер: проверка Pro (Dodo Payments), ИИ-ассистент (Gemini / Claude), вход Google через свой домен, `/api/diag`.
  - `terms.html`, `privacy.html`, `refund.html` — юридические страницы.
- `build/` — исходники, из которых собирается `site/`:
  - `base/` — исходный светлый сайт;
  - `build_dark.py` + `darkify.py`, `dark_layer.css`, `dark_legal.css`, `guides_new.js`, `assets/` — тёмная тема, главный экран, гайды, окно результата;
  - `build_pro.py` + `pro_*.js`, `pro.css` — Pro: оплата, план, лица, прогресс, до/после, отчёт, настройки, ассистент;
  - `_worker.js` — исходник сервера (копируется в `site/`);
  - `tests/` — проверки сервера (Node) и сайта в браузере (Playwright).

## Сборка
```
./build.sh
```
Собирает `site/` заново из `build/`. Нужен Python 3.

## Публикация
Каждый push в ветку `main` автоматически публикует `site/` на Cloudflare Pages (`.github/workflows/deploy.yml`).
Перед публикацией запускаются проверки сервера.

## Настройки Cloudflare (Pages → glowlab → Settings → Variables and Secrets)
Ключи хранятся только там, в коде их нет.
- `DODO_API_KEY` (Secret), `DODO_MODE` = live, `DODO_PRODUCT_IDS`
- `GEMINI_API_KEY` (Secret), `GEMINI_MODEL`, необязательно `GEMINI_FALLBACK`, `GEMINI_THINKING`; или `ANTHROPIC_API_KEY`
- `PRO_EMAILS` — почты с бесплатным Pro
- `AUTH_SELF` = 1 — вход Google через свой домен (после настройки redirect URI в Google Cloud)

## Проверки
```
node build/tests/pro_worker_test.mjs site/_worker.js
node build/tests/stream_test.mjs site/_worker.js
python3 build/tests/pro_e2e.py site shots phone     # нужен playwright
```
