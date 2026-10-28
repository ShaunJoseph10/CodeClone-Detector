# CodeClone Detector

A source-code plagiarism detector for a small subset of Python, built for a Data Structures
micro-project. Every core data structure (stack, queue, linked-list hash table, merge sort,
binary search, BFS) is implemented by hand. Only the Python standard library is used, and
the built-in `ast` / `tokenize` modules are **not** used.

## Problem statement

Students often copy a solution and disguise it by renaming variables, reordering functions,
swapping operands or adding comments. Comparing text line by line misses these disguises.
CodeClone Detector parses each submission into an abstract syntax tree, removes the
disguises by normalizing the tree, fingerprints every subtree, and finds identical subtrees
shared between files. It then ranks file pairs by similarity and groups students who share
one solution into clusters.

## Architecture pipeline

```
Lexer -> Parser -> Normalizer -> Hasher -> HashTable -> Matcher -> Scorer -> Graph -> Report
```

| Stage | File | What it does |
|---|---|---|
| Lexer | `codeclone/lexer.py` | Text -> tokens. Indentation stack emits INDENT/DEDENT; bracket stack checks balance |
| Parser | `codeclone/parser.py` | Recursive descent for statements; shunting-yard + operand stack for expressions |
| AST | `codeclone/ast_nodes.py`, `ast_print.py` | `Node` tree; BFS pretty-printer using a queue |
| Normalizer | `codeclone/normalizer.py` | names -> VAR, user functions -> FUNC, literals -> NUM/STR, `a > b` -> `b < a` |
| Hasher | `codeclone/hasher.py` | Iterative post-order (stack): size and polynomial hash of every subtree; commutative children sorted |
| HashTable | `codeclone/hashtable.py` | Separate chaining with singly linked lists, rehash at load factor > 0.75 |
| Matcher | `codeclone/matcher.py` | Subtrees with size >= MIN_MASS go into the table; same-bucket pairs from different files are verified structurally; only maximal clones are kept |
| Scorer | `codeclone/scorer.py` | Dice similarity `2 * matched / (total_A + total_B)` |
| Ranking | `codeclone/ranking.py` | Merge sort (descending) and binary search for the threshold cut |
| Graph | `codeclone/graph.py` | Similarity graph (adjacency lists); BFS connected components = clusters |
| Report | `codeclone/report.py` | `report.html` (ranked table, side-by-side highlighted code, clusters) and a console summary |

## CO to data-structure mapping

| CO | Topic | Where it is used |
|---|---|---|
| CO1 | Stacks / Queues | Indentation stack and bracket stack (`lexer.py`); operator and operand stacks (`parser.py`); explicit stacks for iterative traversals (`hasher.py`, `normalizer.py`, `matcher.py`); linked-list queue (`structures.py`) for the BFS printer and BFS clusters |
| CO2 | Linked lists | Each hash-table bucket is a singly linked list of `Entry` cells (`hashtable.py`); the queue is a linked list |
| CO3 | Trees | The AST (`ast_nodes.py`, built by `parser.py`); level-order printing; post-order hashing; subtree matching |
| CO4 | Hashing | Polynomial subtree fingerprints (`hasher.py`); custom chained hash table with rehashing (`hashtable.py`) |
| CO5 | Sorting / Searching / Graphs | Merge sort and binary search (`ranking.py`); similarity graph with BFS components (`graph.py`) |

Search the code for `# CO` to see each use marked in place.

## Time complexity

Notation: `L` = characters of source, `N` = total AST nodes across all files, `n` = files,
`d` = tree depth, `b` = entries in a bucket, `C` = clones found.

| Stage | Complexity | Notes |
|---|---|---|
| Lexer | O(L) | one pass; each stack push/pop O(1) |
| Parser (shunting-yard) | O(T) for T tokens | every operator pushed and popped once |
| Normalizer | O(N) | one iterative walk |
| Hasher | O(N log d)* | post-order; `pow(P, k, M)` per child (*O(N) with precomputed powers) |
| HashTable insert | O(1) average, O(N) total | rehash is O(N) but amortized O(1) per insert |
| Matcher | O(N + Σ b² · s) | pair scan inside each bucket, `s` = size of the structural check |
| Scorer | O(n² + C · s) | every pair of files gets a score |
| Merge sort | O(P log P), P = n(n-1)/2 | |
| Binary search | O(log P) | |
| BFS clusters | O(n + E) | E = flagged pairs |
| Report | O(P + size of flagged sources) | |

Overall the cost is dominated by the O(n²) pair scoring for large classes. Matching itself is
close to linear in the total code size.

## How to run

Requires Python 3.8+ and nothing else.

```bash
python main.py dataset/ --threshold 0.6 --min-mass 6   # writes report.html
python evaluate.py                                      # precision/recall + timing
python -m unittest discover tests -v                    # 26 tests
python -m codeclone.ast_print dataset/p5_fact_original.py  # print an AST level by level
```

Options: `--threshold` is the similarity cutoff for flagging (0–1). `--min-mass` is the
smallest subtree, in nodes, that counts as a clone. `--out` sets the report path.

## Dataset and evaluation

`dataset/` has 6 original programs (gcd, primes, bubble sort, fibonacci, factorial/nCr,
search). Each comes with 7 variants: `copy_comments`, `renamed`, `reordered`, `swapped`,
`deadcode`, `forwhile` and `different` (a different algorithm for the same task). There are
also 3 unrelated programs, giving 51 files and 1275 pairs. A pair counts as true plagiarism
when both files come from the same program and neither one is `different`, which gives 126
positive pairs.

Results of `python evaluate.py`:

| threshold | precision | recall |
|---|---|---|
| 0.4 | 1.000 | 0.841 |
| 0.5 | 1.000 | 0.635 |
| 0.6 | 1.000 | 0.595 |
| 0.7 | 1.000 | 0.476 |
| 0.8 | 1.000 | 0.476 |

At threshold 0.6, every copy_comments, renamed, swapped and reordered variant is detected
(6/6 each). Only 2/6 deadcode and 1/6 forwhile variants are detected. Those are Type-3
clones, which exact subtree matching only partly catches (see Limitations). Running time
grows roughly quadratically: 0.02 s for 51 files and about 0.5 s for 200.

## Literature survey

- **MOSS** (Schleimer, Wilkerson, Aiken, *"Winnowing: Local Algorithms for Document
  Fingerprinting"*, SIGMOD 2003). MOSS hashes k-grams of the token stream and keeps a
  guaranteed subset of fingerprints chosen by *winnowing* (the minimum hash in each sliding
  window). It is fast and language-independent but works on tokens, not structure. Our
  detector also uses hash fingerprints, but over AST subtrees instead of token k-grams.
- **JPlag** (Prechelt, Malpohl, Philippsen, *"Finding Plagiarisms among a Set of
  Programs with JPlag"*, 2002). JPlag turns programs into token strings and compares them
  with *Greedy String Tiling* plus Karp–Rabin hashing, reporting the share of tokens covered
  by tiles. Our Dice score over matched nodes plays the same role as JPlag's coverage
  percentage.
- **CloneDR** (Baxter, Yahin, Moura, Sant'Anna, Bier, *"Clone Detection Using Abstract
  Syntax Trees"*, ICSM 1998). CloneDR hashes AST subtrees into buckets, compares subtrees
  within a bucket, and keeps only maximal clones. This project follows CloneDR's approach
  most closely: subtree hashing, a mass threshold, bucket-wise comparison and the maximal
  clone filter.

## Limitations

- **Type-4 (semantic) clones are not detected.** The same task solved with a different
  algorithm (for example, the sieve versus trial division) scores low by design.
- **Type-3 clones are only partly detected.** Inserted dead code or a `for` rewritten as a
  `while` changes the enclosing blocks, so only the unchanged statements still match.
  Lowering `--min-mass` helps a little.
- **Language subset only:** assignments (`=`, `+=` and similar), arithmetic, comparisons,
  `and`/`or`/`not`, `if`/`elif`/`else`, `while`, `for ... in ...`, `def`/`return`, calls,
  integer and string literals, lists and indexing, `pass`/`break`/`continue`. Classes,
  floats, dictionaries, tuple unpacking, imports, `try`, lambdas, slicing and attribute
  access (`x.y`) are not supported. Files that fail to parse are skipped with a warning.
- `and`/`or` are treated as commutative, as the specification asks, even though Python
  short-circuits them.
- Pair scoring is O(n²) in the number of files, which is fine for a class but not for a
  large archive.
