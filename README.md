# The Lift

A daily trivia game. You get five prompts like "Name a fast food chain" and 25 seconds each.
The more niche your answer, the higher the lift climbs: past three random New York towers,
up to the Empire State Building, or out into space.

- **Today's Lift** is the same five prompts and towers for everyone, refreshing at midnight.
- **Free ride** gives unlimited random rounds.
- Wrong answers flash FLOOR NOT RECOGNISED and you can keep guessing until time runs out.
- Close misspellings ask "Did you mean …?"; press Enter again to lock the answer in.
- After each round you can see every answer you could have given, and share your result.

## Play it

**https://somethingorotherogod.github.io/the-lift/**

Or run it yourself: open `index.html` in a browser (it loads `lift_questions.js` from the same folder).
To serve it locally: `python3 -m http.server` and visit http://localhost:8000.

## Files

| File | What it is |
| --- | --- |
| `index.html` | The whole game: lift scene, buildings, matching, results. |
| `lift_questions.js` | The question bank the game loads. Generated, don't edit by hand. |
| `tiers.txt` | Every prompt and answer, sorted into five nicheness tiers. Edit this to change questions. |
| `build_lift.py` | Builds `lift_questions.js` from `tiers.txt` (plus Wikipedia spellings from `questions.js`). |
| `questions.js` | Answer lists and spellings pulled from Wikipedia/Wikidata by `build_questions.py`. |
| `build_questions.py` | Fetches `questions.js` from Wikipedia. Slow; rarely needed. |
| `tiers_hard.txt` | The older, harder question set (popes, Nobel winners and so on). |
| `tiers_brands.txt` | The brand prompts on their own, before merging into `tiers.txt`. |

## Changing the questions

1. Edit `tiers.txt`. Each prompt starts with `= Name a …`; lines `1:` to `5:` list answers from
   most common to most niche, separated by ` | `. Extra spellings go in braces: `Coca-Cola {Coke}`.
2. Run `python3 build_lift.py`.
3. Reload the page.
