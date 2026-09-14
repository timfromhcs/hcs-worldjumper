import requests
import re

r = requests.get('https://huggingface.co/spaces/timfromhcs/hcs-worldjumper')
print("Status:", r.status_code)
# Search for iframe or direct URL
for line in r.text.splitlines():
    if 'iframe' in line or 'hf.space' in line:
        print("MATCH:", line[:200])
