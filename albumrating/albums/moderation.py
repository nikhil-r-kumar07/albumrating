import re

# Comments containing any of these words are rejected before they're posted.
# Add slurs and other words you never want on the site, in lowercase, e.g.
# BLOCKED_WORDS = ['word1', 'word2']
# Matching ignores case and catches common disguises: "W0RD", "w.o.r.d", "w-o-r-d", "w o r d".
BLOCKED_WORDS = []

# A comment is hidden automatically once this many different people report it.
HIDE_AFTER_REPORTS = 2

_SWAPS = str.maketrans({'@': 'a', '4': 'a', '3': 'e', '1': 'i', '0': 'o', '$': 's', '5': 's', '7': 't'})

def is_blocked(text):
    text = text.lower().translate(_SWAPS)
    # "w.o.r.d" or "w-o-r-d" -> "word"
    text = re.sub(r'(?<=[a-z])[.\-_*]+(?=[a-z])', '', text)
    words = re.findall(r'[a-z]+', text)
    # "w o r d" -> look inside runs of single letters
    runs, run = [], ''
    for word in words + ['']:
        if len(word) == 1:
            run += word
        else:
            if len(run) > 1:
                runs.append(run)
            run = ''
    for blocked in BLOCKED_WORDS:
        blocked = blocked.lower()
        # Whole words only, so a blocked word inside an innocent longer word doesn't trigger it.
        if blocked in words or any(blocked in r for r in runs):
            return True
    return False
