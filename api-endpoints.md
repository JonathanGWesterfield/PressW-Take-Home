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
HTTP 405 response. These modern contracts intentionally differ from the
legacy-compatible `/callboard/...` wrappers, which will be implemented in the
next slice.
