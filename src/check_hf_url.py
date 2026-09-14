import urllib.request
import re
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('HF_TOKEN')
req = urllib.request.Request(
    'https://huggingface.co/spaces/timfromhcs/hcs-worldjumper',
    headers={'Authorization': f'Bearer {token}', 'User-Agent': 'Mozilla/5.0'}
)
html = urllib.request.urlopen(req).read().decode('utf-8')
iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
print('Iframes found:', iframes)

matches = re.findall(r'https?://[^\s"\'<>]+\.hf\.space[^\s"\'<>]*', html)
print('hf.space URLs found:', set(matches))

# Look for data-props or embed details
data_props = re.findall(r'data-props=["\']([^"\']+)["\']', html)
if data_props:
    print('data-props found (len):', len(data_props[0]))
    for m in re.findall(r'https?://[^\s"\'<>]+', data_props[0]):
        print('url in data-props:', m)
