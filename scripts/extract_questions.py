#!/usr/bin/env python3
"""Write BUILD_DIR/<deck>.questions.json for decks with question slides.

Usage: extract_questions.py BUILD_DIR DECK.md...

A question is a slide containing a comment like this one. The app reads the
JSON, and Marp shows the comment to the presenter as a speaker note.

    <!-- question
    ask: Which is false?     (optional; default is the slide's first heading)
    answer: A                (required; an option letter if the slide has a
    answer: C                 numbered list, otherwise a model answer. Repeat
                              the line for each accepted answer)
    -->

A numbered list on the slide becomes the options, unless the slide has the
`numbered` class. Values may contain colons. Indent a line to continue the
previous value.
Each question's id is generated from what students see (see question_id).
Decks without question slides get no JSON. Any invalid question fails the
build, because a silently dropped question is worse than a stopped deploy.
Standard library only, since `make build` doesn't use the venv.
"""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

SCHEMA = 2
LETTERS = "ABCD"  # the theme's answer boxes (see COLORS.md)

FRONT_MATTER = re.compile(r"\A---[ \t]*\n(.*?)^---[ \t]*$", re.M | re.S)
COMMENT = re.compile(r"<!--.*?-->", re.S)
MARKER = re.compile(r"<!--\s*question\b(.*?)-->", re.S)
SEPARATOR = re.compile(r"^---[ \t]*$", re.M)
HEADING = re.compile(r"^#{1,6}[ \t]+(.+)$", re.M)
OPTION = re.compile(r"\d+[.)][ \t]+(.*)")


def blank(match):
    """Hide text from later regexes while keeping every offset and line."""
    return re.sub(r"[^\n]", " ", match[0])


def blank_code(text):
    """Blank fenced code blocks, so examples in them are never parsed."""
    out, fenced = [], False
    for line in text.splitlines(keepends=True):
        is_fence = line.startswith(("```", "~~~"))
        hide = fenced or is_fence
        out.append(re.sub(r"[^\n]", " ", line) if hide else line)
        if is_fence:
            fenced = not fenced
    return "".join(out)


def split_slides(plain):
    """Return (start, end) offsets per slide of text with comments blanked."""
    fm = FRONT_MATTER.match(plain)
    start = fm.end() if fm else 0
    bounds = []
    for sep in SEPARATOR.finditer(plain, start):
        bounds.append((start, sep.start()))
        start = sep.end()
    return bounds + [(start, len(plain))]


def parse_fields(body):
    """Return (ask, answers) from a question comment's body."""
    values = {"ask": [], "answer": []}
    key = None
    for line in body.strip().splitlines():
        if not line.strip():
            continue
        if m := re.match(r"(\w+):[ \t]*(.*)", line):
            key = m[1]
            if key not in values:
                raise ValueError(f"unknown key {key!r} (indent the line if it continues a value)")
            if key == "ask" and values[key]:
                raise ValueError("duplicate key 'ask'")
            values[key].append(m[2].strip())
        elif key is None:
            raise ValueError(f"expected 'key: value', got {line.strip()!r}")
        else:
            values[key][-1] = f"{values[key][-1]} {line.strip()}".strip()
    return (values["ask"] or [""])[0], values["answer"]


def parse_options(slide):
    """Return the slide's first numbered list as {letter: text}."""
    items, started = [], False
    for line in slide.splitlines():
        if m := OPTION.match(line):
            items.append(m[1].strip())
            started = True
        elif started and line.strip():
            if not line[0].isspace():
                break
            items[-1] += " " + line.strip()
    if len(items) > len(LETTERS):
        raise ValueError(f"{len(items)} options, but the theme only letters {len(LETTERS)}")
    return dict(zip(LETTERS, items))


def question_id(question):
    """Changes only when students would see a different question: moving the
    slide or fixing `answers` keeps earlier responses attached, and a reworded
    question can't be mixed up with the old wording."""
    seen = {k: question[k] for k in ("ask", "options")}
    digest = hashlib.sha256(json.dumps(seen, sort_keys=True).encode()).hexdigest()
    return f"q-{digest[:12]}"  # the prefix stops tools reading it as a number


def build_question(ask, answers, slide, slide_number, numbered):
    answers = [a for a in answers if a]  # a blank `answer:` line is a placeholder
    if not answers:
        raise ValueError("missing answer")
    if len(set(answers)) < len(answers):
        raise ValueError("the same answer is listed twice")

    # The numbered class means the list is a sequence, not A-D boxes.
    options = {} if numbered else parse_options(slide)
    if options:
        if len(options) < 2:
            raise ValueError("a numbered list needs at least 2 options")
        for answer in answers:
            if answer not in options:
                raise ValueError(
                    f"answer {answer!r} is not one of {', '.join(options)} "
                    "(add the numbered class if the list isn't answer choices)"
                )

    heading = HEADING.search(slide)
    ask = ask or (heading[1].strip() if heading else "")
    if not ask:
        raise ValueError("slide has no heading, so add ask")

    return {"slide": slide_number, "ask": ask, "options": options, "answers": answers}


def extract(path, text):
    """Return (questions, errors) for one deck."""
    questions, errors, seen = [], [], Counter()
    no_code = blank_code(text)
    plain = COMMENT.sub(blank, no_code)

    def fail(pos, message):
        errors.append(f"{path}:{text.count(chr(10), 0, pos) + 1}: {message}")

    for number, (start, end) in enumerate(split_slides(plain), 1):
        markers = list(MARKER.finditer(no_code, start, end))
        if not markers:
            continue
        marker = markers[0]
        if len(markers) > 1:
            fail(markers[1].start(), "more than one question on a slide")
            continue
        comments = COMMENT.findall(no_code[start:end])
        numbered = any(re.search(r"_class:.*\bnumbered\b", c) for c in comments)
        try:
            question = build_question(*parse_fields(marker[1]), plain[start:end], number, numbered)
        except ValueError as e:
            fail(marker.start(), str(e))
            continue
        # A deck may repeat a question on purpose, e.g. before and after a lesson.
        qid = question_id(question)
        seen[qid] += 1
        if seen[qid] > 1:
            qid += f"-{seen[qid]}"
        questions.append({"id": qid, "order": len(questions) + 1, **question})
    return questions, errors


def main(build_dir, paths):
    outputs, errors = [], []
    for path in map(Path, paths):
        text = path.read_text()
        questions, deck_errors = extract(path, text)
        errors += deck_errors
        if questions:
            fm = FRONT_MATTER.match(text)
            title = re.search(r"^title:[ \t]*(.+)$", fm[1], re.M) if fm else None
            outputs.append((path, {
                "schema": SCHEMA,
                "deck": path.with_suffix("").as_posix(),
                "title": title[1].strip() if title else None,
                "questions": questions,
            }))
    if errors:
        sys.exit("Invalid question slides:\n" + "\n".join(f"  {e}" for e in errors))
    for path, data in outputs:
        out = Path(build_dir) / path.with_suffix(".questions.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        # No timestamps: build/ is committed, so unchanged decks must not diff.
        out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        print(f"{out}: {len(data['questions'])} question(s)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
