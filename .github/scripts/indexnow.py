import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlparse

SITE = os.environ.get('SITE_URL', 'https://art-bombik.github.io').rstrip('/')
ENDPOINT = os.environ.get('INDEXNOW_ENDPOINT', 'https://api.indexnow.org/indexnow')
KEY = os.environ['INDEXNOW_KEY']
WAIT_SECONDS = int(os.environ.get('INDEXNOW_WAIT', '900'))
POLL_SECONDS = int(os.environ.get('INDEXNOW_POLL', '15'))
EMPTY_TREE = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'
NOINDEX = re.compile(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex', re.I)


def git(*args):
    return subprocess.run(['git', *args], capture_output=True, text=True, check=True).stdout


def exists(revision):
    return subprocess.run(['git', 'cat-file', '-e', f'{revision}^{{commit}}'], capture_output=True).returncode == 0


def changed_pages(before):
    if before and set(before) != {'0'} and exists(before):
        start = before
    elif exists('HEAD^'):
        start = 'HEAD^'
    else:
        start = EMPTY_TREE
    output = git('diff', '--name-only', '--diff-filter=d', start, 'HEAD', '--', '*.html')
    return [line for line in output.splitlines() if line]


def page_path(file):
    return '/' + re.sub(r'(^|/)index\.html$', r'\1', file)


def is_indexable(file, sitemap, robots):
    path = page_path(file)
    return path in sitemap and robots.can_fetch('*', SITE + path) and not NOINDEX.search(Path(file).read_text(encoding='utf-8'))


def fetch(url):
    request = urllib.request.Request(f'{url}?v={int(time.time())}', headers={'Cache-Control': 'no-cache'})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    except (urllib.error.URLError, TimeoutError):
        return None


def wait_until_live(files):
    expected = {f'{SITE}{page_path(file)}': Path(file).read_bytes() for file in files}
    expected[f'{SITE}/{KEY}.txt'] = KEY.encode()
    deadline = time.time() + WAIT_SECONDS
    while True:
        pending = [url for url, body in expected.items() if fetch(url) != body]
        if not pending:
            return
        if time.time() >= deadline:
            sys.exit(f'Not published in time: {", ".join(pending)}')
        time.sleep(POLL_SECONDS)


def submit(urls):
    payload = json.dumps({
        'host': urlparse(SITE).netloc,
        'key': KEY,
        'keyLocation': f'{SITE}/{KEY}.txt',
        'urlList': urls,
    }).encode()
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    for attempt in range(4):
        request = urllib.request.Request(ENDPOINT, data=payload, headers=headers, method='POST')
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                print(f'IndexNow answered {response.status} for {len(urls)} page(s)')
                return
        except urllib.error.HTTPError as error:
            status = error.code
        except (urllib.error.URLError, TimeoutError) as error:
            status = str(error)
        retryable = status == 429 or not isinstance(status, int) or status >= 500
        if not retryable or attempt == 3:
            sys.exit(f'IndexNow refused the request: {status}')
        time.sleep(POLL_SECONDS * (attempt + 1))


def main():
    sitemap = {urlparse(loc).path for loc in re.findall(r'<loc>([^<]+)</loc>', Path('sitemap.xml').read_text(encoding='utf-8'))}
    robots = urllib.robotparser.RobotFileParser()
    robots.parse(Path('robots.txt').read_text(encoding='utf-8').splitlines())
    files = [file for file in changed_pages(os.environ.get('BEFORE', '')) if is_indexable(file, sitemap, robots)]
    if not files:
        print('No indexable pages changed')
        return
    wait_until_live(files)
    urls = [f'{SITE}{page_path(file)}' for file in files]
    print('\n'.join(urls))
    submit(urls)


if __name__ == '__main__':
    main()
