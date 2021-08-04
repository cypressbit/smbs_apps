from django.core.exceptions import ValidationError


def validate_phone(phone):
    clean = phone.strip().replace('-', '').replace('(', '').replace(')', '')
    try:
        number = int(clean)
    except ValueError:
        raise ValidationError(u'%s contains non-digits' % phone)
    return number
