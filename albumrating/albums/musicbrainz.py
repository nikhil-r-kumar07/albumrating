import re
import requests

MB_URL = 'https://musicbrainz.org/ws/2/'
HEADERS = {'User-Agent': 'IYMReviews/1.0 ( iymmoviereviews@gmail.com )'}

def _parse(group):
    artist = group['artist-credit'][0]['artist']
    date = group.get('first-release-date', '')
    return {
        'mbid': group['id'],
        'name': group['title'],
        'artist_name': artist['name'],
        'artist_mbid': artist['id'],
        'year': int(date[:4]) if date[:4].isdigit() else None,
        'cover_url': 'https://coverartarchive.org/release-group/' + group['id'] + '/front-500',
    }

def search_albums(query):
    query = re.sub(r'[+\-&|!(){}\[\]^"~*?:\\/]', ' ', query).strip()
    if not query:
        return []
    try:
        response = requests.get(MB_URL + 'release-group/', headers=HEADERS, timeout=10, params={
            'query': '(' + query + ') AND primarytype:album', 'fmt': 'json', 'limit': 12})
        response.raise_for_status()
    except requests.RequestException:
        return None
    return [_parse(group) for group in response.json().get('release-groups', [])]

def get_album(mbid):
    try:
        response = requests.get(MB_URL + 'release-group/' + mbid, headers=HEADERS, timeout=10,
                                params={'inc': 'artists', 'fmt': 'json'})
        response.raise_for_status()
    except requests.RequestException:
        return None
    return _parse(response.json())
