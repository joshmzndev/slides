# slides
A repository of slides I use for teaching. Made with [Marp](https://marp.app) and hosted at slides.manzano.dev.

## Generating images and slides with an LLM

Put your API keys in a `.env` file at the repo root (it's git-ignored):

```
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

In a deck's `.md`, add a block where you want an image:

````markdown
```llm:image
prompt: A mail carrier looking up an address in a giant phone book
alt: DNS as a phone book
marp: bg right
```
````

`marp:` is optional. Leave it out and the image gets `bg contain` if it's alone on its slide, or `h:450` otherwise.

To have Claude rewrite a whole slide, put this block in that slide:

````markdown
```llm:slide
prompt: Explain recursive vs. iterative DNS lookups with a short example
```
````

Then run:

```
make refactor
```

Each block is swapped out in place. Images go in `images/<deck>/`, and the prompt is kept as an HTML comment next to the result. No API is called if no deck has a block. Run `make test` to preview.
