# Click-to-enlarge images in Quarto Reveal.js

## Recommendation for this project

Use Quarto's built-in `lightbox` feature. The installed Quarto is **1.8.25**, so no extension installation or `filters:` entry is required; lightbox became built in with Quarto 1.4 ([first-party extension README](https://github.com/quarto-ext/lightbox#lightbox)). The repository does not currently contain the old `quarto-ext/lightbox` extension under `_extensions/`.

For every eligible block image in a Reveal.js document:

```yaml
---
format: revealjs
lightbox: true
---
```

```markdown
![Alt text](images/example.png)
```

`lightbox: auto` is equivalent to `true`. Automatic matching covers figures and images that form a block by themselves, but not images inline with other content. Exclude an automatically matched image with `.nolightbox` ([Quarto: enabling and disabling lightbox](https://quarto.org/docs/output-formats/html-lightbox-figures.html#enabling-lightbox)):

```markdown
![Do not enlarge](images/example.png){.nolightbox}
```

To opt in only selected images, omit the document-level setting and add `.lightbox` to each selected image. Merely using this class loads the built-in feature ([Quarto: applying lightbox to specific images](https://quarto.org/docs/output-formats/html-lightbox-figures.html#applying-lightbox-to-specific-images)):

```markdown
![Click to enlarge](images/example.png){.lightbox}
```

For a gallery, add the same `group` value to each lightboxed image ([Quarto: galleries](https://quarto.org/docs/output-formats/html-lightbox-figures.html#galleries)):

```markdown
![First](images/first.png){.lightbox group="demo"}

![Second](images/second.png){.lightbox group="demo"}
```

## Images already wrapped in links

An existing Markdown link around an image is **not** converted to a lightbox. This applies in automatic mode and also when `.lightbox` is placed on the nested image: Quarto deliberately stops traversal at a `Link`, because lightbox itself works by wrapping the image in a link. The built-in filter's source comments state both rules ([Quarto CLI 1.8.25 lightbox filter, `Link` handler](https://github.com/quarto-dev/quarto-cli/blob/v1.8.25/src/resources/filters/layout/lightbox.lua#L183-L191), [link creation](https://github.com/quarto-dev/quarto-cli/blob/v1.8.25/src/resources/filters/layout/lightbox.lua#L106-L111)).

Therefore, do not nest or combine a destination link with lightbox markup. To get click-to-enlarge behavior, remove the existing outer link and use the image alone with either automatic matching or `.lightbox`:

```markdown
<!-- Not lightboxed: the existing destination link wins. -->
[![Image](images/example.png){.lightbox}](https://example.com/)

<!-- Lightboxed. -->
![Image](images/example.png){.lightbox}
```

## Reveal.js compatibility

The built-in feature is emitted for JavaScript HTML output, which includes Reveal.js, and official Quarto examples show `format: revealjs` with `lightbox: true`. However, it has a current Reveal.js keyboard interaction bug: while the lightbox is open, navigating among gallery images can also change the underlying slide ([Quarto CLI issue #14842](https://github.com/quarto-dev/quarto-cli/issues/14842)). Thus basic click-to-enlarge works, but gallery keyboard navigation is not fully Reveal-aware in Quarto 1.8.25.

Quarto's documented workaround is to disable Reveal keyboard handling while GLightbox is open, then restore it on close. Put this script in an HTML file loaded through `include-after-body`, so it runs after Quarto defines `lightboxQuarto` ([official issue and maintainer workaround](https://github.com/quarto-dev/quarto-cli/issues/14842)):

```html
<script>
  document.addEventListener('DOMContentLoaded', () => {
    lightboxQuarto.on('open',  () => Reveal.configure({ keyboard: false }));
    lightboxQuarto.on('close', () => Reveal.configure({ keyboard: true }));
  });
</script>
```

This workaround is needed only if Reveal keyboard events conflict with lightbox interaction; it is not an extension installation step.

## Installation rules

- **This project (Quarto 1.8.25):** install nothing. Use the built-in YAML/Markdown above.
- **Quarto 1.4 or newer generally:** install nothing; the former extension explicitly says the feature is built in.
- **Only for Quarto older than 1.4:** install the first-party extension with `quarto add quarto-ext/lightbox`, add `filters: [lightbox]`, and then use its `lightbox` settings/classes ([extension installation and usage](https://github.com/quarto-ext/lightbox#installation)). Upgrading Quarto is preferable to adding that superseded extension.
