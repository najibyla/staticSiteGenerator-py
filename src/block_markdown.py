import re
from enum import Enum

from htmlnode import ParentNode
from inline_markdown import text_to_textnodes
from textnode import TextNode, TextType, text_node_to_html_node


class BlockType(Enum):
    # The six kinds of top-level block a markdown document can contain.
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    CODE = "code"
    QUOTE = "quote"
    UNORDERED_LIST = "unordered_list"
    ORDERED_LIST = "ordered_list"


def markdown_to_blocks(markdown: str) -> list[str]:
    # Split a whole markdown document into its top-level blocks. Blocks
    # are separated by a blank line, which in the raw text is a double
    # newline.
    blocks = []

    for raw_block in markdown.split("\n\n"):
        # Trim the newline left on each end by the split, plus any
        # indentation the document happened to carry. Newlines *inside*
        # a block are kept, so a paragraph written over two lines stays
        # a single block.
        block = raw_block.strip()

        # Three or more newlines in a row produce empty pieces, and so
        # does a document that starts or ends with a blank line. None of
        # those are real blocks.
        if block == "":
            continue

        blocks.append(block)

    return blocks


def block_to_block_type(block: str) -> BlockType:
    # Work out what kind of block this is. The block is assumed to be
    # already stripped of leading and trailing whitespace, which
    # markdown_to_blocks above takes care of.
    lines = block.split("\n")

    # One to six "#" then a space. Seven or more is not a heading: the
    # regex cannot match, because after at most six "#" it needs a space
    # and finds another "#" instead.
    if re.match(r"#{1,6} ", block):
        return BlockType.HEADING

    # A fenced code block opens with ``` and closes with ```, with at
    # least one newline between the fences. The length check stops a bare
    # "```" (which starts and ends with the same three characters) from
    # counting as a whole block.
    if len(block) >= 6 and block.startswith("```") and block.endswith("```") and "\n" in block:
        return BlockType.CODE

    # For the remaining three, every line has to match, not just the
    # first. all() over a generator stops at the first line that fails.
    if all(line.startswith(">") for line in lines):
        return BlockType.QUOTE

    # The space after "-" is required, so "-dash" is not a list.
    if all(line.startswith("- ") for line in lines):
        return BlockType.UNORDERED_LIST

    # The numbers must start at 1 and go up by one each line, so
    # enumerate gives the number each line ought to begin with.
    if all(
        line.startswith(f"{number}. ")
        for number, line in enumerate(lines, start=1)
    ):
        return BlockType.ORDERED_LIST

    # Anything else is just a paragraph.
    return BlockType.PARAGRAPH


def text_to_children(text: str) -> list:
    # Parse a string of inline markdown into the HTML nodes it describes.
    # Shared by every block type except code, which must not have its
    # contents parsed.
    return [text_node_to_html_node(node) for node in text_to_textnodes(text)]


def _paragraph_to_html_node(block):
    # A paragraph written over several lines is one paragraph, so the
    # newlines become spaces rather than being kept.
    paragraph = " ".join(block.split("\n"))
    return ParentNode("p", text_to_children(paragraph))


def _heading_to_html_node(block):
    # The number of "#" characters is the heading level, so "###" is an
    # <h3>. The text starts after the "#"s and the space that follows.
    level = len(block) - len(block.lstrip("#"))
    text = block[level + 1 :]
    return ParentNode(f"h{level}", text_to_children(text))


def _code_to_html_node(block):
    # Strip the opening and closing ``` fences, then drop the rest of the
    # opening fence's line, which is either empty or a language tag. The
    # trailing newline before the closing fence is deliberately kept.
    inner = block[3:-3]
    if "\n" in inner:
        inner = inner.split("\n", 1)[1]

    # Code is literal: no inline parsing, so the text goes straight into
    # a single raw-text node rather than through text_to_children.
    text_node = text_node_to_html_node(TextNode(inner, TextType.TEXT))
    return ParentNode("pre", [ParentNode("code", [text_node])])


def _quote_to_html_node(block):
    # Drop the ">" from each line, and any space after it, then join the
    # lines back into one run of text.
    lines = []
    for line in block.split("\n"):
        text = line.lstrip(">").strip()
        # A bare ">" is a blank line inside the quote. Keeping it would
        # put a double space in the middle of the joined text.
        if text == "":
            continue
        lines.append(text)
    return ParentNode("blockquote", text_to_children(" ".join(lines)))


def _unordered_list_to_html_node(block):
    # Each line is one item; "- " is the marker, so the text starts at
    # character 2.
    items = []
    for line in block.split("\n"):
        items.append(ParentNode("li", text_to_children(line[2:])))
    return ParentNode("ul", items)


def _ordered_list_to_html_node(block):
    # Same idea, but the marker length varies with the number, so the
    # text starts after "N. " for whatever N that line carries.
    items = []
    for number, line in enumerate(block.split("\n"), start=1):
        text = line[len(f"{number}. ") :]
        items.append(ParentNode("li", text_to_children(text)))
    return ParentNode("ol", items)


# Which builder handles which block type.
_BLOCK_BUILDERS = {
    BlockType.PARAGRAPH: _paragraph_to_html_node,
    BlockType.HEADING: _heading_to_html_node,
    BlockType.CODE: _code_to_html_node,
    BlockType.QUOTE: _quote_to_html_node,
    BlockType.UNORDERED_LIST: _unordered_list_to_html_node,
    BlockType.ORDERED_LIST: _ordered_list_to_html_node,
}


def markdown_to_html_node(markdown: str):
    # Convert a whole markdown document into one <div> holding a node per
    # block, each with its own inline content as children.
    children = []

    for block in markdown_to_blocks(markdown):
        block_type = block_to_block_type(block)
        children.append(_BLOCK_BUILDERS[block_type](block))

    return ParentNode("div", children)


def extract_title(markdown: str) -> str:
    # Pull the page title out of the document: the text of its single "#"
    # heading. Raises if the document has none, since every page needs a
    # title.
    for line in markdown.split("\n"):
        # "# " with the space means only an h1 matches; "## Blog posts"
        # starts with "#" but not with "# ", so it is skipped.
        if line.startswith("# "):
            return line[2:].strip()

    raise ValueError("no h1 header found in markdown")
