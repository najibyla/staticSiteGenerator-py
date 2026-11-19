import unittest
from block_markdown import (
    markdown_to_blocks,
    block_to_block_type,
    BlockType,
    markdown_to_html_node,
    extract_title,
)


class TestMarkdownToBlocks(unittest.TestCase):
    # The example from the lesson. Note the multiline string is not
    # indented: a tab or spaces would become part of each line.
    def test_markdown_to_blocks(self):
        md = """
This is **bolded** paragraph

This is another paragraph with _italic_ text and `code` here
This is the same paragraph on a new line

- This is a list
- with items
"""
        blocks = markdown_to_blocks(md)
        self.assertEqual(
            blocks,
            [
                "This is **bolded** paragraph",
                "This is another paragraph with _italic_ text and `code` here\nThis is the same paragraph on a new line",
                "- This is a list\n- with items",
            ],
        )

    # A heading, a paragraph and a list: three blocks.
    def test_heading_paragraph_list(self):
        md = """# This is a heading

This is a paragraph of text. It has some **bold** and _italic_ words inside of it.

- This is the first list item in a list block
- This is a list item
- This is another list item"""
        self.assertEqual(
            markdown_to_blocks(md),
            [
                "# This is a heading",
                "This is a paragraph of text. It has some **bold** and _italic_ words inside of it.",
                "- This is the first list item in a list block\n- This is a list item\n- This is another list item",
            ],
        )

    # One paragraph with no blank lines is a single block.
    def test_single_block(self):
        self.assertEqual(
            markdown_to_blocks("Just one paragraph"),
            ["Just one paragraph"],
        )

    # Newlines inside a block are kept; only blank lines separate blocks.
    def test_newlines_within_block_are_kept(self):
        md = "line one\nline two\nline three"
        self.assertEqual(markdown_to_blocks(md), ["line one\nline two\nline three"])

    # Extra blank lines between blocks produce empty pieces, which are
    # dropped rather than returned as empty blocks.
    def test_excessive_newlines(self):
        md = "first block\n\n\n\n\nsecond block"
        self.assertEqual(markdown_to_blocks(md), ["first block", "second block"])

    # Leading and trailing blank lines around the whole document.
    def test_leading_and_trailing_newlines(self):
        md = "\n\n\nonly block\n\n\n"
        self.assertEqual(markdown_to_blocks(md), ["only block"])

    # Whitespace around a block is stripped.
    def test_strips_whitespace(self):
        md = "   padded block   \n\n\t tabbed block \t"
        self.assertEqual(markdown_to_blocks(md), ["padded block", "tabbed block"])

    # An empty document has no blocks.
    def test_empty_string(self):
        self.assertEqual(markdown_to_blocks(""), [])

    # A document of nothing but whitespace likewise.
    def test_only_whitespace(self):
        self.assertEqual(markdown_to_blocks("   \n\n  \n\n\t"), [])

    # A block that is only a blank line between two others disappears,
    # leaving the real blocks in order.
    def test_blank_block_between_two_blocks(self):
        md = "one\n\n   \n\ntwo"
        self.assertEqual(markdown_to_blocks(md), ["one", "two"])

    # Several different block types in one document, kept in order.
    def test_many_blocks_in_order(self):
        md = """# Heading

paragraph one

> a quote

```
code block
```

1. ordered one
2. ordered two"""
        self.assertEqual(
            markdown_to_blocks(md),
            [
                "# Heading",
                "paragraph one",
                "> a quote",
                "```\ncode block\n```",
                "1. ordered one\n2. ordered two",
            ],
        )



class TestBlockToBlockType(unittest.TestCase):
    # --- headings ---

    def test_heading_one_hash(self):
        self.assertEqual(block_to_block_type("# Heading"), BlockType.HEADING)

    # Every level from 1 to 6 counts as a heading.
    def test_heading_all_levels(self):
        for level in range(1, 7):
            block = "#" * level + " Heading"
            self.assertEqual(block_to_block_type(block), BlockType.HEADING, block)

    # Seven "#" is past the limit, so it is just a paragraph.
    def test_heading_seven_hashes_is_paragraph(self):
        self.assertEqual(
            block_to_block_type("####### Too many"), BlockType.PARAGRAPH
        )

    # The space after the "#" is required.
    def test_heading_without_space_is_paragraph(self):
        self.assertEqual(block_to_block_type("#NoSpace"), BlockType.PARAGRAPH)

    # --- code ---

    def test_code_block(self):
        self.assertEqual(
            block_to_block_type("```\nprint('hi')\n```"), BlockType.CODE
        )

    # A language after the opening fence is still a code block.
    def test_code_block_with_language(self):
        self.assertEqual(
            block_to_block_type("```python\nx = 1\n```"), BlockType.CODE
        )

    # Several lines between the fences.
    def test_code_block_multiline(self):
        block = "```\nline one\nline two\nline three\n```"
        self.assertEqual(block_to_block_type(block), BlockType.CODE)

    # No newline between the fences: not a multiline code block.
    def test_code_single_line_is_paragraph(self):
        self.assertEqual(block_to_block_type("```inline```"), BlockType.PARAGRAPH)

    # Opened but never closed.
    def test_code_unclosed_is_paragraph(self):
        self.assertEqual(
            block_to_block_type("```\nnever closed"), BlockType.PARAGRAPH
        )

    # A bare fence is too short to be both the opening and the closing.
    def test_code_bare_fence_is_paragraph(self):
        self.assertEqual(block_to_block_type("```"), BlockType.PARAGRAPH)

    # --- quotes ---

    def test_quote_single_line(self):
        self.assertEqual(block_to_block_type("> a quote"), BlockType.QUOTE)

    def test_quote_multiple_lines(self):
        self.assertEqual(
            block_to_block_type("> line one\n> line two"), BlockType.QUOTE
        )

    # A space after ">" is allowed but not required.
    def test_quote_without_space(self):
        self.assertEqual(block_to_block_type(">no space"), BlockType.QUOTE)

    # One line missing its ">" means the whole block is a paragraph.
    def test_quote_with_one_bad_line_is_paragraph(self):
        self.assertEqual(
            block_to_block_type("> quoted\nnot quoted"), BlockType.PARAGRAPH
        )

    # --- unordered lists ---

    def test_unordered_list_single_item(self):
        self.assertEqual(block_to_block_type("- item"), BlockType.UNORDERED_LIST)

    def test_unordered_list_multiple_items(self):
        self.assertEqual(
            block_to_block_type("- one\n- two\n- three"),
            BlockType.UNORDERED_LIST,
        )

    # The space after the "-" is required.
    def test_unordered_list_without_space_is_paragraph(self):
        self.assertEqual(block_to_block_type("-nospace"), BlockType.PARAGRAPH)

    def test_unordered_list_with_one_bad_line_is_paragraph(self):
        self.assertEqual(
            block_to_block_type("- one\nnot an item"), BlockType.PARAGRAPH
        )

    # --- ordered lists ---

    def test_ordered_list_single_item(self):
        self.assertEqual(block_to_block_type("1. item"), BlockType.ORDERED_LIST)

    def test_ordered_list_multiple_items(self):
        self.assertEqual(
            block_to_block_type("1. one\n2. two\n3. three"),
            BlockType.ORDERED_LIST,
        )

    # The numbers must start at 1.
    def test_ordered_list_not_starting_at_one_is_paragraph(self):
        self.assertEqual(
            block_to_block_type("2. two\n3. three"), BlockType.PARAGRAPH
        )

    # They must go up by exactly one each line.
    def test_ordered_list_skipping_a_number_is_paragraph(self):
        self.assertEqual(
            block_to_block_type("1. one\n3. three"), BlockType.PARAGRAPH
        )

    # Out of order is not a list either.
    def test_ordered_list_out_of_order_is_paragraph(self):
        self.assertEqual(
            block_to_block_type("1. one\n3. three\n2. two"), BlockType.PARAGRAPH
        )

    # The space after the "." is required.
    def test_ordered_list_without_space_is_paragraph(self):
        self.assertEqual(block_to_block_type("1.no space"), BlockType.PARAGRAPH)

    # Ten or more items keep counting correctly.
    def test_ordered_list_past_ten(self):
        block = "\n".join(f"{n}. item {n}" for n in range(1, 13))
        self.assertEqual(block_to_block_type(block), BlockType.ORDERED_LIST)

    # --- paragraphs ---

    def test_paragraph(self):
        self.assertEqual(
            block_to_block_type("This is a normal paragraph."),
            BlockType.PARAGRAPH,
        )

    # Inline markdown does not change the block type.
    def test_paragraph_with_inline_markdown(self):
        self.assertEqual(
            block_to_block_type("Some **bold** and _italic_ and `code` here"),
            BlockType.PARAGRAPH,
        )

    def test_paragraph_multiple_lines(self):
        self.assertEqual(
            block_to_block_type("line one\nline two"), BlockType.PARAGRAPH
        )

    # Every block type produced by markdown_to_blocks is classified as
    # expected, which is how the two functions will be used together.
    def test_classifies_a_whole_document(self):
        md = """# Heading

a paragraph

> quoted

- a
- b

1. one
2. two

```
code
```"""
        types = [block_to_block_type(b) for b in markdown_to_blocks(md)]
        self.assertEqual(
            types,
            [
                BlockType.HEADING,
                BlockType.PARAGRAPH,
                BlockType.QUOTE,
                BlockType.UNORDERED_LIST,
                BlockType.ORDERED_LIST,
                BlockType.CODE,
            ],
        )



class TestMarkdownToHTMLNode(unittest.TestCase):
    # The first example from the lesson: two paragraphs, with the
    # newlines inside the first one turned into spaces.
    def test_paragraphs(self):
        md = """
This is **bolded** paragraph
text in a p
tag here

This is another paragraph with _italic_ text and `code` here

"""
        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><p>This is <b>bolded</b> paragraph text in a p tag here</p><p>This is another paragraph with <i>italic</i> text and <code>code</code> here</p></div>",
        )

    # The second example: a code block keeps its markdown literally, and
    # keeps its newlines.
    def test_codeblock(self):
        md = """
```
This is text that _should_ remain
the **same** even with inline stuff
```
"""
        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><pre><code>This is text that _should_ remain\nthe **same** even with inline stuff\n</code></pre></div>",
        )

    # A single paragraph with no inline markdown at all.
    def test_single_plain_paragraph(self):
        self.assertEqual(
            markdown_to_html_node("Just some words").to_html(),
            "<div><p>Just some words</p></div>",
        )

    # Each heading level maps to its own tag.
    def test_all_heading_levels(self):
        for level in range(1, 7):
            md = "#" * level + " Heading text"
            self.assertEqual(
                markdown_to_html_node(md).to_html(),
                f"<div><h{level}>Heading text</h{level}></div>",
                md,
            )

    # Inline markdown inside a heading is still parsed.
    def test_heading_with_inline_markdown(self):
        self.assertEqual(
            markdown_to_html_node("## A **bold** heading").to_html(),
            "<div><h2>A <b>bold</b> heading</h2></div>",
        )

    # A code block with a language tag: the tag line is dropped, and the
    # body is still left unparsed.
    def test_codeblock_with_language(self):
        md = "```python\nx = **1**\n```"
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            "<div><pre><code>x = **1**\n</code></pre></div>",
        )

    # A one-line quote.
    def test_quote_single_line(self):
        self.assertEqual(
            markdown_to_html_node("> a wise remark").to_html(),
            "<div><blockquote>a wise remark</blockquote></div>",
        )

    # A quote over several lines becomes one blockquote, with the ">"
    # markers removed and the lines joined.
    def test_quote_multiple_lines(self):
        md = "> line one\n> line two\n> line three"
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            "<div><blockquote>line one line two line three</blockquote></div>",
        )

    # A bare ">" is a blank line within the quote: it separates the
    # lines but must not leave a double space in the joined text.
    def test_quote_with_blank_line(self):
        md = "> first line\n>\n> second line"
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            "<div><blockquote>first line second line</blockquote></div>",
        )

    # Inline markdown works inside a quote too.
    def test_quote_with_inline_markdown(self):
        self.assertEqual(
            markdown_to_html_node("> a **bold** remark").to_html(),
            "<div><blockquote>a <b>bold</b> remark</blockquote></div>",
        )

    # Each item of an unordered list gets its own <li>.
    def test_unordered_list(self):
        md = "- first\n- second\n- third"
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            "<div><ul><li>first</li><li>second</li><li>third</li></ul></div>",
        )

    def test_unordered_list_with_inline_markdown(self):
        md = "- plain\n- with **bold**\n- with `code`"
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            "<div><ul><li>plain</li><li>with <b>bold</b></li><li>with <code>code</code></li></ul></div>",
        )

    # Ordered lists use <ol>, and the numbers themselves are dropped.
    def test_ordered_list(self):
        md = "1. first\n2. second\n3. third"
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            "<div><ol><li>first</li><li>second</li><li>third</li></ol></div>",
        )

    # Past item nine the marker is longer, so the text must still start
    # in the right place.
    def test_ordered_list_past_ten(self):
        md = "\n".join(f"{n}. item {n}" for n in range(1, 12))
        html = markdown_to_html_node(md).to_html()
        self.assertIn("<li>item 10</li>", html)
        self.assertIn("<li>item 11</li>", html)

    # Links and images inside a paragraph.
    def test_paragraph_with_link_and_image(self):
        md = "See [boot dev](https://boot.dev) and ![cat](/cat.png)"
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            '<div><p>See <a href="https://boot.dev">boot dev</a> and <img src="/cat.png" alt="cat"></img></p></div>',
        )

    # An empty document produces an empty div rather than failing.
    def test_empty_markdown(self):
        self.assertEqual(markdown_to_html_node("").to_html(), "<div></div>")

    # A whole document of mixed blocks, in order: this is the shape the
    # generator will actually produce.
    def test_full_document(self):
        md = """# Title

An **intro** paragraph.

- one
- two

1. first
2. second

> quoted words

```
raw _code_ here
```"""
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            "<div>"
            "<h1>Title</h1>"
            "<p>An <b>intro</b> paragraph.</p>"
            "<ul><li>one</li><li>two</li></ul>"
            "<ol><li>first</li><li>second</li></ol>"
            "<blockquote>quoted words</blockquote>"
            "<pre><code>raw _code_ here\n</code></pre>"
            "</div>",
        )

    # The top level is always a single div parent.
    def test_root_is_a_div(self):
        node = markdown_to_html_node("# Heading\n\nparagraph")
        self.assertEqual(node.tag, "div")
        self.assertEqual(len(node.children), 2)



class TestExtractTitle(unittest.TestCase):
    # The example from the lesson.
    def test_extract_title(self):
        self.assertEqual(extract_title("# Hello"), "Hello")

    # Surrounding whitespace is stripped from the title text.
    def test_extract_title_strips_whitespace(self):
        self.assertEqual(extract_title("#    Padded title   "), "Padded title")

    # The heading does not have to be the first line.
    def test_extract_title_not_first_line(self):
        md = "Some intro text\n\n# The Real Title\n\nmore text"
        self.assertEqual(extract_title(md), "The Real Title")

    # Only the first h1 is used when there is more than one.
    def test_extract_title_first_of_several(self):
        md = "# First\n\n# Second"
        self.assertEqual(extract_title(md), "First")

    # An h2 is not an h1: "## " does not start with "# ".
    def test_extract_title_ignores_h2(self):
        md = "## Not a title\n\n# Actual title"
        self.assertEqual(extract_title(md), "Actual title")

    # Inline markdown in the heading is returned as written, since the
    # title goes into a <title> tag where markup has no meaning.
    def test_extract_title_keeps_inline_markdown(self):
        self.assertEqual(extract_title("# A **bold** title"), "A **bold** title")

    # No h1 anywhere: there is no title to return.
    def test_extract_title_no_h1_raises(self):
        with self.assertRaises(ValueError):
            extract_title("## Only an h2\n\nsome text")

    # A "#" with no space is not a heading.
    def test_extract_title_hash_without_space_raises(self):
        with self.assertRaises(ValueError):
            extract_title("#NoSpace")

    def test_extract_title_empty_document_raises(self):
        with self.assertRaises(ValueError):
            extract_title("")

    # The real page's title, end to end.
    def test_extract_title_from_site_content(self):
        md = "# Tolkien Fan Club\n\n![img](/images/tolkien.png)\n\n## Blog posts"
        self.assertEqual(extract_title(md), "Tolkien Fan Club")


if __name__ == "__main__":
    unittest.main()
