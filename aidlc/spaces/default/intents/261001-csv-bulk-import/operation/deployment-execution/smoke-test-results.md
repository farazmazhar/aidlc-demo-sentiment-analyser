# Smoke Test Results — CSV Bulk Import / Export

> Stage: **deployment-execution**. Real ASGI app served by real `uvicorn` at
> `http://127.0.0.1:8137`, offline engine, throwaway database.

## Import request

`POST /v1/analyses/import`, `Content-Type: text/csv`, body (one text per row, with
a `text` header row and one blank row):

```
text
I love this product
This is terrible and slow

I feel okay about it
```

**Response `200 OK`:**

```json
{
  "import_id": "bc0519de75194dbd9f8d51e50ffc75d3",
  "imported": 3,
  "skipped": 1,
  "label_counts": {"positive": 1, "negative": 1, "neutral": 1},
  "mean_confidence": 0.7999999999999999
}
```

The header row was skipped, the blank row was counted as skipped and did not
abort the request, and the three analyzable rows were persisted under one shared
`import_id` — exactly FR1.2/FR1.3/FR1.4/FR1.5/FR1.6.

## Export request

`GET /v1/analyses/export?import_id=bc0519de75194dbd9f8d51e50ffc75d3`

**Response `200 OK`**, headers:

```
content-type: text/csv; charset=utf-8
content-disposition: attachment; filename="analyses-bc0519de75194dbd9f8d51e50ffc75d3.csv"
```

body:

```csv
id,text,label,confidence,model,provider,created_at
3,I feel okay about it,neutral,0.7,dummy-keyword-v1,offline,2026-10-01T16:34:19Z
2,This is terrible and slow,negative,0.85,dummy-keyword-v1,offline,2026-10-01T16:34:19Z
1,I love this product,positive,0.85,dummy-keyword-v1,offline,2026-10-01T16:34:19Z
```

Newest-first ordering, the documented column set, `text/csv`, and the attachment
disposition — exactly FR2.2/FR2.3.

## Negative / edge cases

| Request | Response | Expectation |
|---------|----------|-------------|
| `GET /v1/analyses/export?import_id=does-not-exist` | `404` `{"code":"IMPORT_NOT_FOUND","message":"No analyses were found for import_id 'does-not-exist'."}` | FR2.4 — envelope, not an empty body |
| `POST /v1/analyses/import` with `Content-Type: application/json` | `422` `{"code":"VALIDATION_FAILED","message":"body: Input should be a valid bytes"}` | FR1.7 — unsupported content type refused through the envelope |
| `GET /v1/analyses` (existing endpoint) | `200` bare JSON array; each record now carries `"import_id": "bc0519de75194dbd9f8d51e50ffc75d3"` | FR3.2 — the additive field is returned by the existing endpoint |

## Verdict

**All smoke tests passed.** The bulk import/export feature works end to end against
the real running app, and the existing endpoints remain backward compatible with
the additive `import_id` field.
