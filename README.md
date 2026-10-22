# FNN stories feed

Public story feed for the FNN Fake News Network app (www.fnnfakenewsnetwork.com).

- `stories.json`: the current edition. The app reads it from
  https://raw.githubusercontent.com/richdiskin/fnn-data/main/stories.json
- `stories.schema.json`: JSON Schema (draft 2020-12) for the feed.
- `validate.py`: checks the feed against the schema and the writing rules. Run `python3 validate.py` before every push; it must report 0 errors.

Rules: story bodies carry no links (every source goes in `record`), `slug` never changes after publish, and `then`/`now` are optional but come as a pair.
