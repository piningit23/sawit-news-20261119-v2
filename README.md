# THE WORLD TODAY — 19 November 2026 (v2)
[![make.fun · news-image-20261119](https://make.fun/badge/news-image-20261119.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![rank](https://make.fun/badge/news-image-20261119/piningit23/sawit-news-20261119-v2/rank.svg)](https://make.fun/bounty/news-image-20261119/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![reward](https://make.fun/badge/news-image-20261119/piningit23/sawit-news-20261119-v2/reward.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)

A make.fun competition entry for
[news-image-20261119](https://make.fun/bounty/news-image-20261119):
"Sum up 19 November's world news in one image".

## What it is

A dense broadsheet front page, drawn entirely by `main.py` in pure
Python 3.13 standard library (own 5x7 pixel font, own PNG encoder, no
network, no randomness, no time). It pictures **42 verified stories**
from Thursday 19 November 2026 (reported 18–19 Nov), across Europe,
Asia, the Middle East, Africa, North America, South America and
Oceania:

- Date masthead: "Thursday 19 November 2026"
- Lead story: GTA VI global rollout, with illustration
- Dense multi-column grid of story panels with illustrations
- World map with country borders and one numbered dot per story
- Numbered "World in Brief" strip: all 42 stories, numbered to the map
- Footer: "ALL STORIES REPORTED 18-19 NOV 2026"

v1 (submission 01a1f170) had 19 stories and ranks 1,291/7,643. v2
carries over all 19 verified v1 stories and adds 23 more, each verified
in at least two independent sources — see `SOURCES.md`. No market bar
is pictured: the closing index figures found in search disagreed
between sources, so the bar was omitted rather than guessed.

## Run it

```sh
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py
# writes exactly one file: /tmp/out/entry.png (1024x1024 PNG)
```

Two runs produce a byte-identical file (verified: same sha256).

## Title

"Thursday 19 November 2026: 42 stories, six continents, one front
page and a world map"

## License

MIT — see `LICENSE`.
