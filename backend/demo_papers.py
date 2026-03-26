"""
Pre-loaded demo paper excerpts for one-click conversion testing.
All text is synthetic / paraphrased to avoid copyright issues.
"""
from typing import Any

DEMO_PAPERS: list[dict[str, Any]] = [
    {
        "id": "attention-is-all-you-need",
        "title": "Attention Is All You Need",
        "description": "The Transformer architecture — self-attention replaces recurrence for sequence modelling.",
        "topic": "Natural Language Processing",
        "year": 2017,
        "text": """\
Abstract
We propose the Transformer, a model architecture based solely on attention mechanisms,
dispensing with recurrence and convolutions entirely. The model achieves superior quality
on machine translation tasks while being more parallelisable and requiring significantly
less time to train.

1. Introduction
Recurrent neural networks have been the dominant approach to sequence modelling. However,
the sequential nature of RNNs precludes parallelisation within training examples, which
becomes critical at longer sequence lengths.

2. Methodology
The Transformer uses stacked self-attention and point-wise, fully connected layers for
both the encoder and decoder. Multi-head attention allows the model to jointly attend to
information from different representation subspaces.

Multi-Head Attention:
  MultiHead(Q, K, V) = Concat(head_1, ..., head_h) * W_O
  head_i = Attention(Q*W_i_Q, K*W_i_K, V*W_i_V)

Scaled Dot-Product Attention:
  Attention(Q, K, V) = softmax(Q*K^T / sqrt(d_k)) * V

3. Algorithms
The encoder is composed of N=6 identical layers, each with two sub-layers: multi-head
self-attention and position-wise feed-forward network. Residual connections and layer
normalisation are applied around each sub-layer.

Positional encoding uses sine and cosine functions of different frequencies so the model
can learn to attend by relative position.

4. Datasets
We trained and evaluated on:
- WMT 2014 English-German (4.5M sentence pairs)
- WMT 2014 English-French (36M sentence pairs)
- The Penn Treebank dataset (40K training sentences) for English constituency parsing

5. Results
The Transformer (big) model achieves 28.4 BLEU on the WMT 2014 English-to-German
translation task, improving on the best previously reported results by more than 2 BLEU.
On English-to-French translation it achieves 41.0 BLEU, outperforming all previous models
at less than 1/4 the training cost.

6. Conclusions
The Transformer is the first transduction model relying entirely on self-attention to
compute representations of its input and output without using sequence-aligned RNNs or
convolution. We achieve state-of-the-art results on English-to-German and English-to-French
translation tasks and plan to extend the Transformer to other modalities.
""",
    },
    {
        "id": "bert-pretraining",
        "title": "BERT: Pre-training of Deep Bidirectional Transformers",
        "description": "Bidirectional encoder representations from transformers for language understanding.",
        "topic": "Natural Language Processing",
        "year": 2019,
        "text": """\
Abstract
We introduce BERT (Bidirectional Encoder Representations from Transformers), designed to
pre-train deep bidirectional representations by jointly conditioning on both left and right
context. Pre-trained BERT can be fine-tuned with just one additional output layer to create
state-of-the-art models for a wide range of tasks.

1. Introduction
Language model pre-training has been shown to be effective for improving many NLP tasks.
Existing pre-trained representations are either unidirectional or shallowly bidirectional,
which limits their power. BERT addresses these limitations using a masked language modelling
objective that enables pre-training of deep bidirectional representations.

2. Methodology
BERT pre-training uses two unsupervised tasks:
- Masked Language Model (MLM): randomly mask 15% of input tokens and predict them.
- Next Sentence Prediction (NSP): predict whether two sentences are consecutive.

Fine-tuning simply adds a task-specific layer on top of the pre-trained representations.

3. Algorithms
Input representation combines token embeddings, segment embeddings, and position embeddings.
Transformer encoder with L layers, H hidden size, A attention heads.

BERT_BASE: L=12, H=768, A=12, Total Parameters=110M
BERT_LARGE: L=24, H=1024, A=16, Total Parameters=340M

4. Datasets
Pre-training corpora:
- BooksCorpus (800M words)
- English Wikipedia (2,500M words)
Fine-tuning benchmarks: GLUE, SQuAD v1.1, SQuAD v2.0, SWAG

5. Results
BERT_LARGE achieves 80.5% on GLUE benchmark (7.7% improvement over prior state-of-the-art).
On SQuAD v1.1, BERT obtains 93.2 F1 (1.5 points improvement). On SQuAD v2.0, BERT obtains
83.1 F1 (5.1 points improvement over prior best).

6. Conclusions
BERT advances the state of the art for eleven NLP tasks. The key insight is the importance
of bidirectional pre-training for language representations. BERT is the first fine-tuning
based representation model that achieves state-of-the-art performance on sentence-level and
token-level tasks.
""",
    },
    {
        "id": "arc-agi-benchmark",
        "title": "On the Measure of Intelligence (ARC)",
        "description": "The ARC dataset as a benchmark for general intelligence — abstract reasoning tasks.",
        "topic": "Artificial General Intelligence",
        "year": 2019,
        "text": """\
Abstract
We introduce the Abstraction and Reasoning Corpus (ARC), a benchmark designed to measure
general intelligence rather than task-specific skill. ARC tasks require solving novel
visual puzzles from only a few examples, testing core knowledge priors including object
persistence, counting, and basic geometry.

1. Introduction
Current AI benchmarks mostly measure narrow skills. A system that achieves human-level
performance on ARC must demonstrate genuine abstract reasoning, not pattern matching.
Each ARC task presents a small set of input/output grid pairs and asks the model to
deduce the transformation rule and apply it to a new input.

2. Methodology
Tasks are generated by composing core knowledge priors:
- Objectness and object properties (colour, shape, size)
- Goal-directedness and intentionality
- Numbers and counting (up to ~10)
- Basic Euclidean geometry (symmetry, rotation, scaling)

Human performance is established by having naive (non-expert) participants solve each task.
Only tasks where humans achieve above 85% accuracy are included.

3. Algorithms
Evaluation metric: percentage of tasks solved (an exact match of the output grid).
Two attempts are allowed per task. No partial credit.

Baseline approaches tested:
- Random search over DSL programs
- Neural program synthesis (DreamCoder-style)
- Few-shot GPT prompting (as of 2019)

4. Datasets
- ARC training set: 400 tasks
- ARC evaluation set: 400 tasks
- Private test set: 100 held-out tasks (used for the ARC Prize competition)

5. Results
State-of-the-art AI systems achieve < 30% on ARC public evaluation, while humans average
85%. This gap illustrates the difficulty of the benchmark for current deep learning methods.
GPT-4 achieves approximately 20% without fine-tuning.

6. Conclusions
ARC provides a reliable measure of general fluid intelligence. The benchmark requires
systems to learn efficient priors over abstract transformations rather than memorising
task-specific solutions. Bridging the human-AI gap on ARC remains a core challenge for AGI.
""",
    },
]

DEMO_PAPER_MAP: dict[str, dict[str, Any]] = {p["id"]: p for p in DEMO_PAPERS}
