# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`smbs_apps` is a **Django app library** — a collection of reusable Django applications that get installed into a separate host Django project. This repo contains only apps; there is no `manage.py`, `settings.py`, or `urls.py` here. All Django management commands (`migrate`, `runserver`, `test`, etc.) must be run from the host project that installs these apps.

## Architecture

### App layout

Each directory at the root is a standalone Django app. Apps are imported as `smbs_apps.<app_name>` (e.g. `smbs_apps.smbs_blog`). The dependency graph flows from `smbs_base` outward:

- **`smbs_base`** — foundation; all other apps depend on it. Provides abstract base models (`SiteModel`, `TimestampModel`, `SettingsModel`, `BaseMetadata`), base views (`SMBSView`, `SMBSTemplateView`, `SMBSObjectMetadataView`), a context processor that injects `BaseSettings` into every template, and a custom SMTP email backend.
- **`smbs_pages`** — CMS engine. Pages have a `Container → Row → Column → Widget` content tree. Widgets are discovered at startup by scanning every installed app's `smbs_widgets/` package (see `smbs_pages/widgets.py`). Pages support up to 3 levels of nesting (grand_parent/parent/slug).
- **`smbs_blog`** — blog with built-in SEO checks enforced in `Post.clean()`. Uses `django-taggit` for tags and `smbs_comments_tree` for threaded comments.
- **`smbs_shop`** — e-commerce with PayPal and Stripe integrations (`smbs_shop/integrations/`), cart/order/payment models, and `smbs_custom_attrs` for generic product attributes.
- **`smbs_inventory`** — product catalog (no cart/payment); simpler than `smbs_shop`.
- **`smbs_comments_tree`** — abstract `Comment` model (MPTT tree, bleach-sanitized) used by blog, Q&A, and user posts.
- **`smbs_reactions`** — `ReactionMixin` and `Reaction` model; mixed into comments and other content types.
- **`smbs_accounts`** — user registration/auth + a `sync_mailchimp` management command.
- **`smbs_social`** — social sharing links via context processor.
- **`smbs_alerts`** — site-wide banner alerts.
- **`smbs_qa`** — Q&A forum.
- **`smbs_user_posts`** — user-generated posts.
- **`smbs_profile`** — user profile pages.
- **`smbs_forms`** — generic form builder with contact and address widgets.
- **`smbs_newsletter`** — newsletter subscription.
- **`smbs_cities_light`** — city/country data with a `get_city_data` management command.
- **`smbs_cart`** — legacy cart (PayPal-only); `smbs_shop` is the newer replacement.
- **`smbs_contact`** — basic contact form.
- **`smbs_custom_attrs`** — generic `CustomAttribute` model (content-type based); used by `smbs_shop`.

### Key patterns

**Settings singleton** — every app with configurable settings extends `SettingsModel` (which itself extends `SiteModel`). Only one settings instance is allowed per Django `Site`. Retrieve with `MySettings.get_object()`.

**Widget system** — to add a widget type, create `<app>/smbs_widgets/<widget_name>.py` with a `Widget` class that has a `NAME` class attribute and a `render()` method. The `smbs_pages` widget discovery runs at import time on `find_widgets()`.

**Multi-site** — all content models include `SiteModel` (a FK to `django.contrib.sites.models.Site`), so the same database can serve multiple sites.

**SEO metadata** — `ObjectMetadata` (for content objects) and `ViewMetadata` (for named views) are both abstract-based. Views inherit from `SMBSObjectMetadataView` to inject `metadata` into template context automatically.

**Page depth limit** — `Page.save()` enforces a maximum nesting depth of 3 levels.

## Required context processors

Add to `TEMPLATES[0]['OPTIONS']['context_processors']` in the host project:

```python
'smbs_apps.smbs_base.context_processors.base',
'smbs_apps.smbs_pages.context_processors.get_pages',
'smbs_apps.smbs_inventory.context_processors.inventory',   # if using smbs_inventory
```

## External dependencies

- `django-taggit` — tags on `Post`, `Item`, `ShopItem`
- `django-mptt` — tree structure for `Comment`
- `bleach` — HTML sanitization in comments
- `Pillow` — image processing in `smbs_shop` (generates placeholder images)
- `django-imagekit` / `versatileimagefield` — image generators (`imagegenerators.py` files)
- `pyyaml` — template YAML parsing in `smbs_pages`
- PostgreSQL — required; uses `JSONField` and `ArrayField` from `django.contrib.postgres`
