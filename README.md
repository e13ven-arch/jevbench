# JevBench v1

A benchmark for **Jev-class decision models**: you hand the model a piece of state
and a bounded rubric, and it hands back a typed answer with a probability. No prose,
no parsing, no "as an AI language model".

Five axes, because a single score would hide the trade-off that actually decides which
one you ship: **smart** (is it right), **cheap** (what 1,000 decisions cost), **fast**
(end-to-end latency, network included), **reliable** (does the stated probability mean
anything, does it survive a rephrasing, does it keep to the schema) and **open**
(weights and licence).

JevBench is [Benchmark Heaven](https://benchmarkheaven.com)'s own benchmark. It is not
affiliated with or endorsed by TypeSafe AI, whose Jev model is one of the systems
measured here. Results, the method and the limits are in
[`results/`](results/) and on <https://benchmarkheaven.com/jev-models>.

## What is in the suite

242 decisions, six families, three cohorts:

| Cohort | Decisions | Published here? |
|---|---|---|
| `original-public` | 72 (36 paraphrase pairs) | yes, `datasets/public/original.jsonl` |
| `heldout-private` | 24 | no - held back so the suite cannot be trained on in full |
| `imported-public-source` | 146 | no - ground truth is ours, the task text is not ours to redistribute |

Families: request **routing**, answer **adequacy** judging, **policy** yes/no checks,
**intent** classification, **ordinal** severity scoring and enum **extraction**.
Every item states its exact label set; the model answers over that set and nothing else.

The 146 imported decisions come from our own auto-router experiment: 78 routing requests
with human-assigned categories, and 68 answer-adequacy judgements whose ground truth is a
deterministic grader's verdict on a saved answer. See [`THIRD-PARTY.md`](THIRD-PARTY.md).

## How a model is asked

Every system sees the same state, the same instructions, the same rubric and the same
exact label set. Only the transport differs, and each adapter uses the interface the
author published:

| Adapter | For |
|---|---|
| `typesafe` | TypeSafe's `/v1/systemone`, and the open rebuilds that implement the same wire format |
| `systemone_list` | the list-shaped `/decide` flavour some rebuilds ship |
| `gradio_space` | a rebuild whose only public interface is its Hugging Face Space demo |
| `local_openjev` | open weights loaded in-process, no network |
| `openai_compat` | ordinary instruction models, JSON-schema-constrained |

The first four read the model's **own** probability distribution. The last one asks the
model to **write** probabilities out under a schema. Those are different objects and are
labelled `native` and `verbalized` everywhere. Token-level logprobs are not used
anywhere, for anyone.

## Reproduce

Python 3.10+. The HTTP adapters need only the standard library.

```sh
python -m unittest discover -s tests -v

# Jev, the published 72-decision cohort
python -m jevbench.cli run --tasks datasets/public/original.jsonl \
  --adapter typesafe --model jev-latest --key-env TYPESAFE_API_KEY \
  --price-in-per-m 0.042 --price-out-per-m 0 \
  --results RUN/results.jsonl --raw-dir RUN/raw \
  --ledger RUN/ledger.jsonl --cap-usd 15 --manifest RUN/manifest.json

# an open rebuild on its author's public endpoint - note the empty key
python -m jevbench.cli run --tasks datasets/public/original.jsonl \
  --adapter typesafe --endpoint https://SOME-PUBLIC-ENDPOINT --key-env '' \
  --model jev-latest --cost-basis no_billable_account_public_endpoint \
  --reserve-usd 0 --delay-s 0.2 \
  --results RUN2/results.jsonl --raw-dir RUN2/raw --ledger RUN/ledger.jsonl

python -m jevbench.cli summarize --tasks datasets/public/original.jsonl \
  --results RUN/results.jsonl --public-export RUN/summary.json
```

Keys live in the environment and are named, never written into a config file, a result
or a log. `--key-env ''` sends no `Authorization` header at all, which is what a
stranger's public endpoint should get from us.

House rules the harness enforces rather than documents:

- **One budget for everything.** A file-locked ledger reserves the worst-case cost
  *before* a request goes out and settles the real cost after. The cap is shared across
  every run, not granted per model. A crashed run's reservation stays charged.
- **Every run directory is new.** Results and raw responses are created exclusively;
  a rerun can never overwrite paid evidence.
- **Stop means stop.** A 401, 403 or 429, or three consecutive infrastructure errors,
  ends the run. The rest stays unattempted and is reported as unattempted - never as
  answers the model got wrong. There are no retries.
- **No invented numbers.** An unknown price is `null`, not `0`. An empty metric is
  `null` with `n = 0`, not a flattering `0.0`. A malformed distribution is a schema
  failure and counts as wrong; it is never repaired into a distribution.

## What gets measured

- **Accuracy** - argmax over the exact label set. Every block also reports
  `majority_class_accuracy`, the score of always answering with the commonest label,
  because some cohorts are skewed and an accuracy has to be read against its floor.
  95 % confidence intervals resample whole scenarios, since paraphrases of one scenario
  are not independent draws.
- **Brier** - the multi-class sum `sum_k (p_k - y_k)^2` over the exact label set. Binary
  questions use the matching two-class convention, so the numbers are comparable.
- **ECE** - top-label confidence, 10 equal-width bins. Empty bins are absent, not zero.
  The calibration denominator is reported next to it.
- **Ordinal MAE** - for score questions, the probability-weighted level against the
  reference level, reported beside argmax accuracy rather than instead of it.
- **Paraphrase consistency** - both the same-answer rate and the both-correct rate.
  Agreement alone rewards a model that is consistently wrong.
- **Latency** - caller wall time including the network, one request at a time, no
  concurrency. The first request is reported separately because a scale-to-zero endpoint
  bills its cold start to whoever knocks first.
- **Cost** - measured token usage times the provider's own published tariff, marked
  `derived_usage_times_tariff`. A route with no billable account - a public demo, our own
  CPU, a flat-rate subscription - reports `null` and says which, because unmetered is not
  free.
- **Openness** - code licence, weight availability and weight licence are three separate
  facts, and a permissive repository licence is not a licence for the base model.

## Limits, stated plainly

- 242 decisions is a pilot, not a census. It is English-only, and the original cases are
  short and hand-written.
- The adequacy cohort is 61 `yes` to 7 `no`; its majority-class floor is 82 %. Read that
  family's accuracy against that floor. Some of the judged answers were produced by
  models that also appear as baselines here, so two baselines judge some of their own work.
- The held-out split is sent to the services being evaluated in order to get predictions.
  Not public is not the same as not seen, and this is not a contamination proof.
- Latency comes from one origin (a Hetzner server in Germany) at one time of day. A
  hosted endpoint and a local CPU are not the same kind of latency and should not be
  read as one ranking.
- Public demo endpoints are shared with everyone else using them. Their numbers describe
  that deployment on that day, not the model's ceiling on your hardware.
- Several projects could not be run at all - no GPU, gated weights, Apple-Silicon-only,
  browser-only. They are listed with the concrete reason, and an exclusion is an
  availability fact, never a quality verdict.

## Licence

MIT for this harness and the 72 original public decisions. Everything else - model
weights, other projects' code, upstream datasets - keeps its own licence. See
[`THIRD-PARTY.md`](THIRD-PARTY.md).
