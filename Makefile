BUILD := build
# Decks live in course folders; -mindepth 2 skips root files like CLAUDE.md.
SLIDES := $(shell find . -mindepth 2 -name '*.md' -not -path './$(BUILD)/*' -not -path './.*')
THEMES := $(wildcard themes/*.css)

.PHONY: build test deploy

# Copy all HTML into build/ after rebuilding any out-of-date decks,
# plus only the images/ files the decks actually reference.
build: $(SLIDES:.md=.html)
	rm -rf $(BUILD) && mkdir -p $(BUILD)
	find . -name '*.html' -not -path './$(BUILD)/*' -not -path './.*' -exec cp --parents {} $(BUILD) \;
	grep -ohE 'images/[^])"'"'"'[:space:]]+' $(SLIDES) | sort -u | xargs -r cp --parents -t $(BUILD)

# Build, then serve build/ locally to preview changes (no commit or push).
test: build
	python3 -m http.server --directory $(BUILD)

# Build, then commit everything and push (which triggers the deploy).
deploy: build
	git add .
	git diff --cached --quiet || git commit -m "$$(date '+%Y-%m-%d %H:%M:%S')"
	git push

# Rebuild a deck only when its .md, a theme, or the marp config changed.
%.html: %.md $(THEMES) .marprc.yml
	marp $< -o $@
