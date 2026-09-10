#!/usr/bin/env python3
"""
True Painting MN - static site builder.

Reads:
  _src/shell.html          shared page shell (header/footer/nav)
  _src/partials/*.html     reusable blocks, inserted with {{PARTIAL:name}}
  _src/faqs.json           question/answer sets, inserted with {{FAQ:setname}}
  _src/pages.json          page list + SEO metadata
  _src/pages/<slug>.html   the unique body content of each page

Writes:
  <slug>.html              one finished page per entry
  sitemap.xml              every page, newest lastmod

Run it with:   python3 build.py
"""

import hashlib
import json
import os
import re
import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "_src")
SITE = "https://truepaintingmn.com"
# Cache-buster: changes whenever style.css changes, so browsers never
# serve a stale stylesheet after a deploy.
def css_version():
    css = os.path.join(ROOT, "assets", "css", "style.css")
    with open(css, "rb") as fh:
        return hashlib.sha1(fh.read()).hexdigest()[:8]

PHONE = "+19524860205"
PHONE_DISPLAY = "(952) 486-0205"
EMAIL = "info@truepaintingmn.com"


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


# --------------------------------------------------------------------------
# Site-wide structured data. Every page carries this so search engines and
# AI assistants always see a consistent picture of the business.
# --------------------------------------------------------------------------
def business_node():
    return {
        "@type": ["HousePainter", "LocalBusiness"],
        "@id": SITE + "/#business",
        "name": "True Painting MN",
        "alternateName": "True Painting",
        "url": SITE + "/",
        "logo": SITE + "/assets/og-image.png",
        "image": SITE + "/assets/og-image.png",
        "telephone": PHONE,
        "email": EMAIL,
        "priceRange": "$$",
        "currenciesAccepted": "USD",
        "paymentAccepted": "Cash, Check, Venmo, Zelle",
        "description": (
            "True Painting MN is an owner-operated interior painting business in "
            "Plymouth, Minnesota. Interior rooms, ceilings, trim and doors, plus the "
            "small drywall patching that comes with a repaint. Free estimates."
        ),
        "founder": {
            "@type": "Person",
            "name": "Alek Silenko",
            "jobTitle": "Owner and Painter",
        },
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Plymouth",
            "addressRegion": "MN",
            "postalCode": "55441",
            "addressCountry": "US",
        },
        "geo": {"@type": "GeoCoordinates", "latitude": 45.0105, "longitude": -93.4555},
        "areaServed": [
            {"@type": "City", "name": n, "addressRegion": "MN"}
            for n in [
                "Plymouth", "Maple Grove", "Minnetonka", "Wayzata", "Golden Valley",
                "Medina", "Osseo", "New Hope", "Crystal", "St. Louis Park",
                "Brooklyn Park", "Hopkins", "Orono", "Long Lake", "Corcoran",
            ]
        ],
        "openingHoursSpecification": [
            {
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "opens": "07:30",
                "closes": "18:00",
            },
            {
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": "Saturday",
                "opens": "08:00",
                "closes": "16:00",
            },
        ],
        "knowsLanguage": "en-US",
        "slogan": "Careful prep. Clean lines. Straight answers.",
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": "Interior painting services",
            "itemListElement": [
                {
                    "@type": "Offer",
                    "itemOffered": {"@type": "Service", "name": n, "url": SITE + u},
                }
                for n, u in [
                    ("Interior House Painting", "/interior-house-painting"),
                    ("Ceiling Painting", "/ceiling-painting"),
                    ("Trim and Door Painting", "/trim-and-door-painting"),
                    ("Drywall Patching and Repair", "/drywall-patching-and-repair"),
                ]
            ],
        },
    }


def website_node():
    return {
        "@type": "WebSite",
        "@id": SITE + "/#website",
        "url": SITE + "/",
        "name": "True Painting MN",
        "publisher": {"@id": SITE + "/#business"},
        "inLanguage": "en-US",
    }


def breadcrumb_node(crumbs, path):
    return {
        "@type": "BreadcrumbList",
        "@id": SITE + path + "#breadcrumbs",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": name,
                "item": SITE + url,
            }
            for i, (name, url) in enumerate(crumbs)
        ],
    }


def faq_node(pairs, path):
    return {
        "@type": "FAQPage",
        "@id": SITE + path + "#faq",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": re.sub(r"<[^>]+>", "", a).strip(),
                },
            }
            for q, a in pairs
        ],
    }


# --------------------------------------------------------------------------
# FAQ rendering: one source of truth for both the visible accordion and the
# FAQPage structured data, so the two can never drift apart.
# --------------------------------------------------------------------------
def render_faq(pairs, open_first=True):
    out = ['<div class="faq-list">']
    for i, (q, a) in enumerate(pairs):
        is_open = " open" if (open_first and i == 0) else ""
        out.append(
            '<details class="faq-item"%s>\n  <summary>%s</summary>\n'
            '  <div class="faq-body">%s</div>\n</details>' % (is_open, q, a)
        )
    out.append("</div>")
    return "\n".join(out)


def render_breadcrumbs(crumbs):
    if not crumbs:
        return ""
    items = []
    for i, (name, url) in enumerate(crumbs):
        if i == len(crumbs) - 1:
            items.append('<li aria-current="page">%s</li>' % name)
        else:
            items.append('<li><a href="%s">%s</a></li>' % (url, name))
    return (
        '<nav class="breadcrumbs" aria-label="Breadcrumb"><ol>%s</ol></nav>'
        % "".join(items)
    )


def main():
    shell = read(os.path.join(SRC, "shell.html"))
    pages = json.loads(read(os.path.join(SRC, "pages.json")))
    faqs = json.loads(read(os.path.join(SRC, "faqs.json")))

    partials = {}
    pdir = os.path.join(SRC, "partials")
    if os.path.isdir(pdir):
        for fn in os.listdir(pdir):
            if fn.endswith(".html"):
                partials[fn[:-5]] = read(os.path.join(pdir, fn))

    cssver = css_version()
    today = datetime.date.today().isoformat()
    built = []

    for page in pages:
        slug = page["slug"]
        path = page["path"]
        body = read(os.path.join(SRC, "pages", slug + ".html"))

        # Expand partials (they may themselves reference FAQ sets, so do these first).
        for name, html in partials.items():
            body = body.replace("{{PARTIAL:" + name + "}}", html)

        # Expand FAQ sets and collect the Q&A used on this page for schema.
        used_faqs = []
        for name in re.findall(r"\{\{FAQ:([a-z0-9_-]+)\}\}", body):
            pairs = [(item["q"], item["a"]) for item in faqs[name]]
            used_faqs.extend(pairs)
            body = body.replace("{{FAQ:" + name + "}}", render_faq(pairs))

        crumbs = [tuple(c) for c in page.get("breadcrumb", [])]
        body = body.replace("{{BREADCRUMBS}}", render_breadcrumbs(crumbs))

        # ---- structured data ----
        graph = [business_node(), website_node()]
        graph.append(
            {
                "@type": page.get("pagetype", "WebPage"),
                "@id": SITE + path + "#webpage",
                "url": SITE + path,
                "name": page["title"],
                "description": page["description"],
                "isPartOf": {"@id": SITE + "/#website"},
                "about": {"@id": SITE + "/#business"},
                "inLanguage": "en-US",
            }
        )
        if crumbs:
            graph.append(breadcrumb_node(crumbs, path))
        # Only one page should carry FAQPage markup for a given set of questions,
        # otherwise Google sees the same rich result duplicated across the site.
        if used_faqs and page.get("faqschema", True):
            graph.append(faq_node(used_faqs, path))
        for extra in page.get("schema", []):
            graph.append(extra)

        schema = json.dumps(
            {"@context": "https://schema.org", "@graph": graph},
            indent=2,
            ensure_ascii=False,
        )

        html = shell
        html = html.replace("{{BODY}}", body)
        html = html.replace("{{TITLE}}", page["title"])
        html = html.replace("{{DESCRIPTION}}", page["description"])
        html = html.replace("{{PATH}}", path)
        html = html.replace("{{OGTYPE}}", page.get("ogtype", "website"))
        html = html.replace("{{CSSVER}}", cssver)
        html = html.replace("{{SCHEMA}}", schema)
        html = html.replace("{{HEADEXTRA}}", page.get("headextra", ""))
        html = html.replace("{{BODYEXTRA}}", page.get("bodyextra", ""))

        # Mark the current nav item.
        for key in ["services", "areas", "pricing", "about", "faq", "contact"]:
            token = "{{NAV_" + key.upper() + "}}"
            mark = ' aria-current="page"' if page.get("nav") == key else ""
            html = html.replace(token, mark)

        write(os.path.join(ROOT, slug + ".html"), html)
        if page.get("index", True):
            built.append((path, page.get("priority", "0.7")))

    # ---- sitemap ----
    urls = "\n".join(
        "  <url>\n"
        "    <loc>%s%s</loc>\n"
        "    <lastmod>%s</lastmod>\n"
        "    <changefreq>monthly</changefreq>\n"
        "    <priority>%s</priority>\n"
        "  </url>" % (SITE, p, today, pri)
        for p, pri in built
    )
    write(
        os.path.join(ROOT, "sitemap.xml"),
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + urls
        + "\n</urlset>\n",
    )

    print("Built %d pages + sitemap.xml" % len(pages))


if __name__ == "__main__":
    main()
