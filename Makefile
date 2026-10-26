BUILD := build
# Decks live in course folders; -mindepth 2 skips root files like CLAUDE.md.
SLIDES := $(shell find . -mindepth 2 -name '*.md' -not -path './$(BUILD)/*' -not -path './.*')
THEMES := $(wildcard themes/*.css)

.PHONY: deploy

# Copy all HTML into build/ after rebuilding any out-of-date decks.
deploy: $(SLIDES:.md=.html)
	rm -rf $(BUILD) && mkdir -p $(BUILD)
	find . -name '*.html' -not -path './$(BUILD)/*' -not -path './.*' -exec cp --parents {} $(BUILD) \;

# Rebuild a deck only when its .md, a theme, or the marp config changed.
%.html: %.md $(THEMES) .marprc.yml
	marp $< -o $@
