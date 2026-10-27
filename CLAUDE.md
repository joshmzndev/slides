# Slides

Slide decks written in Markdown and converted to HTML with [Marp](https://marp.app).

**Never read, open, print, or search any `.env` file (or its contents) in any way, including with `cat`, `grep`, `source`, or scripts that echo it.** It holds API keys. This is strictly forbidden, with no exceptions. Only `scripts/refactor.py` loads it, at run time.

- `<course>/*.md`: slide sources (e.g. `ap-cyb/dns.md`); the `.html` next to each is Marp's output.
- `index.html`: hand-written landing page for slides.manzano.dev; `make build` copies it to `build/index.html`. Nothing generates it, so whenever a deck or course is added, renamed, or removed, edit its "What's here" list by hand in the same change (a new course gets its own card).
- `themes/`: custom Marp themes (set via `.marprc.yml`). Marp inlines them into the HTML, so the CSS isn't deployed.
- `make build`: rebuilds decks whose `.md`, a theme, or `.marprc.yml` changed and copies the HTML into `build/`, keeping the folder layout, along with any `images/` files the decks reference.
- `make test`: runs `make build`, then serves `build/` locally with `python3 -m http.server` to preview.
- `make refactor`: runs `scripts/refactor.py` (in `.venv`) over every deck, replacing ```` ```llm:image ```` blocks (`prompt:`, `alt:`, optional `marp:` keywords like `bg right`; without them an image alone on its slide gets `bg contain`, otherwise `h:450`, so it fits) with an OpenAI-generated image in `images/<deck>/`, and ```` ```llm:slide ```` blocks (`prompt:`) with a whole slide written by Claude. Decks are regex-scanned first, so no API is called when there's nothing to replace. Keys `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` go in `.env` (git-ignored).
- `make deploy`: runs `make build`, deletes each deck's `.html` once its copy in `build/` matches (so the next build regenerates every deck; `index.html` is kept), then `git add .`, commits with the current date and time as the message, and pushes.
- `build/`: what gets deployed. GitHub Actions (`.github/workflows/main.yml`) uploads it to Cloudflare with `wrangler deploy` on every push to `main` (see `wrangler.toml`), using the `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` repository secrets.
