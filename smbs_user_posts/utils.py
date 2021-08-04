import requests
import extraction


USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36")


def get_extraction(url):
    headers = {'User-Agent': USER_AGENT}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    html = response.text
    extracted = extraction.Extractor().extract(html, source_url=url)
    return extracted
