export function clampRating(value) {
  const rating = Number(value);
  return Number.isFinite(rating) ? Math.max(0, Math.min(5, Math.round(rating))) : 0;
}

const root = document.querySelector('#star-meter');
const label = document.querySelector('#rating-value');
let record = null;

function render(value) {
  const rating = clampRating(value);
  root.replaceChildren();
  for (let index = 1; index <= 5; index += 1) {
    const star = document.createElement('button');
    star.type = 'button';
    star.className = `star${index <= rating ? ' star--active' : ''}`;
    star.textContent = '★';
    star.setAttribute('aria-label', `Set rating to ${index} stars`);
    star.addEventListener('click', async () => {
      if (!record) return;
      await grist.docApi.applyUserActions([['UpdateRecord', 'Table1', record.id, {Rating: index}]]);
    });
    root.append(star);
  }
  label.textContent = record ? `${rating} of 5 stars` : 'Select a row to rate';
}

if (window.grist) {
  grist.ready({requiredAccess: 'full', columns: [{name: 'Rating', title: 'Rating', type: 'Int'}]});
  grist.onRecord((nextRecord) => {
    record = nextRecord;
    const mapped = grist.mapColumnNames(nextRecord) || nextRecord;
    render(mapped.Rating);
  });
  render(0);
}
