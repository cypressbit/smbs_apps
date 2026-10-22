"""
Public API for document pages: saving drafts, publishing, rollback and
preview tokens. Editors, the AI pipeline and management commands go through
these functions rather than writing Page/PageRevision fields directly.
"""
from django.core import signing
from django.db import transaction
from django.db.models import F, Max

from smbs_apps.smbs_pages import documents


PREVIEW_SALT = 'smbs_pages.preview'
PREVIEW_MAX_AGE = 60 * 60 * 24  # one day


class DraftConflict(Exception):
    """The draft changed since the caller loaded it (another tab or editor)."""

    def __init__(self, current_version):
        super().__init__(f'Draft is at version {current_version}.')
        self.current_version = current_version


def save_draft(page, document, *, expected_version=None, user=None, allow_staff_widgets=False):
    """
    Validates `document` and stores it as the page's draft (publishing is a
    separate step, see publish_page). If
    `expected_version` is given and the stored draft has moved on, raises
    DraftConflict. Returns the new draft version.
    """
    from smbs_apps.smbs_pages.models import Page

    cleaned, _ = documents.validate(document, assign_ids=True, allow_staff_widgets=allow_staff_widgets)
    with transaction.atomic():
        current = Page.objects.select_for_update().only('draft_version').get(pk=page.pk)
        if expected_version is not None and current.draft_version != expected_version:
            raise DraftConflict(current.draft_version)
        # The content mode is left alone: a legacy page keeps serving its old
        # tree until the draft is published (preview links show the draft).
        Page.objects.filter(pk=page.pk).update(draft=cleaned, draft_version=F('draft_version') + 1)
    page.refresh_from_db(fields=['draft', 'draft_version'])
    return page.draft_version


@transaction.atomic
def publish_page(page, *, user=None, note=''):
    """Snapshots the current draft as a new revision and makes it the published one."""
    from smbs_apps.smbs_pages.models import Page, PageRevision

    page = Page.objects.select_for_update().get(pk=page.pk)
    number = (page.revisions.aggregate(last=Max('number'))['last'] or 0) + 1
    revision = PageRevision.objects.create(page=page, number=number, document=page.draft,
                                           note=note[:255], created_by=user)
    page.published_revision = revision
    page.content_mode = Page.ContentMode.DOCUMENT
    page.save(update_fields=['published_revision', 'content_mode', 'updated'])
    return revision


@transaction.atomic
def restore_revision(page, number, *, user=None):
    """Rollback: publishes revision `number` again (as a new revision) and makes it the draft too."""
    from smbs_apps.smbs_pages.models import Page

    page = Page.objects.select_for_update().get(pk=page.pk)
    revision = page.revisions.get(number=number)
    Page.objects.filter(pk=page.pk).update(draft=revision.document, draft_version=F('draft_version') + 1)
    page.refresh_from_db()
    return publish_page(page, user=user, note=f'Restored revision {number}')


def unpublish_page(page):
    page.published_revision = None
    page.save(update_fields=['published_revision', 'updated'])


def publish_chrome(chrome):
    chrome.published = chrome.draft
    chrome.save(update_fields=['published', 'updated'])


def preview_token(page):
    """A signed token that lets anyone holding it see the page's draft for a day."""
    return signing.dumps({'page': page.pk}, salt=PREVIEW_SALT, compress=True)


def check_preview_token(token, page):
    try:
        data = signing.loads(token, salt=PREVIEW_SALT, max_age=PREVIEW_MAX_AGE)
    except signing.BadSignature:
        return False
    return data.get('page') == page.pk
