# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`smbs_apps` is a **Django app library** — a collection of reusable Django applications that get installed into a separate host Django project. This repo contains only apps; there is no `manage.py`, `settings.py`, or `urls.py` here. All Django management commands (`migrate`, `runserver`, `test`, etc.) must be run from the host project that installs these apps.

## Architecture

### App layout

Each directory at the root is a standalone Django app. Apps are imported as `smbs_apps.<app_name>` (e.g. `smbs_apps.smbs_blog`). The dependency graph flows from `smbs_base` outward:

- **`smbs_base`** — foundation; all other apps depend on it. Provides abstract base models (`SiteModel`, `TimestampModel`, `SettingsModel`, `BaseMetadata`), base views (`SMBSView`, `SMBSTemplateView`, `SMBSObjectMetadataView`), a context processor that injects `BaseSettings` into every template, and a custom SMTP email backend.
- **`smbs_pages`** — CMS engine. Pages support up to 3 levels of nesting (grand_parent/parent/slug) and have one of two content modes (`Page.content_mode`):
  - `legacy` (default): the relational `Container → Row → Column → Widget` tree, rendered by `page_detail.html`. Unchanged for existing sites.
  - `document`: a JSON page document (`documents.py`) with `draft`, immutable `PageRevision`s and `published_revision`; rendered by `rendering.py`. Widgets in documents are **schema widgets** (`widgets.BaseWidget` + a `fields.Schema` of props), keyed by a stable `key`. `SiteChrome` holds the site header/footer as documents. A **SiteSpec** (whole site as JSON) is applied with `documents.materialize()` and read back with `documents.export()`; edits use `documents.apply_ops()`. Go through `services.py` to save drafts, publish, roll back and make preview tokens. `manage.py pages_convert` turns legacy trees into document drafts.
- **`smbs_blog`** — blog with built-in SEO checks enforced in `Post.clean()`. Uses `django-taggit` for tags and `smbs_comments_tree` for threaded comments.
- **`smbs_shop`** — e-commerce with PayPal and Stripe integrations (`smbs_shop/integrations/`), cart/order/payment models, and `smbs_custom_attrs` for generic product attributes.
- **`smbs_inventory`** — product catalog (no cart/payment); simpler than `smbs_shop`.
- **`smbs_comments_tree`** — abstract `Comment` model (MPTT tree, bleach-sanitized) used by blog, Q&A, and user posts.
- **`smbs_reactions`** — `ReactionMixin` and `Reaction` model; mixed into comments and other content types.
- **`smbs_accounts`** — user registration/auth + a `sync_mailchimp` management command.
- **`smbs_oauth`** — "Sign in with Google" (OAuth 2.0 Authorization Code flow via plain `requests`, no third-party auth library). Adds a `google_oauth_enabled` context processor so `smbs_accounts`' login/signup templates show the button only on sites that install and register this app; client id/secret are admin-editable (`GoogleOAuthSettings`, same singleton pattern as `smbs_base.SettingsModel`).
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
- **`smbs_managed`** — the contract between a Digitally Boosted site installation and its core platform: Ed25519 JWT single sign-on (`/manage/sso/`), the token-protected SiteSpec `materialize` and `status` endpoints, health check / edge cache-header / staff-only-admin middleware, and `CoreClient`. Only Digitally Boosted sites install it (needs the `managed` extra).
- **`smbs_custom_attrs`** — generic `CustomAttribute` model (content-type based); used by `smbs_shop`.

### Key patterns

**Settings singleton** — every app with configurable settings extends `SettingsModel` (which itself extends `SiteModel`). Only one settings instance is allowed per Django `Site`. Retrieve with `MySettings.get_object()`.

**Widget system** — widgets live in `<app>/smbs_widgets/<module>.py` and are discovered lazily (on first use) from every installed app.
- *Schema widgets* (page documents): subclass `smbs_pages.widgets.BaseWidget`; set a stable `key` (stored in documents — never rename it), `NAME`, `category`, `icon` (Bootstrap Icons name), `ai_hint`, `template`, and a nested `Props(fields.Schema)`. **Defaults must validate**, so a freshly inserted widget is valid. Render text escaped; only `fields.RichText` values (sanitized with nh3) may use `|safe`.
- *Legacy widgets* (relational tree): a module-level `Widget` class with `NAME` and `render()`; `Widget.type` stores the module path. In documents they render through `LegacyWidgetAdapter` (staff only).

**Multi-site** — all content models include `SiteModel` (a FK to `django.contrib.sites.models.Site`), so the same database can serve multiple sites.

**SEO metadata** — `ObjectMetadata` (for content objects) and `ViewMetadata` (for named views) are both abstract-based. Views inherit from `SMBSObjectMetadataView` to inject `metadata` into template context automatically.

**Page depth limit** — `Page.save()` enforces a maximum nesting depth of 3 levels.

**Migrations must not depend on the host** — every app's `AppConfig` sets `default_auto_field` to whatever its migrations use (`BigAutoField` for `smbs_pages`, `AutoField` for the rest), and choices derived from settings or installed apps are **callables** (e.g. `smbs_blog.models.language_choices`, `smbs_pages.widgets.legacy_widget_choices`) so migrations store a reference, not a snapshot. `makemigrations` in any host must report no changes for smbs apps; if it doesn't, fix it here rather than committing a host-specific migration.

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
