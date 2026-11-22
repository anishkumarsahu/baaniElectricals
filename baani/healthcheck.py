"""Probe the local web server without relying on the host network or a proxy."""
import json
import os
import urllib.request


def main():
    hosts = [host.strip() for host in os.environ.get('ALLOWED_HOSTS', 'localhost').split(',') if host.strip()]
    host = hosts[0] if hosts else 'localhost'
    host = 'localhost' if host == '*' else host.lstrip('.')
    request = urllib.request.Request('http://127.0.0.1:8004/healthz', headers={'Host': host})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=5) as response:
        if response.status != 200 or json.load(response) != {'status': 'ok'}:
            raise SystemExit(1)


if __name__ == '__main__':
    main()
