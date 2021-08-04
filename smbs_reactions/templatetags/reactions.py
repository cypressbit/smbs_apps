from django import template


register = template.Library()


@register.simple_tag
def has_reacted(model, user):
    return model.reactions.filter(user=user).exists()
