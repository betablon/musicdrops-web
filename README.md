# musicdrops-web
## German pages

The pages at the root hold both languages (`lang="en"` and `lang="de"` side by
side) and are served as the English site. `de/` is generated from them by
`scripts/build_german_pages.py`: edit the root pages, never `de/`. The
"Build German pages" workflow rebuilds `de/` on every push to `main`; to see
it locally, run `python3 scripts/build_german_pages.py`.
