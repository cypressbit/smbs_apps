"""HTTP client for the core platform API (site → core), authenticated with CORE_API_TOKEN."""
import requests

from smbs_apps.smbs_managed import conf


TIMEOUT = 10


class CoreAPIError(Exception):
    def __init__(self, status, body):
        super().__init__(f'Core API returned {status}: {body[:200]}')
        self.status = status
        self.body = body


class CoreClient:

    def __init__(self, base_url=None, token=None, session=None):
        self.base_url = (base_url or conf.get('CORE_API_URL')).rstrip('/') + '/'
        self.token = token if token is not None else conf.get('CORE_API_TOKEN')
        self.session = session or requests

    def _request(self, method, path, payload=None):
        response = self.session.request(
            method, self.base_url + path.lstrip('/'), json=payload, timeout=TIMEOUT,
            headers={'Authorization': f'Bearer {self.token}'},
        )
        if not 200 <= response.status_code < 300:
            raise CoreAPIError(response.status_code, response.text)
        return response.json() if response.content else {}

    def get(self, path):
        return self._request('GET', path)

    def post(self, path, payload):
        return self._request('POST', path, payload)

    def published(self, host=None):
        """Tells the core the site published, so it purges the edge cache."""
        return self.post('sites/published/', {'project_id': conf.get('SITE_PROJECT_ID'), 'host': host})

    def ai_assist(self, payload):
        return self.post('ai/assist/', {'project_id': conf.get('SITE_PROJECT_ID'), **payload})

    def report_usage(self, payload):
        return self.post('sites/usage/', {'project_id': conf.get('SITE_PROJECT_ID'), **payload})
