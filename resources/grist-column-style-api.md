# Grist column styles through the REST and Python APIs

## Answer

**Yes.** Grist's REST API can change a column's default cell and header style by patching the column metadata field **`fields.widgetOptions`**. `widgetOptions` is not a JSON object at the REST boundary: it is a **string containing serialized JSON**. There is no separate column `style` field.

The official columns endpoint is `PATCH /api/docs/{docId}/tables/{tableId}/columns`; each item is identified by column `id`, and changed metadata goes under `fields`. The official add-column example also demonstrates that `widgetOptions` is a JSON-encoded string rather than a nested object ([REST `modifyColumns`](https://support.getgrist.com/api/#tag/columns/operation/modifyColumns), [official `widgetOptions` example](https://support.getgrist.com/api/#tag/columns/operation/addColumns)). The upstream route resolves the column ID and updates its `_grist_Tables_column` metadata record ([`DocApi.ts`, pinned lines 770–790](https://github.com/gristlabs/grist-core/blob/2c46edd39c7bbf6c59cef0cd48a0ab92e2500a9c/app/server/lib/DocApi.ts#L770-L790)).

## Supported style values

The current upstream style interfaces define these option keys ([`Styles.ts`, pinned lines 1–17](https://github.com/gristlabs/grist-core/blob/2c46edd39c7bbf6c59cef0cd48a0ab92e2500a9c/app/common/Styles.ts#L1-L17)):

| Scope | `widgetOptions` keys | Value type |
|---|---|---|
| Cell | `textColor`, `fillColor` | string (normally a CSS/hex color such as `"#FFFFFF"`) |
| Cell | `fontBold`, `fontUnderline`, `fontItalic`, `fontStrikethrough` | boolean |
| Column header | `headerTextColor`, `headerFillColor` | string |
| Column header | `headerFontBold`, `headerFontUnderline`, `headerFontItalic`, `headerFontStrikethrough` | boolean |

Grist maps those exact properties out of parsed `widgetOptions`, then writes style changes back into that JSON object ([`ViewFieldRec.ts`, pinned lines 239–295](https://github.com/gristlabs/grist-core/blob/2c46edd39c7bbf6c59cef0cd48a0ab92e2500a9c/app/client/models/entities/ViewFieldRec.ts#L239-L295)). Adjacent display options include `alignment` (`"left"`, `"center"`, or `"right"`) and `wrap` (boolean); these are presentation options but are not members of the core `Style`/`HeaderStyle` interfaces ([`WidgetOptions.ts`, pinned lines 1–11](https://github.com/gristlabs/grist-core/blob/2c46edd39c7bbf6c59cef0cd48a0ab92e2500a9c/app/common/WidgetOptions.ts#L1-L11), [`ViewFieldRec.ts`, pinned lines 250–268](https://github.com/gristlabs/grist-core/blob/2c46edd39c7bbf6c59cef0cd48a0ab92e2500a9c/app/client/models/entities/ViewFieldRec.ts#L250-L268)).

`widgetOptions` also holds type-specific settings (for example number/date formatting, choices, and widgets), so a PATCH replaces the whole serialized metadata value rather than deep-merging its inner JSON. Read the current column, parse its `widgetOptions`, merge the desired keys locally, and serialize the complete object back to avoid erasing unrelated options.

## REST request

This request sets the default body style and header style for column `Name`:

```bash
curl -X PATCH \
  -H "Authorization: Bearer $GRIST_API_KEY" \
  -H "Content-Type: application/json" \
  --data '{
    "columns": [{
      "id": "Name",
      "fields": {
        "widgetOptions": "{\"textColor\":\"#FFFFFF\",\"fillColor\":\"#2563EB\",\"fontBold\":true,\"headerTextColor\":\"#FFFFFF\",\"headerFillColor\":\"#1E3A8A\",\"headerFontBold\":true}"
      }
    }]
  }' \
  "https://docs.getgrist.com/api/docs/$DOC_ID/tables/People/columns"
```

Use the Grist host that owns the document. The official usage guide documents bearer authentication and JSON request bodies ([REST API usage](https://support.getgrist.com/rest-api/#usage)).

## Official Python client

**Supported through the client's generic REST call, not through a dedicated style or update-columns method.** Grist identifies `grist_api` as its maintained Python client ([official API-client list](https://support.getgrist.com/rest-api/#api-clients)). Its `columns(table_name)` convenience method only performs GET, while `call(url, json_data, method)` forwards the chosen HTTP method to the document API ([pinned `columns`](https://github.com/gristlabs/py_grist_api/blob/7ff12056927104764226dbd200d54d53d61429dd/grist_api/grist_api.py#L144-L154), [pinned generic REST call](https://github.com/gristlabs/py_grist_api/blob/7ff12056927104764226dbd200d54d53d61429dd/grist_api/grist_api.py#L78-L125)). Therefore Python can invoke the same REST PATCH:

```python
import json
from grist_api import GristDocAPI

api = GristDocAPI(DOC_ID, server="https://docs.getgrist.com")

column = next(c for c in api.columns("People")["columns"] if c["id"] == "Name")
options = json.loads(column["fields"].get("widgetOptions") or "{}")
options.update({
    "textColor": "#FFFFFF",
    "fillColor": "#2563EB",
    "fontBold": True,
    "headerTextColor": "#FFFFFF",
    "headerFillColor": "#1E3A8A",
    "headerFontBold": True,
})

api.call(
    "tables/People/columns",
    json_data={
        "columns": [{
            "id": "Name",
            "fields": {"widgetOptions": json.dumps(options)},
        }],
    },
    method="PATCH",
)
```

The important value-shape requirement is the second serialization: `fields.widgetOptions` must receive `json.dumps(options)`, **not** `options` itself.

## Conditional-formatting API status

**Partially available in practice, but not supported end to end by the documented public contract.** There is no dedicated conditional-formatting endpoint in the [official REST API reference](https://support.getgrist.com/api/); the documented conditional-formatting page describes only the [UI workflow and formula behavior](https://support.getgrist.com/conditional-formatting/).

The documented [columns PATCH operation](https://support.getgrist.com/api/#tag/columns/operation/modifyColumns) accepts an `id` plus a generic `fields` object, and the [add-column example](https://support.getgrist.com/api/#tag/columns/operation/addColumns) demonstrates `widgetOptions` as JSON serialized into a string. The underlying API type likewise leaves `fields` open-ended ([`RecordWithStringId`, pinned lines 32–35](https://github.com/gristlabs/grist-core/blob/2c46edd39c7bbf6c59cef0cd48a0ab92e2500a9c/app/plugin/DocApiTypes.ts#L32-L35), [`ColumnsPatch` and `ColumnMetadata`, pinned lines 113–141](https://github.com/gristlabs/grist-core/blob/2c46edd39c7bbf6c59cef0cd48a0ab92e2500a9c/app/plugin/DocApiTypes.ts#L113-L141)). However, the OpenAPI documentation defines neither a conditional-formatting `rules` field nor the `widgetOptions.rulesOptions` payload, RefList encoding, hidden formula-column lifecycle, or ordering invariant. Therefore the columns endpoint alone does not document a complete operation for creating, editing, reordering, or deleting a rule.

Grist also documents [`POST /api/docs/{docId}/apply`](https://support.getgrist.com/api/#tag/docs/operation/applyUserActions), but explicitly calls it a low-level endpoint using Grist's internal action format. Its request schema is only an array of arrays and its listed common actions do not include `AddEmptyRule`. The route passes those arrays straight to `activeDoc.applyUserActions` ([`DocApi.ts`, pinned lines 207–211](https://github.com/gristlabs/grist-core/blob/2c46edd39c7bbf6c59cef0cd48a0ab92e2500a9c/app/server/lib/DocApi.ts#L207-L211)); even the source `UserAction` type is just a broad array rather than a conditional-formatting contract ([`DocActions.ts`, pinned line 198](https://github.com/gristlabs/grist-core/blob/2c46edd39c7bbf6c59cef0cd48a0ab92e2500a9c/app/common/DocActions.ts#L198)). Thus the transport endpoint is public, but no complete conditional-formatting operation can be constructed from documented action contracts alone.

The missing protocol is visible only in internal source. A rule is a hidden formula column referenced by the owner's `rules` RefList, while its same-position style lives in `widgetOptions.rulesOptions` ([`RuleOwner.ts`, pinned lines 6–24](https://github.com/gristlabs/grist-core/blob/2c46edd39c7bbf6c59cef0cd48a0ab92e2500a9c/app/client/models/RuleOwner.ts#L6-L24), [`ViewFieldRec.ts`, pinned lines 299–325](https://github.com/gristlabs/grist-core/blob/2c46edd39c7bbf6c59cef0cd48a0ab92e2500a9c/app/client/models/entities/ViewFieldRec.ts#L299-L325)). The internal schema exposes `rules` on columns, view fields, and view sections ([column metadata, pinned lines 31–49](https://github.com/gristlabs/grist-core/blob/2c46edd39c7bbf6c59cef0cd48a0ab92e2500a9c/app/common/schema.ts#L31-L49), [view metadata, pinned lines 108–140](https://github.com/gristlabs/grist-core/blob/2c46edd39c7bbf6c59cef0cd48a0ab92e2500a9c/app/common/schema.ts#L108-L140)). The UI creates one through undocumented `AddEmptyRule` ([client call, pinned lines 313–325](https://github.com/gristlabs/grist-core/blob/2c46edd39c7bbf6c59cef0cd48a0ab92e2500a9c/app/client/models/entities/ViewFieldRec.ts#L313-L325), [server implementation, pinned lines 2027–2060](https://github.com/gristlabs/grist-core/blob/2c46edd39c7bbf6c59cef0cd48a0ab92e2500a9c/sandbox/grist/useractions.py#L2027-L2060)), and removal coordinates a style-array update with `RemoveColumn` ([`RuleOwner.ts`, pinned lines 27–43](https://github.com/gristlabs/grist-core/blob/2c46edd39c7bbf6c59cef0cd48a0ab92e2500a9c/app/client/models/RuleOwner.ts#L27-L43)).

**Safest recommendation:** use the documented UI for conditional formatting. Use REST for the documented base `widgetOptions` styling above. If automation is unavoidable, pin the Grist server version and treat `apply` plus `AddEmptyRule`/metadata updates as an unsupported internal integration, with end-to-end tests that verify rule/style alignment and distinguish column rules from view-field or whole-row rules.

## Scope and limitations

- **Column metadata, not per-cell formatting.** This changes the column's default display options. It does not attach a style to an individual `(row, column)` cell, and the documented records endpoints do not define a per-cell style field. The official conditional-formatting documentation likewise describes formula-driven styles for cells in a column or whole rows, rather than arbitrary static formatting on one record ([Conditional formatting](https://support.getgrist.com/conditional-formatting/)).
- **A view-specific override can hide the column-level result.** A view field uses the column's `widgetOptions` only when the field's own `widgetOptions` is empty; otherwise the field-level value wins ([`ViewFieldRec.ts`, pinned lines 191–201](https://github.com/gristlabs/grist-core/blob/2c46edd39c7bbf6c59cef0cd48a0ab92e2500a9c/app/client/models/entities/ViewFieldRec.ts#L191-L201)). `PATCH /columns` updates column metadata, not a particular `_grist_Views_section_field`, so an existing view-specific override may need to be removed or updated through lower-level document actions rather than this documented column endpoint.
- **Conditional formatting is separate.** Core represents it with a `rules` list referencing rule/formula columns and an ordered `rulesOptions` array of styles inside `widgetOptions`; the two must stay aligned ([`ViewFieldRec.ts`, pinned lines 299–325](https://github.com/gristlabs/grist-core/blob/2c46edd39c7bbf6c59cef0cd48a0ab92e2500a9c/app/client/models/entities/ViewFieldRec.ts#L299-L325)). Setting the base style keys above neither creates nor edits conditional rules.
- **Choice colors are not general per-cell formatting.** The official `widgetOptions` example uses `choiceOptions` to style a particular Choice value; all cells displaying that choice inherit it ([official add-column example](https://support.getgrist.com/api/#tag/columns/operation/addColumns)).
