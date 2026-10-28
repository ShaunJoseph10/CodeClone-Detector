"""Lexer: turns source text into a list of tokens (type, value, line).

Token types: NAME, KEYWORD, NUM, STR, OP, NEWLINE, INDENT, DEDENT, EOF
"""

from .structures import Stack

KEYWORDS = {
    "def", "return", "if", "elif", "else", "while", "for", "in",
    "and", "or", "not", "True", "False", "None", "pass", "break", "continue",
}

# Two-character operators are checked before one-character ones.
TWO_CHAR_OPS = {"==", "!=", "<=", ">=", "+=", "-=", "*=", "/=", "%=", "//"}
ONE_CHAR_OPS = set("+-*/%<>=()[]:,.")
CLOSING = {")": "(", "]": "["}


class LexerError(Exception):
    pass


class Token:
    def __init__(self, type_, value, line):
        self.type = type_
        self.value = value
        self.line = line

    def __repr__(self):
        return "Token(%s, %r, %d)" % (self.type, self.value, self.line)


def tokenize(source):
    tokens = []

    # CO1: stack of indentation levels (same idea as CPython). Bottom is always 0.
    indent_stack = Stack()
    indent_stack.push(0)

    # CO1: stack used to check that ( ) and [ ] are balanced.
    paren_stack = Stack()

    lines = source.split("\n")
    for line_no, raw in enumerate(lines, start=1):
        line = raw.replace("\t", "    ")
        stripped = line.strip()

        # Inside open brackets a line is a continuation: no indentation handling.
        if paren_stack.is_empty():
            if stripped == "" or stripped.startswith("#"):
                continue  # blank lines and comment-only lines are ignored

            indent = len(line) - len(line.lstrip(" "))
            if indent > indent_stack.peek():
                indent_stack.push(indent)
                tokens.append(Token("INDENT", indent, line_no))
            else:
                # Pop every deeper level; each pop is one DEDENT.
                while indent < indent_stack.peek():
                    indent_stack.pop()
                    tokens.append(Token("DEDENT", indent, line_no))
                if indent != indent_stack.peek():
                    raise LexerError("line %d: inconsistent dedent (indent %d matches no outer block)"
                                     % (line_no, indent))

        i = 0
        n = len(line)
        while i < n:
            ch = line[i]
            if ch == " ":
                i += 1
            elif ch == "#":
                break  # rest of the line is a comment
            elif ch.isdigit():
                j = i
                while j < n and line[j].isdigit():
                    j += 1
                tokens.append(Token("NUM", int(line[i:j]), line_no))
                i = j
            elif ch.isalpha() or ch == "_":
                j = i
                while j < n and (line[j].isalnum() or line[j] == "_"):
                    j += 1
                word = line[i:j]
                tokens.append(Token("KEYWORD" if word in KEYWORDS else "NAME", word, line_no))
                i = j
            elif ch in "'\"":
                j = i + 1
                while j < n and line[j] != ch:
                    j += 2 if line[j] == "\\" else 1
                if j >= n:
                    raise LexerError("line %d: unterminated string" % line_no)
                tokens.append(Token("STR", line[i + 1:j], line_no))
                i = j + 1
            elif line[i:i + 2] in TWO_CHAR_OPS:
                tokens.append(Token("OP", line[i:i + 2], line_no))
                i += 2
            elif ch in ONE_CHAR_OPS:
                if ch in "([":
                    paren_stack.push((ch, line_no))  # CO1: push opening bracket
                elif ch in ")]":
                    if paren_stack.is_empty() or paren_stack.peek()[0] != CLOSING[ch]:
                        raise LexerError("line %d: unmatched '%s'" % (line_no, ch))
                    paren_stack.pop()  # CO1: pop matching bracket
                tokens.append(Token("OP", ch, line_no))
                i += 1
            else:
                raise LexerError("line %d: unexpected character %r" % (line_no, ch))

        # A logical line ends only when every bracket is closed.
        if paren_stack.is_empty() and tokens and tokens[-1].type not in ("NEWLINE", "INDENT", "DEDENT"):
            tokens.append(Token("NEWLINE", None, line_no))

    if not paren_stack.is_empty():
        ch, opened = paren_stack.peek()
        raise LexerError("line %d: '%s' was never closed" % (opened, ch))

    last = len(lines)
    while indent_stack.peek() > 0:  # close all open blocks at end of file
        indent_stack.pop()
        tokens.append(Token("DEDENT", 0, last))
    tokens.append(Token("EOF", None, last))
    return tokens
