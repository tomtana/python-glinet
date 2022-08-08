import requests

url = "https://dev.gl-inet.cn/docs/api_docs_api/"


def get_api_description(url):
    resp = requests.get(url)
    return resp.json()
