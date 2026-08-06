/*
 * Cookie consent gate, shared by every site built on smbs_base.
 *
 * Any analytics/tracking snippet added to a site's BaseSettings.global_metadata
 * (rendered into <head> by smbs_apps.smbs_base.context_processors.base) must be
 * neutered so it can't run before the visitor has chosen. Do that by writing it
 * as:
 *
 *   <script type="text/plain" data-consent="analytics" src="https://...">
 *   <script type="text/plain" data-consent="analytics">gtag('config', '...');</script>
 *
 * type="text/plain" stops the browser from executing it. Once the visitor
 * accepts, activateGatedScripts() below clones each placeholder into a real
 * <script> tag (copying every attribute except "type") so it actually runs.
 * Nothing here executes anything on decline or before a choice is made.
 */
(function () {
    var COOKIE_NAME = 'smbs_cookie_consent';
    var COOKIE_DAYS = 365;

    function getCookie(name) {
        var match = document.cookie.match('(?:^|; )' + name + '=([^;]*)');
        return match ? decodeURIComponent(match[1]) : null;
    }

    function setCookie(name, value, days) {
        var expires = new Date(Date.now() + days * 24 * 60 * 60 * 1000).toUTCString();
        var secure = window.location.protocol === 'https:' ? '; Secure' : '';
        document.cookie = name + '=' + encodeURIComponent(value) +
            '; expires=' + expires + '; path=/; SameSite=Lax' + secure;
    }

    function activateGatedScripts() {
        var placeholders = document.querySelectorAll('script[type="text/plain"][data-consent="analytics"]');
        placeholders.forEach(function (placeholder) {
            var script = document.createElement('script');
            Array.prototype.forEach.call(placeholder.attributes, function (attr) {
                if (attr.name !== 'type') {
                    script.setAttribute(attr.name, attr.value);
                }
            });
            script.text = placeholder.text;
            placeholder.parentNode.replaceChild(script, placeholder);
        });
    }

    function hideBanner() {
        var banner = document.getElementById('smbs-cookie-consent');
        if (banner) {
            banner.setAttribute('hidden', '');
        }
    }

    function setStatus(status) {
        setCookie(COOKIE_NAME, status, COOKIE_DAYS);
        hideBanner();
        if (status === 'accepted') {
            activateGatedScripts();
        }
        document.dispatchEvent(new CustomEvent('smbs:consent', { detail: { status: status } }));
    }

    window.smbsConsent = {
        status: function () {
            return getCookie(COOKIE_NAME);
        },
        accept: function () {
            setStatus('accepted');
        },
        decline: function () {
            setStatus('declined');
        }
    };

    document.addEventListener('DOMContentLoaded', function () {
        var existing = getCookie(COOKIE_NAME);

        if (existing === 'accepted') {
            activateGatedScripts();
            return;
        }
        if (existing === 'declined') {
            return;
        }

        var banner = document.getElementById('smbs-cookie-consent');
        if (!banner) {
            return;
        }
        banner.removeAttribute('hidden');

        var acceptBtn = document.getElementById('smbs-cookie-accept');
        var declineBtn = document.getElementById('smbs-cookie-decline');
        if (acceptBtn) {
            acceptBtn.addEventListener('click', window.smbsConsent.accept);
        }
        if (declineBtn) {
            declineBtn.addEventListener('click', window.smbsConsent.decline);
        }
    });
})();
