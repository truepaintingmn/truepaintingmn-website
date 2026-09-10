# truepaintingmn.com

The website for True Painting MN — interior painting in Plymouth, Minnesota.

Plain static HTML. No frameworks, no build tools to install. Cloudflare Pages
serves whatever is on the `main` branch, so pushing here publishes the site.

## Editing the site

Do **not** edit the `.html` files in the root — they are generated and your
changes will be wiped out the next time the site is built. Edit these instead:

| What you want to change | File to edit |
| --- | --- |
| The words on a page | `_src/pages/<page-name>.html` |
| A question or answer | `_src/faqs.json` |
| Page title / Google description | `_src/pages.json` |
| The menu, header or footer | `_src/shell.html` |
| The estimate form | `_src/partials/form.html` |
| Colors, fonts, spacing | `assets/css/style.css` |
| Your prices in the calculator | the six numbers at the top of the script in `_src/pages/pricing.html` |

Then rebuild:

```
python3 build.py
```

That regenerates every page in the root plus `sitemap.xml`. Commit and push,
and Cloudflare publishes it within a minute or two.

## Adding a new page

1. Write the body content in `_src/pages/your-page.html`
2. Add an entry to `_src/pages.json` (copy an existing one and change it)
3. Run `python3 build.py`

The sitemap, breadcrumbs, structured data and menu highlighting are handled
for you.

## Files Cloudflare cares about

- `_redirects` — sends www to the bare domain
- `_headers` — security headers and long cache lifetimes for `/assets/`
- `404.html` — the not-found page
- `robots.txt` / `sitemap.xml` — for search engines
