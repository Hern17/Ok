AGENTS.md – Quick Reference for TalentMatch AI

## Setup & Environment

- Use **uv** (not pip) for all dependency management.
    ```bash
    uv venv .venv          # create virtual env
    .\.venv\Scripts\Activate.ps1   # PowerShell activation
    uv sync                # install from pyproject.toml (Python ≥3.10)
    ```
- Python version must be **≥3.10** (enforced in `pyproject.toml`).

## Running the Application

- Start Flask dev server (debug mode) with:
    ```bash
    uv run app.py
    ```
- Server always listens on `http://127.0.0.1:5000`.

## Testing & Quality Checks

- Lint with **ruff** (default lint config):
    ```bash
    uv run ruff .
    ```
- Type‑check with **mypy** (if present in repo):
    ```bash
    uv run mypy .
    ```
- Run tests (only if `pytest` is installed):
    ```bash
    uv run pytest
    ```
- Recommended order for CI: **lint → type‑check → test**.

## Core Packages & Entry Points

| Package                 | Purpose                                                           |
| ----------------------- | ----------------------------------------------------------------- |
| `app.py`                | Flask routes, entrypoint for web UI                               |
| `auth.py`               | Login/session decorators                                          |
| `db.py`                 | SQLite schema, migrations                                         |
| `ai_helper.py`          | Questionnaire analysis, skill inference                           |
| `cv_renderer.py`        | Build CV data, render TXT/Typst, PDF generation                   |
| `templates/`            | Jinja2 UI, dynamic questionnaire rendering                        |
| `data/cv_template.yaml` | Single source of truth for CV layout **and** questionnaire schema |

## Data Flow Highlights (Agent‑Important)

1. **Questionnaire → JSON**
   `candidate_save_questionnaire` (`app.py:118`) stores the full payload
   in `candidates.questionnaire_data` (JSON string). It is **not** on the
   `users` table.
2. **AI analysis** (`ai_helper.analyze_questionnaire`) receives that JSON (`qdata`).
   - **Key conflict**: `experience` appears twice in `cv_template.yaml`.
     - **Select field** (`about` section) → string (`entry`, `mid`, `senior`, `lead`).
     - **Entries field** (`work_experience` section) → list of dicts.
   - `exp_labels` lookup expects a string. The local helper `to_str`
     (L269‑272) now coerces any non‑string to `str(value)` and falls back
     to a default, so dict/list/`None` cannot raise
     `TypeError: unhashable type` any more. Do not remove that guard.
3. **CV builder** (`cv_renderer._build_user_data`) maps data to section IDs.
   - `profile` arrives as a `sqlite3.Row` (the route uses
     `get_db()` → `conn.row_factory = sqlite3.Row`). Rows have no
     `.get()`, so `_build_user_data` first does
     `profile = dict(profile) if profile else {}`. Keep that conversion.
   - `certifications` is a list of Rows too; each item is converted
     before `.get('name', ...)` / `.get('skills', [])`.
   - `work_experience` entries are stored under key `experience` for the
     **section ID**:
     ```python
     data["experience"] = qdata.get("work_experience", [])
     ```
   - Do **not** map the `experience` select (string) to that key.

## Questionnaire Rendering (JS) – Gotchas

- **Dynamic entry fields** (`entries` type) rely on `window._entryFields_<key>`.
    - Inline `<script>` tags injected via `innerHTML` never execute.
    - **Fix**: initialise those globals in `renderSections()` after sections are built:
        ```javascript
        SECTIONS.sections.forEach((sec) => {
            (sec.questions || []).forEach((q) => {
                if (q.type === "entries" && q.fields) {
                    window[`_entryFields_${q.key}`] = q.fields;
                }
            });
        });
        ```
- **Prefill data** must use `q.key` (not `q.id`) when locating DOM elements.
- **Add/Remove entry UI** is handled by `addEntry(key, prefill?)` and
  `collectEntries(key)`. Ensure both functions exist in
  `candidate_questionnaire.html`.

## Common Pitfalls & Fixes

- **Duplicate key `experience`** → rename entries field to `work_experience`
  in `cv_template.yaml` (already applied).
- **`exp_labels` lookup failure** → `to_str` already guards it. If you
  refactor, preserve the `str(value)` fallback for non‑string types.
- **`profile.get(...)` on a `sqlite3.Row`** → always convert with
  `dict(profile)` first or use bracket access. The current renderer
  does this in `_build_user_data`.
- **Cert list items are Rows too** → convert each before `.get(...)`.
- **Missing `_entryFields_` init** → add init loop in `renderSections()`
  (see above).
- **Work Experience not shown in CV** → `cv_renderer._build_user_data`
  must map `work_experience` → `experience` (section ID). Verify that
  mapping exists.
- **Script tags in HTML** → never rely on `<script>` inside generated
  HTML; always set globals via JS after DOM creation.

## Debugging Tips

- Inspect `qdata` before calling `analyze_questionnaire`:
    ```python
    import json, pprint
    pprint.pprint(json.loads(profile['questionnaire_data']))
    ```
  (`profile` here = the `candidates` row.)
- Verify `exp_labels` keys:
    ```python
    exp_labels = {"entry": "Entry Level", "mid": "Mid Level", "senior": "Senior Level", "lead": "Lead / Manager"}
    ```
- Check generated CV JSON:
    ```bash
    uv run python -c "from cv_renderer import generate_cv; import json; profile={'questionnaire_data':json.dumps({...})}; print(generate_cv(profile, [], {}, fmt='txt'))"
    ```
- Use Flask debug console (`flask run --debug`) to inspect `request.form`
  payload on `/candidate/save_questionnaire`.

## Reference Files (high‑signal)

- `pyproject.toml` – dependency list, required Python version.
- `data/cv_template.yaml` – schema definitions, crucial for questionnaire
  & CV generation.
- `db.py` – `candidates` table holds `questionnaire_data` and `skills`.
- `ai_helper.py` – `to_str` (L269) is the guard for non‑string fields.
  `exp_labels.get(...)` is the original failure point.
- `cv_renderer.py` – `_build_user_data` does `dict(profile)` conversion
  and maps `work_experience` → `experience`.
- `templates/candidate_questionnaire.html` – entry UI, prefill logic,
  `_entryFields_` init.

---

\*Keep this file in the repository root as `AGENTS.md`. It is the
definitive cheat‑sheet for any OpenCode session working on TalentMatch AI.
