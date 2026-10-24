# Encore API endpoints

## `GET /v3/crew`

Returns the current committed crew records visible to the organization in the
single required `X-Org-Id` header. The endpoint is read-only and orders records
by ascending ID.

`X-Org-Id` is required exactly once and must be a positive ASCII decimal 32-bit
integer. Query parameters are optional but strict: `page` defaults to `1`, and
`page_size` defaults to `25`; both are positive ASCII decimal integers and
`page_size` is at most `100`. `page` deliberately has no database-ID/int32
ceiling, so any positive out-of-range page returns an empty `items` array with
HTTP 200. Unknown or repeated query parameters, duplicate organization headers,
and malformed values return HTTP 422 using FastAPI's normal
`{"detail":"..."}` error envelope.

Example:

```http
GET /v3/crew?page=1&page_size=2
X-Org-Id: 7
```

```json
{
  "items": [
    {
      "id": 2,
      "org_id": 7,
      "user_name": "marta.kowalski@harborlight.example",
      "display_name": "M. Kowalski",
      "rate": "31.00",
      "is_lead": true,
      "notes": "head rigger, day calls preferred"
    },
    {
      "id": 6,
      "org_id": 7,
      "user_name": "deshawn.avery@harborlight.example",
      "display_name": "D. Avery",
      "rate": "24.50",
      "is_lead": false,
      "notes": ""
    }
  ],
  "page": 1,
  "page_size": 2,
  "total": 8
}
```

## `GET /v3/crew/{crew_id}`

Returns one current committed crew record from the organization in
`X-Org-Id`. `crew_id` must be a positive ASCII decimal 32-bit integer. Query
parameters are not accepted. Invalid header, path, or query values return HTTP
422; an absent or foreign record returns the common HTTP 404 body
`{"detail":"Crew not found"}`.

Example:

```http
GET /v3/crew/2
X-Org-Id: 7
```

```json
{
  "id": 2,
  "org_id": 7,
  "user_name": "marta.kowalski@harborlight.example",
  "display_name": "M. Kowalski",
  "rate": "31.00",
  "is_lead": true,
  "notes": "head rigger, day calls preferred",
  "preferences_raw": "{\"sms\": \"Y\", \"ui_rows\": 25, \"digest\": \"Y\"}"
}
```

The response has the list fields plus nullable `preferences_raw`, which is the
stored text and may be malformed JSON. `rate` is a nullable two-decimal string,
and `is_lead` is `true` only when the stored value is uppercase `Y`. As on the
list endpoint, `X-Org-Id` must be one positive ASCII decimal 32-bit value. HTTP
422 responses use `{"detail":"..."}` and never expose database diagnostics.

Trailing-slash forms return HTTP 404. Unsupported methods return the normal
HTTP 405 response.

## Legacy compatibility reads

`GET /callboard/crew/list` and `GET /callboard/crew/show` retain the existing
Callboard client contract while migration routing remains unchanged. They use
the same tenant-scoped current-read service as `/v3`, but intentionally preserve
legacy differences: the `X-Org-Id` header accepts its observed loose integer
forms, list paging uses `page` and `per_page` with first-value-wins semantics,
and application errors are HTTP 200 compact JSON bodies with a trailing newline.
`crew_id` on `show` is passed as bound text to PostgreSQL's integer cast, so its
documented historical parser errors, signed forms, and range behavior remain
visible. These are compatibility behavior, not guidance for new clients.

List example:

```http
GET /callboard/crew/list?page=1&per_page=1
X-Org-Id: 7
```

```json
{"data":{"crew":[{"crew_id":2,"crew_name":"marta.kowalski@harborlight.example","display_name":"M. Kowalski","is_lead":"Y","notes":"head rigger, day calls preferred","org":7,"rate":"31.00"}],"page":1,"total":8},"result":"ok","tg_flash":null}
```

Detail example:

```http
GET /callboard/crew/show?crew_id=2
X-Org-Id: 7
```

```json
{"data":{"crew_id":2,"crew_name":"marta.kowalski@harborlight.example","display_name":"M. Kowalski","is_lead":"Y","notes":"head rigger, day calls preferred","org":7,"prefs":"{\"sms\": \"Y\", \"ui_rows\": 25, \"digest\": \"Y\"}","rate":"31.00"},"result":"ok","tg_flash":null}
```

The list omits `prefs`; detail returns the stored raw preference text. Null
notes, preferences, and rates become empty strings, while a null display name
stays JSON `null`. Only stored uppercase `Y` serializes as legacy `"Y"`.
Unknown list query parameters are ignored, duplicate list/show parameters use
their first value, duplicate organization headers fail, and foreign or absent
records both return `{"error":"not found","result":"fail"}`. Trailing or
suffix paths return the legacy 404 JSON failure body; wrong methods and OPTIONS
keep the legacy dispatch behavior, including its validation precedence and
direct 308 double-slash redirect HTML.
