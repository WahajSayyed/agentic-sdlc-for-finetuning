## Here's the plan before we build:

**Backend** — one new endpoint `GET /api/v1/executions/{id}/download` that:
1. Checks `output/{execution_id}/` exists and has files
2. Zips the entire folder in memory (no temp files on disk)
3. Streams it back as `application/zip` with filename `execution_{id}_artifacts.zip`
4. Returns 404 if execution doesn't exist, 404 if no artifacts yet

**Frontend** — two places:
- **Executions list** — small download icon button on each row (only enabled when status is `completed`)
- **Execution detail** — prominent "Download Artifacts" button (same condition)

Perfect — I'll work from the Celery version we built. Let's go.

---

### File 1 — Updated `web/executions/router.py`---

### File 2 — `ui/lib/api.ts` — add download function

Add this to the `executions` object in your existing `api.ts`:---

### File 3 — `ui/components/executions/DownloadButton.tsx`Now I need to see your current `ExecutionsTable.tsx` and `execution-detail` components to add the button in the right place. Let me check what we built:Good — I have everything I need. Now update both components:Now add `downloadArtifacts` to `api.ts`:---

## Summary — Files to Update

```
web/executions/router.py                          ← REPLACE (adds /download endpoint)
ui/lib/api.ts                                     ← REPLACE (adds downloadArtifacts)
ui/components/executions/DownloadButton.tsx       ← CREATE  (new reusable component)
ui/components/executions/ExecutionsTable.tsx      ← REPLACE (adds icon button column)
ui/components/execution-detail/ExecutionHeader.tsx ← REPLACE (adds prominent button)
```

---

## How it behaves

**Executions list** — each row gets a `⬇` icon button in a new Download column. It's greyed out and disabled for `pending`/`running` rows, active for `completed`/`failed`. Clicking it downloads without navigating away — `stopPropagation()` prevents the row click from triggering navigation.

**Execution detail** — a full "Download Artifacts" button appears top-right of the header, aligned opposite the back button. Shows a spinner while downloading, an error message if something goes wrong, and a hint "Available once execution completes" when the execution hasn't finished yet.

**One important note** — after replacing `router.py`, restart the API container so the new endpoint registers:
```bash
task docker:restart
# or just
docker compose restart api
```