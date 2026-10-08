def oauth(request):
    """Lets shared templates (smbs_accounts/login.html, signup.html) show the
    "Continue with Google" button only on sites that actually install this
    app and register this processor — same shape as smbs_base's `base`
    context processor. A site that doesn't register it never gets this
    variable, so `{% if google_oauth_enabled %}` is false and the
    `{% url 'smbs_oauth:google_login' %}` tag inside never executes."""
    return {'google_oauth_enabled': True}
