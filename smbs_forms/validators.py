from django.core.exceptions import ValidationError


def validate_phone(phone):
    """Accepts digits with common separators: "(555) 123-4567", "+1 555.123.4567"."""
    clean = phone.strip()
    if clean.startswith('+'):
        clean = clean[1:]
    for separator in ' -().':
        clean = clean.replace(separator, '')
    if not clean.isdigit():
        raise ValidationError(u'%s contains non-digits' % phone)
    return int(clean)
