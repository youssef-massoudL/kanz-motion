# References: what the motion layer grows from

Drop motion, transition, type or composition references here so new pieces are built from what you liked, not
guessed. The guide that turns them into pieces is [docs/MOTION-LANGUAGE.md](../../docs/MOTION-LANGUAGE.md) section 7.

## Where things go

- `media/`: the clips, screenshots and GIFs themselves. **Local only** (git-ignored): this repo is public and the
  references are other people's work (REPO-1). Name files `<id>.<ext>`.
- `references.json`: one entry per reference. This is what a session reads first.

## An entry

| Field | Meaning |
| --- | --- |
| `id` | short kebab-case name, used as `ref` in the variant built from it |
| `status` | `new` (not looked at), `building`, `used` (a variant or piece exists), `parked` |
| `file` / `url` / `source` | where it is and who made it |
| `idea_types` | which ideas it serves: `value-change`, `loss`, `level`, `share`, `money-moving`, `journey`, `claim`, `focus`, `transition`, `texture` (or a new one) |
| `take` | exactly what to borrow: the motion, the timing, the composition, the reveal |
| `leave` | what not to borrow: always their colours and type (the brand stays Kanz), plus anything else |
| `timestamps` | the seconds that matter in a clip |
| `built_as` | filled in when used: e.g. `K.mx.ENTER.sweep` or `K.mx.stack` |

The more precise `take` is, the closer the result: "the number rides up on the liquid's surface and overshoots by
about 5%" beats "nice fill animation".

## Turning one into a piece

1. Add the entry (`status: new`).
2. Ask for it to be built: a new entrance goes into `K.mx.ENTER` with `ref: "<id>"`; a new device becomes a
   `K.mx.<name>` piece in brand material.
3. It is shown on a real line in `projects/_motion-demo`, rendered and reviewed.
4. The entry gets `status: used` and `built_as`.
