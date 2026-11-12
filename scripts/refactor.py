#!/usr/bin/env python3
"""Replace ```llm:image and ```llm:slide prompt blocks in Marp decks, and
expand answer-modes slides.

Usage: refactor.py DECK.md...

A slide with `answer-modes` in its `<!-- _class: ... -->` becomes two slides,
wrong-answer then best-answer, otherwise identical. No API is called for this.

Every deck is scanned with a regex first; the APIs are only called (and
the SDKs only imported) for blocks that are actually found. Each file is
saved after every replacement, so a failure keeps earlier progress.

Last, one cheap Claude call (REVIEW_MODEL, low effort) reads every deck and
prints suggested fixes for inconsistencies as the final output.
"""
import json
import base64
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOCK = re.compile(r"^```llm:(image|slide)[ \t]*\n(.*?)^```[ \t]*\n?", re.M | re.S)
MODES = re.compile(r"(<!--\s*_class:[^\n>]*?)\banswer-modes\b")
HEADING = re.compile(r"^#{1,6}[ \t]+.+$", re.M)
# Wrong answers come first, so students commit before seeing the best ones.
MODE_ORDER = ("wrong-answer", "best-answer")
IMAGE_MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2.5-sunburst")
# 16:10 like the decks (1280x800), 1.5x for sharp projectors; multiples of 16.
IMAGE_SIZE = os.environ.get("OPENAI_IMAGE_SIZE", "1920x1200")
CLAUDE_MODEL = "claude-opus-5-5"
REVIEW_MODEL = "claude-haiku-5-5"
IMAGE_PROMPT = (
    "In video game pixel art style, create a digital art representation of "
    "{description}. Use visualizations and not words when possible."
)

SLIDE_SYSTEM = """You write exactly one slide of a Marp deck (1280x800, 16:10).
Reply with only that slide's Markdown: no `---`, no front matter, no code fence around it.
- Keep it concise: a heading and at most 5 short lines or bullets.
- Match the deck's tone and markup. Use only classes and styles defined in the theme CSS or the deck's own `style`/`<style>`; set a class with `<!-- _class: name -->`.
- If a picture would help, add a block that is generated later:
```llm:image
prompt: <what to draw>
alt: <alt text>
```"""


REVIEW_SYSTEM = """You review a set of Marp slide decks for a high-school course site for inconsistencies.
Look for things that differ between slides or decks when they should match: terminology and spelling
of the same term, heading capitalization and style, front matter (theme, paginate, etc.),
slide classes (`<!-- _class: ... -->`) and question comments (`<!-- question ... -->` with `ask:`/`answer:` lines),
image markup, numbering of multi-part decks, typos, and facts that contradict each other.
Only report real, specific problems, most important first, at most 15. Each fix must say exactly what to change.
Cite the file path and the line number shown at the start of each line. Return an empty list if nothing is inconsistent."""

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {"issues": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "path:line"},
            "problem": {"type": "string"},
            "fix": {"type": "string"},
        },
        "required": ["location", "problem", "fix"],
        "additionalProperties": False,
    }}},
    "required": ["issues"],
    "additionalProperties": False,
}


def load_env():
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        key, sep, value = line.partition("=")
        key = key.strip().removeprefix("export ").strip()
        if sep and key and not key.startswith("#"):
            os.environ.setdefault(key, value.strip().strip("'\""))


def fields(body):
    """Parse `key: value` lines; unkeyed lines continue the previous value."""
    out, key = {}, None
    for line in body.splitlines():
        if m := re.match(r"(\w+):\s*(.*)", line):
            key = m[1]
            out[key] = m[2].strip()
        elif key and line.strip():
            out[key] += " " + line.strip()
    out.setdefault("prompt", body.strip())
    return out


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "image"


def describe(prompt):
    """Fit a prompt mid-sentence: "A hook." -> "a hook" (acronyms like DNS kept)."""
    prompt = prompt.strip().rstrip(".")
    first = prompt.split(maxsplit=1)[0] if prompt else ""
    if not (len(first) > 1 and first.isupper()):
        prompt = prompt[0].lower() + prompt[1:]
    return prompt


def note(prompt):
    # Marp shows HTML comments as speaker notes; "--" would end the comment early.
    return f"<!-- llm prompt: {prompt.replace('--', '- -')} -->"


def slide_bounds(text, pos):
    """Return the (start, end) offsets of the slide containing pos."""
    seps, fence, offset = [], False, 0
    for line in text.splitlines(keepends=True):
        if line.startswith("```"):
            fence = not fence
        elif not fence and line.rstrip() == "---":
            seps.append((offset, offset + len(line)))
        offset += len(line)
    if text.startswith("---"):
        seps = seps[1:]  # the opening front matter fence isn't a slide break
    start = max((e for s, e in seps if e <= pos), default=0)
    end = min((s for s, e in seps if s >= pos), default=len(text))
    return start, end


def find_modes(text):
    """answer-modes class directives outside fenced code blocks."""
    found, fence, offset = [], False, 0
    for line in text.splitlines(keepends=True):
        if line.startswith("```"):
            fence = not fence
        elif not fence:
            found += MODES.finditer(text, offset, offset + len(line))
        offset += len(line)
    return found


def make_pair(deck, text, match):
    """Replace the answer-modes slide with its wrong-answer and best-answer copies."""
    start, end = slide_bounds(text, match.start())
    body = text[start:end].strip("\n")
    at = match.start() - start - (len(text[start:end]) - len(text[start:end].lstrip("\n")))
    copies = []
    for mode in MODE_ORDER:
        copies.append(body[:at] + match[1] + mode + body[at + len(match[0]):])
    print(f"  answer modes -> {(HEADING.search(body) or match)[0][:60]}")
    lead = "\n" if start else ""
    tail = "\n\n" if end < len(text) else "\n"
    return text[:start] + lead + "\n\n---\n\n".join(copies) + tail + text[end:]


def fit(text, match):
    """Marp keywords that keep the image inside the slide: fill the slide
    when the image is all it holds, otherwise leave room for the text."""
    start, end = slide_bounds(text, match.start())
    rest = text[start : match.start()] + text[match.end() : end]
    alone = not re.sub(r"<!--.*?-->", "", rest, flags=re.S).strip()
    return "bg contain" if alone else "h:450"


def theme_css(text):
    name = re.search(r"^theme:\s*(\S+)", text, re.M)
    name = name[1] if name else "default"
    for css in (ROOT / "themes").glob("*.css"):
        if re.search(rf"@theme\s+{re.escape(name)}\b", css.read_text()):
            return css.read_text()
    return f"/* built-in Marp theme: {name} */"


def make_image(deck, text, match, clients):
    if "openai" not in clients:
        from openai import OpenAI
        clients["openai"] = OpenAI()
    f = fields(match[2])
    result = clients["openai"].images.generate(
        model=IMAGE_MODEL,
        prompt=IMAGE_PROMPT.format(description=describe(f["prompt"])),
        size=IMAGE_SIZE,
    )
    out = ROOT / "images" / deck.stem / f"{slug(f.get('alt') or f['prompt'])}.png"
    n = 2
    while out.exists():
        out = out.with_stem(f"{out.stem.rsplit('_', 1)[0]}_{n}")
        n += 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(result.data[0].b64_json))
    alt = " ".join(filter(None, [f.get("marp") or fit(text, match), f.get("alt")]))
    link = Path(os.path.relpath(out, deck.parent)).as_posix()
    print(f"  image -> {out.relative_to(ROOT)}")
    return text[: match.start()] + f"![{alt}]({link})\n{note(f['prompt'])}\n" + text[match.end() :]


def make_slide(deck, text, match, clients):
    if "anthropic" not in clients:
        from anthropic import Anthropic
        clients["anthropic"] = Anthropic()
    start, end = slide_bounds(text, match.start())
    prompt = fields(match[2])["prompt"]
    resp = clients["anthropic"].beta.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        output_config={"effort": "medium"},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=SLIDE_SYSTEM,
        messages=[{"role": "user", "content": (
            f"<theme_css>\n{theme_css(text)}\n</theme_css>\n\n"
            f"<deck path=\"{deck.relative_to(ROOT)}\">\n{text}\n</deck>\n\n"
            f"<current_slide>\n{text[start:end].strip()}\n</current_slide>\n\n"
            f"Rewrite the current slide, replacing its llm:slide block, to fulfil: {prompt}"
        )}],
    )
    if resp.stop_reason != "end_turn":
        sys.exit(f"Claude stopped with {resp.stop_reason!r}; {deck} left unchanged.")
    slide = "".join(b.text for b in resp.content if b.type == "text").strip()
    slide = re.sub(r"\A```\w*\n(.*)\n```\Z", r"\1", slide, flags=re.S).strip()
    if "```llm:slide" in slide or slide_bounds(slide, 0) != (0, len(slide)):
        sys.exit(f"Claude returned more than one slide; {deck} left unchanged:\n{slide}")
    print(f"  slide -> {slide.splitlines()[0][:60]}")
    return text[:start] + f"\n{slide}\n{note(prompt)}\n\n" + text[end:]


def review(decks, clients):
    """One cheap pass over all decks; returns bullet lines of suggested fixes."""
    if "anthropic" not in clients:
        from anthropic import Anthropic
        clients["anthropic"] = Anthropic()
    docs, themes = [], {}
    for deck in decks:
        text = deck.read_text()
        themes.setdefault(theme_css(text))
        numbered = "\n".join(f"{i}: {line}" for i, line in enumerate(text.splitlines(), 1))
        docs.append(f"<deck path=\"{deck.relative_to(ROOT)}\">\n{numbered}\n</deck>")
    css = "\n".join(themes)
    resp = clients["anthropic"].messages.create(
        model=REVIEW_MODEL,
        max_tokens=8000,
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": REVIEW_SCHEMA}},
        system=REVIEW_SYSTEM,
        messages=[{"role": "user", "content": f"<theme_css>\n{css}\n</theme_css>\n\n" + "\n\n".join(docs)}],
    )
    if resp.stop_reason != "end_turn":
        return [f"- Review didn't finish (stop reason {resp.stop_reason!r}); no suggestions."]
    text = next(b.text for b in resp.content if b.type == "text")
    issues = json.loads(text)["issues"]
    if not issues:
        return ["- No inconsistencies found."]
    return [f"- {i['location']}: {i['problem']}\n  Fix: {i['fix']}" for i in issues]


def main(paths):
    decks = [Path(p).resolve() for p in paths]
    pending = {}
    for d in decks:
        text = d.read_text()
        if n := len(BLOCK.findall(text)) + len(find_modes(text)):
            pending[d] = n
    if not pending:
        print("No llm:image, llm:slide, or answer-modes blocks found.")
    for deck, n in pending.items():
        print(f"{deck.relative_to(ROOT)}: {n} block(s)")

    load_env()
    clients = {}
    for deck in pending:
        print(f"{deck.relative_to(ROOT)}:")
        # Re-scan after each replacement: offsets shift, and a generated
        # slide may add its own llm:image block.
        while match := BLOCK.search(text := deck.read_text()):
            make = make_image if match[1] == "image" else make_slide
            deck.write_text(make(deck, text, match, clients))
        # After the llm blocks, so a generated image isn't requested twice.
        while modes := find_modes(text := deck.read_text()):
            deck.write_text(make_pair(deck, text, modes[0]))

    if not decks:
        return
    print(f"\nChecking {len(decks)} deck(s) for inconsistencies ({REVIEW_MODEL})...", flush=True)
    try:
        lines = review(decks, clients)
    except Exception as e:  # suggestions are optional; never undo the work above
        lines = [f"- Consistency review failed: {e}"]
    print("\nSuggested fixes:")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1:])
