# Grist star meter hosted by Caddy

## Files

- `caddy/star-meter.html` contains the widget markup and styling.
- `caddy/star-meter.js` renders the stars and connects them to Grist.
- Caddy already serves `./caddy` from `/srv`, so the widget URL is:
  `http://127.0.0.1:8000/star-meter.html`.

## Widget integration

Load Grist's plugin API from the Grist origin:

```html
<script src="http://127.0.0.1:8484/grist-plugin-api.js"></script>
```

Declare the required integer column and full access because the widget writes data:

```js
grist.ready({
  requiredAccess: 'full',
  columns: [{name: 'Rating', title: 'Rating', type: 'Int'}],
});
```

React to the selected row and resolve the configured column mapping:

```js
grist.onRecord((record) => {
  const mapped = grist.mapColumnNames(record) || record;
  render(mapped.Rating);
});
```

A star click writes the selected value through a Grist user action:

```js
await grist.docApi.applyUserActions([
  ['UpdateRecord', 'Table1', record.id, {Rating: value}],
]);
```

## Grist setup

1. Add an integer `Rating` column to the source table.
2. Add a **Custom** widget using that table.
3. Select **Custom URL** and enter `http://127.0.0.1:8000/star-meter.html`.
4. Accept the custom-widget security warning.
5. Grant **Full document access**.
6. Map the widget's **Rating** field to the table's `Rating` column.
7. Select a table row; clicking a star updates that row.

## Verification

Use a headless browser for automation. Confirm all three states:

1. A row with `Rating = 3` displays three active stars.
2. Clicking the fifth star changes the cell to `5`.
3. Reloading the document still displays five active stars.

Reference screenshots are in `img/star-meter-04-rating-three.png`, `img/star-meter-05-rating-five.png`, and `img/star-meter-06-final.png`.

## Why Caddy

The in-document Custom Widget Builder runs generated code inside a nested `about:blank` iframe. In this setup, loading the Grist plugin API there was unreliable. A Caddy-hosted page has a stable URL, remains version-controlled, and initializes the plugin API normally.
