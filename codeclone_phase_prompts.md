# CodeClone Detector: Phase Prompts

Three phases. Paste each prompt into your AI coding assistant in order, and finish and test one phase before starting the next.

**Project:** A DSA-based source code plagiarism detector written in Python. Input is a small subset of Python.
**CO mapping:** CO1 Stacks/Queues · CO2 Linked Lists · CO3 Trees · CO4 Hashing · CO5 Sorting/Searching/Graphs

---

## Phase 1: Lexer + Parser + AST (CO1, CO3)

```
Build Phase 1 of a Python project called "CodeClone Detector", a source code plagiarism detector
for a Data Structures micro-project. Do NOT use Python's built-in `ast` or `tokenize` modules;
I must implement the data structures myself.

Input language: a small Python subset only:
- assignments, arithmetic (+ - * / %), comparisons (== != < > <= >=), boolean (and or not)
- if / elif / else, while, for VAR in range(...)
- def with parameters, return, function calls, print(...)
- integer and string literals, comments (#) ignored

Create these files:

1. ast_nodes.py
   - class Node: label (e.g. "Assign", "If", "BinOp:+", "Name", "Num"), value, children (list),
     start_line, end_line, plus fields `size` and `hash` (filled later).

2. lexer.py
   - Tokenizer producing tokens (type, value, line).
   - Use an explicit STACK of indentation levels (like CPython) to emit INDENT and DEDENT tokens.
     Raise a clear error on inconsistent dedent.
   - Use a STACK to check balanced parentheses.

3. parser.py
   - Recursive-descent parser for statements/blocks.
   - Parse expressions with the SHUNTING-YARD algorithm (operator stack -> postfix), then build the
     expression subtree using an operand stack. Handle precedence and unary `not` / unary minus.
   - Returns the root Node("Module").

4. ast_print.py
   - Pretty-print the AST using a QUEUE (level-order / BFS traversal).

5. tests/test_phase1.py
   - At least 5 sample programs (factorial, primes, bubble sort, gcd, fibonacci) that parse
     without error.

Keep code simple, commented, and student-readable. In comments, mark exactly where each stack
and queue is used and which CO it demonstrates. Show me a demo run printing the AST of factorial.
```

---

## Phase 2: Normalize + Hash + Match (CO1, CO2, CO3, CO4)

```
Continue the CodeClone Detector. Phase 1 (lexer.py, parser.py, ast_nodes.py) is done.
Now build the detection core. No built-in dict/set for the main fingerprint table; implement it myself.

1. normalizer.py
   - Walk the AST and replace: variable/parameter names -> "VAR", function names -> "FUNC",
     numbers -> "NUM", strings -> "STR". This defeats variable renaming.
   - For commutative operators (+, *, ==, !=, and, or), children will be ordered by hash later
     so that a+b and b+a match.

2. hasher.py
   - ITERATIVE post-order traversal using an explicit STACK (no recursion).
   - For each node compute size (node count) and hash:
       hash(leaf) = H(label)
       hash(node) = (H(label)*P^k + sum(hash(child_i) * P^(k-i))) mod M
       with P = 131, M = 2**61 - 1. Sort child hashes first for commutative operators.

3. hashtable.py
   - Custom hash table with SEPARATE CHAINING: each bucket is a singly LINKED LIST of
     entries (fingerprint, file_id, node). Methods: insert, get_bucket, load_factor, and
     rehash when load factor > 0.75.

4. matcher.py
   - Insert every subtree with size >= MIN_MASS (default 6) from every file into the table.
   - For buckets holding nodes from 2+ different files, form candidate pairs.
   - Verify each candidate with a structural-equality check (handles hash collisions).
   - Keep only MAXIMAL clones: drop a match if its parents also match.
   - Output clone pairs: (fileA, linesA, fileB, linesB, size).

5. scorer.py
   - similarity(A, B) = 2 * matched_nodes / (total_nodes_A + total_nodes_B)  (Dice coefficient)

6. tests/test_phase2.py
   - Prove these are detected: exact copy, all variables renamed, functions reordered,
     a+b swapped to b+a, extra comments. Prove two unrelated programs score low.

Comment where the stack, linked list, tree, and hashing are used, with CO labels.
```

---

## Phase 3: Ranking + Graph + Report + Evaluation (CO5)

```
Finish the CodeClone Detector. Phases 1 and 2 are done (parser, normalizer, hasher,
custom hash table, matcher, scorer). Now add the final layer and the CLI.

1. ranking.py
   - Implement MERGE SORT myself to sort file pairs by similarity (descending).
   - Implement BINARY SEARCH on the sorted list to return all pairs above a threshold.

2. graph.py
   - Build a similarity GRAPH: files are vertices; add an edge when similarity >= threshold.
   - Find connected components with BFS (using my own queue) to detect plagiarism clusters
     (e.g. 4 students sharing one solution).

3. report.py
   - Generate report.html: ranked pair table with similarity %, matched line ranges shown
     side by side with highlighting, and the list of clusters.
   - Also print a short text summary to the console.

4. main.py (CLI)
   python main.py <folder_of_.py_submissions> --threshold 0.6 --min-mass 6

5. dataset/ + evaluate.py
   - Create 6 original programs and, for each, variants: exact copy+comments, renamed
     variables, reordered functions, swapped operands, dead code inserted, for->while,
     and a completely different algorithm. Add a few unrelated programs.
   - evaluate.py prints precision and recall at thresholds 0.4–0.8 and the running time
     vs number of files.

6. README.md with: problem statement, architecture pipeline
   (Lexer -> Parser -> Normalizer -> Hasher -> HashTable -> Matcher -> Scorer -> Graph -> Report),
   a CO-to-data-structure mapping table, time complexity of each stage, how to run,
   and limitations (Type-4 semantic clones not detected; language subset only).
```

---

## Done checklist
- [x] Phase 1: AST prints correctly for 5 programs
- [x] Phase 2: renamed/reordered copies are detected, unrelated code scores low
- [x] Phase 3: `main.py` produces report.html, and evaluate.py gives precision/recall
- [x] Add a literature-survey section to the report: MOSS (winnowing, Schleimer et al. 2003), JPlag (Prechelt 2002), CloneDR (Baxter et al. 1998)
