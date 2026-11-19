import unittest
from textnode import TextNode, TextType
from inline_markdown import (
    split_nodes_delimiter,
    extract_markdown_images,
    extract_markdown_links,
    split_nodes_image,
    split_nodes_link,
    text_to_textnodes,
)


class TestSplitNodesDelimiter(unittest.TestCase):
    # The example from the lesson: backtick delimiters become code nodes.
    def test_code_block(self):
        node = TextNode("This is text with a `code block` word", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "`", TextType.CODE)
        self.assertEqual(
            new_nodes,
            [
                TextNode("This is text with a ", TextType.TEXT),
                TextNode("code block", TextType.CODE),
                TextNode(" word", TextType.TEXT),
            ],
        )

    # The same logic with a different delimiter and type.
    def test_bold(self):
        node = TextNode("This is text with a **bolded phrase** in the middle", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "**", TextType.BOLD)
        self.assertEqual(
            new_nodes,
            [
                TextNode("This is text with a ", TextType.TEXT),
                TextNode("bolded phrase", TextType.BOLD),
                TextNode(" in the middle", TextType.TEXT),
            ],
        )

    def test_italic(self):
        node = TextNode("This is _italic_ text", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "_", TextType.ITALIC)
        self.assertEqual(
            new_nodes,
            [
                TextNode("This is ", TextType.TEXT),
                TextNode("italic", TextType.ITALIC),
                TextNode(" text", TextType.TEXT),
            ],
        )

    # Two delimited sections in one string.
    def test_two_delimited_sections(self):
        node = TextNode("**one** middle **two**", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "**", TextType.BOLD)
        self.assertEqual(
            new_nodes,
            [
                TextNode("one", TextType.BOLD),
                TextNode(" middle ", TextType.TEXT),
                TextNode("two", TextType.BOLD),
            ],
        )

    # A delimiter at the very start leaves no empty node in front.
    def test_delimiter_at_start(self):
        node = TextNode("**bold** then text", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "**", TextType.BOLD)
        self.assertEqual(
            new_nodes,
            [
                TextNode("bold", TextType.BOLD),
                TextNode(" then text", TextType.TEXT),
            ],
        )

    # Likewise at the very end.
    def test_delimiter_at_end(self):
        node = TextNode("text then **bold**", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "**", TextType.BOLD)
        self.assertEqual(
            new_nodes,
            [
                TextNode("text then ", TextType.TEXT),
                TextNode("bold", TextType.BOLD),
            ],
        )

    # The whole string is delimited: one node comes out.
    def test_whole_string_delimited(self):
        node = TextNode("`all code`", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "`", TextType.CODE)
        self.assertEqual(new_nodes, [TextNode("all code", TextType.CODE)])

    # No delimiter present: the node passes through unchanged.
    def test_no_delimiter_present(self):
        node = TextNode("Just plain text", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "`", TextType.CODE)
        self.assertEqual(new_nodes, [TextNode("Just plain text", TextType.TEXT)])

    # Nodes that are not plain text are never split, even when they
    # contain something that looks like a delimiter.
    def test_non_text_nodes_pass_through(self):
        nodes = [
            TextNode("already bold", TextType.BOLD),
            TextNode("code with ` inside", TextType.CODE),
            TextNode("Boot.dev", TextType.LINK, "https://www.boot.dev"),
            TextNode("alt text", TextType.IMAGE, "/img.png"),
        ]
        self.assertEqual(split_nodes_delimiter(nodes, "`", TextType.CODE), nodes)

    # Several input nodes are each handled in turn, in order.
    def test_multiple_input_nodes(self):
        nodes = [
            TextNode("a `one` b", TextType.TEXT),
            TextNode("stays bold", TextType.BOLD),
            TextNode("c `two` d", TextType.TEXT),
        ]
        self.assertEqual(
            split_nodes_delimiter(nodes, "`", TextType.CODE),
            [
                TextNode("a ", TextType.TEXT),
                TextNode("one", TextType.CODE),
                TextNode(" b", TextType.TEXT),
                TextNode("stays bold", TextType.BOLD),
                TextNode("c ", TextType.TEXT),
                TextNode("two", TextType.CODE),
                TextNode(" d", TextType.TEXT),
            ],
        )

    # Successive passes: the bold node from the first pass survives the
    # second pass untouched, and the remaining text is split further.
    def test_successive_passes(self):
        start = [TextNode("Read **this** and `that`.", TextType.TEXT)]
        after_bold = split_nodes_delimiter(start, "**", TextType.BOLD)
        self.assertEqual(
            after_bold,
            [
                TextNode("Read ", TextType.TEXT),
                TextNode("this", TextType.BOLD),
                TextNode(" and `that`.", TextType.TEXT),
            ],
        )
        after_code = split_nodes_delimiter(after_bold, "`", TextType.CODE)
        self.assertEqual(
            after_code,
            [
                TextNode("Read ", TextType.TEXT),
                TextNode("this", TextType.BOLD),
                TextNode(" and ", TextType.TEXT),
                TextNode("that", TextType.CODE),
                TextNode(".", TextType.TEXT),
            ],
        )

    # An opening delimiter with no closing one is invalid markdown.
    def test_unmatched_delimiter_raises(self):
        node = TextNode("This is **unfinished", TextType.TEXT)
        with self.assertRaises(ValueError):
            split_nodes_delimiter([node], "**", TextType.BOLD)

    def test_unmatched_code_delimiter_raises(self):
        node = TextNode("a `b` c `d", TextType.TEXT)
        with self.assertRaises(ValueError):
            split_nodes_delimiter([node], "`", TextType.CODE)

    # Nothing in, nothing out.
    def test_empty_list(self):
        self.assertEqual(split_nodes_delimiter([], "`", TextType.CODE), [])

    # An empty text node produces no nodes at all, rather than an empty
    # one.
    def test_empty_text_node(self):
        node = TextNode("", TextType.TEXT)
        self.assertEqual(split_nodes_delimiter([node], "`", TextType.CODE), [])

    # The input list itself is not modified; a new list is returned.
    def test_does_not_mutate_input(self):
        nodes = [TextNode("a `b` c", TextType.TEXT)]
        split_nodes_delimiter(nodes, "`", TextType.CODE)
        self.assertEqual(nodes, [TextNode("a `b` c", TextType.TEXT)])



class TestExtractMarkdownImages(unittest.TestCase):
    # One image: alt text and url come back as a tuple.
    def test_extract_markdown_images(self):
        matches = extract_markdown_images(
            "This is text with an ![image](https://i.imgur.com/zjjcJKZ.png)"
        )
        self.assertListEqual([("image", "https://i.imgur.com/zjjcJKZ.png")], matches)

    # The example from the lesson: two images in one string, in order.
    def test_extract_two_images(self):
        text = (
            "This is text with a ![rick roll](https://i.imgur.com/aKaOqIh.gif) "
            "and ![obi wan](https://i.imgur.com/fJRm4Vk.jpeg)"
        )
        self.assertListEqual(
            [
                ("rick roll", "https://i.imgur.com/aKaOqIh.gif"),
                ("obi wan", "https://i.imgur.com/fJRm4Vk.jpeg"),
            ],
            extract_markdown_images(text),
        )

    # No images at all gives an empty list, not an error.
    def test_extract_images_none(self):
        self.assertListEqual([], extract_markdown_images("Just plain text"))

    # An image is allowed to have empty alt text.
    def test_extract_image_empty_alt(self):
        self.assertListEqual(
            [("", "https://example.com/pic.png")],
            extract_markdown_images("![](https://example.com/pic.png)"),
        )

    # A plain link is not an image, so it must not be picked up here.
    def test_extract_images_ignores_links(self):
        self.assertListEqual(
            [],
            extract_markdown_images("A [link](https://www.boot.dev) only"),
        )

    # With both present, only the image is returned.
    def test_extract_images_mixed_with_links(self):
        text = "![pic](/a.png) and [link](https://www.boot.dev)"
        self.assertListEqual([("pic", "/a.png")], extract_markdown_images(text))

    # An image at the very start of the string still matches.
    def test_extract_image_at_start(self):
        self.assertListEqual(
            [("first", "/one.png")],
            extract_markdown_images("![first](/one.png) then words"),
        )


class TestExtractMarkdownLinks(unittest.TestCase):
    # One link: anchor text and url.
    def test_extract_markdown_links(self):
        matches = extract_markdown_links(
            "This is text with a [link](https://www.boot.dev)"
        )
        self.assertListEqual([("link", "https://www.boot.dev")], matches)

    # The example from the lesson: two links, in order.
    def test_extract_two_links(self):
        text = (
            "This is text with a link [to boot dev](https://www.boot.dev) "
            "and [to youtube](https://www.youtube.com/@bootdotdev)"
        )
        self.assertListEqual(
            [
                ("to boot dev", "https://www.boot.dev"),
                ("to youtube", "https://www.youtube.com/@bootdotdev"),
            ],
            extract_markdown_links(text),
        )

    def test_extract_links_none(self):
        self.assertListEqual([], extract_markdown_links("Just plain text"))

    # An image must not be mistaken for a link: this is what the (?<!!)
    # lookbehind is for, since an image is a link with "!" in front.
    def test_extract_links_ignores_images(self):
        self.assertListEqual(
            [],
            extract_markdown_links("An ![image](https://i.imgur.com/a.png) only"),
        )

    # With both present, only the link is returned.
    def test_extract_links_mixed_with_images(self):
        text = "![pic](/a.png) and [link](https://www.boot.dev)"
        self.assertListEqual(
            [("link", "https://www.boot.dev")],
            extract_markdown_links(text),
        )

    # Links can have empty anchor text too.
    def test_extract_link_empty_anchor(self):
        self.assertListEqual(
            [("", "https://www.boot.dev")],
            extract_markdown_links("[](https://www.boot.dev)"),
        )

    # A relative url is just as valid as an absolute one.
    def test_extract_link_relative_url(self):
        self.assertListEqual(
            [("about", "/about")],
            extract_markdown_links("Go to [about](/about) now"),
        )

    # Several links and images interleaved: each function picks out only
    # its own kind, in the order they appear.
    def test_extract_interleaved(self):
        text = (
            "[one](/1) ![two](/2.png) [three](/3) ![four](/4.png)"
        )
        self.assertListEqual(
            [("one", "/1"), ("three", "/3")],
            extract_markdown_links(text),
        )
        self.assertListEqual(
            [("two", "/2.png"), ("four", "/4.png")],
            extract_markdown_images(text),
        )



class TestSplitNodesImage(unittest.TestCase):
    # The example from the lesson: two images with text around them.
    def test_split_images(self):
        node = TextNode(
            "This is text with an ![image](https://i.imgur.com/zjjcJKZ.png) and another ![second image](https://i.imgur.com/3elNhQu.png)",
            TextType.TEXT,
        )
        new_nodes = split_nodes_image([node])
        self.assertListEqual(
            [
                TextNode("This is text with an ", TextType.TEXT),
                TextNode("image", TextType.IMAGE, "https://i.imgur.com/zjjcJKZ.png"),
                TextNode(" and another ", TextType.TEXT),
                TextNode("second image", TextType.IMAGE, "https://i.imgur.com/3elNhQu.png"),
            ],
            new_nodes,
        )

    def test_split_single_image(self):
        node = TextNode("Look: ![cat](/cat.png) there", TextType.TEXT)
        self.assertListEqual(
            [
                TextNode("Look: ", TextType.TEXT),
                TextNode("cat", TextType.IMAGE, "/cat.png"),
                TextNode(" there", TextType.TEXT),
            ],
            split_nodes_image([node]),
        )

    # An image at the very start leaves no empty node in front of it.
    def test_split_image_at_start(self):
        node = TextNode("![cat](/cat.png) comes first", TextType.TEXT)
        self.assertListEqual(
            [
                TextNode("cat", TextType.IMAGE, "/cat.png"),
                TextNode(" comes first", TextType.TEXT),
            ],
            split_nodes_image([node]),
        )

    # Likewise at the very end.
    def test_split_image_at_end(self):
        node = TextNode("ends with ![cat](/cat.png)", TextType.TEXT)
        self.assertListEqual(
            [
                TextNode("ends with ", TextType.TEXT),
                TextNode("cat", TextType.IMAGE, "/cat.png"),
            ],
            split_nodes_image([node]),
        )

    # Nothing but an image: a single node comes out.
    def test_split_image_only(self):
        node = TextNode("![cat](/cat.png)", TextType.TEXT)
        self.assertListEqual(
            [TextNode("cat", TextType.IMAGE, "/cat.png")],
            split_nodes_image([node]),
        )

    # Two images with no text between them: no empty node in the middle.
    def test_split_adjacent_images(self):
        node = TextNode("![a](/a.png)![b](/b.png)", TextType.TEXT)
        self.assertListEqual(
            [
                TextNode("a", TextType.IMAGE, "/a.png"),
                TextNode("b", TextType.IMAGE, "/b.png"),
            ],
            split_nodes_image([node]),
        )

    # The same image twice: both are found, not just the first.
    def test_split_duplicate_images(self):
        node = TextNode("![a](/a.png) and ![a](/a.png)", TextType.TEXT)
        self.assertListEqual(
            [
                TextNode("a", TextType.IMAGE, "/a.png"),
                TextNode(" and ", TextType.TEXT),
                TextNode("a", TextType.IMAGE, "/a.png"),
            ],
            split_nodes_image([node]),
        )

    # No images: the node comes back as it was.
    def test_split_images_none_present(self):
        node = TextNode("Just plain text", TextType.TEXT)
        self.assertListEqual([node], split_nodes_image([node]))

    # A plain link is not an image, so it is left alone.
    def test_split_images_ignores_links(self):
        node = TextNode("A [link](https://www.boot.dev) here", TextType.TEXT)
        self.assertListEqual([node], split_nodes_image([node]))

    # An image with empty alt text still becomes an IMAGE node.
    def test_split_image_empty_alt(self):
        node = TextNode("see ![](/cat.png)", TextType.TEXT)
        self.assertListEqual(
            [
                TextNode("see ", TextType.TEXT),
                TextNode("", TextType.IMAGE, "/cat.png"),
            ],
            split_nodes_image([node]),
        )

    # Nodes that are not plain text are never split.
    def test_split_images_non_text_nodes(self):
        nodes = [
            TextNode("already bold", TextType.BOLD),
            TextNode("alt", TextType.IMAGE, "/old.png"),
            TextNode("code ![a](/a.png)", TextType.CODE),
        ]
        self.assertListEqual(nodes, split_nodes_image(nodes))

    # Several input nodes are handled in turn, in order.
    def test_split_images_multiple_input_nodes(self):
        nodes = [
            TextNode("one ![a](/a.png)", TextType.TEXT),
            TextNode("stays bold", TextType.BOLD),
            TextNode("![b](/b.png) two", TextType.TEXT),
        ]
        self.assertListEqual(
            [
                TextNode("one ", TextType.TEXT),
                TextNode("a", TextType.IMAGE, "/a.png"),
                TextNode("stays bold", TextType.BOLD),
                TextNode("b", TextType.IMAGE, "/b.png"),
                TextNode(" two", TextType.TEXT),
            ],
            split_nodes_image(nodes),
        )

    def test_split_images_empty_list(self):
        self.assertListEqual([], split_nodes_image([]))


class TestSplitNodesLink(unittest.TestCase):
    # The example from the lesson: two links with text around them.
    def test_split_links(self):
        node = TextNode(
            "This is text with a link [to boot dev](https://www.boot.dev) and [to youtube](https://www.youtube.com/@bootdotdev)",
            TextType.TEXT,
        )
        self.assertListEqual(
            [
                TextNode("This is text with a link ", TextType.TEXT),
                TextNode("to boot dev", TextType.LINK, "https://www.boot.dev"),
                TextNode(" and ", TextType.TEXT),
                TextNode("to youtube", TextType.LINK, "https://www.youtube.com/@bootdotdev"),
            ],
            split_nodes_link([node]),
        )

    def test_split_single_link(self):
        node = TextNode("Go to [about](/about) now", TextType.TEXT)
        self.assertListEqual(
            [
                TextNode("Go to ", TextType.TEXT),
                TextNode("about", TextType.LINK, "/about"),
                TextNode(" now", TextType.TEXT),
            ],
            split_nodes_link([node]),
        )

    def test_split_link_at_start(self):
        node = TextNode("[about](/about) comes first", TextType.TEXT)
        self.assertListEqual(
            [
                TextNode("about", TextType.LINK, "/about"),
                TextNode(" comes first", TextType.TEXT),
            ],
            split_nodes_link([node]),
        )

    def test_split_link_at_end(self):
        node = TextNode("ends with [about](/about)", TextType.TEXT)
        self.assertListEqual(
            [
                TextNode("ends with ", TextType.TEXT),
                TextNode("about", TextType.LINK, "/about"),
            ],
            split_nodes_link([node]),
        )

    def test_split_link_only(self):
        node = TextNode("[about](/about)", TextType.TEXT)
        self.assertListEqual(
            [TextNode("about", TextType.LINK, "/about")],
            split_nodes_link([node]),
        )

    def test_split_adjacent_links(self):
        node = TextNode("[a](/a)[b](/b)", TextType.TEXT)
        self.assertListEqual(
            [
                TextNode("a", TextType.LINK, "/a"),
                TextNode("b", TextType.LINK, "/b"),
            ],
            split_nodes_link([node]),
        )

    def test_split_links_none_present(self):
        node = TextNode("Just plain text", TextType.TEXT)
        self.assertListEqual([node], split_nodes_link([node]))

    # An image is not a link, so it must be left alone. This is the
    # lookbehind in the link pattern doing its job.
    def test_split_links_ignores_images(self):
        node = TextNode("An ![image](/cat.png) here", TextType.TEXT)
        self.assertListEqual([node], split_nodes_link([node]))

    def test_split_link_empty_anchor(self):
        node = TextNode("see [](/about)", TextType.TEXT)
        self.assertListEqual(
            [
                TextNode("see ", TextType.TEXT),
                TextNode("", TextType.LINK, "/about"),
            ],
            split_nodes_link([node]),
        )

    def test_split_links_non_text_nodes(self):
        nodes = [
            TextNode("already italic", TextType.ITALIC),
            TextNode("anchor", TextType.LINK, "/old"),
        ]
        self.assertListEqual(nodes, split_nodes_link(nodes))

    def test_split_links_empty_list(self):
        self.assertListEqual([], split_nodes_link([]))


class TestSplitImagesAndLinksTogether(unittest.TestCase):
    # Running both passes over one string: each pass handles its own kind
    # and leaves the other's nodes untouched.
    def test_image_pass_then_link_pass(self):
        node = TextNode(
            "![pic](/a.png) then [link](https://www.boot.dev) end",
            TextType.TEXT,
        )
        after_images = split_nodes_image([node])
        self.assertListEqual(
            [
                TextNode("pic", TextType.IMAGE, "/a.png"),
                TextNode(" then [link](https://www.boot.dev) end", TextType.TEXT),
            ],
            after_images,
        )
        self.assertListEqual(
            [
                TextNode("pic", TextType.IMAGE, "/a.png"),
                TextNode(" then ", TextType.TEXT),
                TextNode("link", TextType.LINK, "https://www.boot.dev"),
                TextNode(" end", TextType.TEXT),
            ],
            split_nodes_link(after_images),
        )

    # The order of the two passes does not change the result.
    def test_link_pass_then_image_pass(self):
        node = TextNode(
            "![pic](/a.png) then [link](https://www.boot.dev) end",
            TextType.TEXT,
        )
        after_links = split_nodes_link([node])
        self.assertListEqual(
            [
                TextNode("pic", TextType.IMAGE, "/a.png"),
                TextNode(" then ", TextType.TEXT),
                TextNode("link", TextType.LINK, "https://www.boot.dev"),
                TextNode(" end", TextType.TEXT),
            ],
            split_nodes_image(after_links),
        )

    # The input list is not modified; a new list is returned.
    def test_does_not_mutate_input(self):
        nodes = [TextNode("a ![x](/x.png) b", TextType.TEXT)]
        split_nodes_image(nodes)
        self.assertListEqual([TextNode("a ![x](/x.png) b", TextType.TEXT)], nodes)



class TestTextToTextNodes(unittest.TestCase):
    # The example from the lesson: every inline type in one string.
    def test_text_to_textnodes(self):
        text = "This is **text** with an _italic_ word and a `code block` and an ![obi wan image](https://i.imgur.com/fJRm4Vk.jpeg) and a [link](https://boot.dev)"
        self.assertListEqual(
            [
                TextNode("This is ", TextType.TEXT),
                TextNode("text", TextType.BOLD),
                TextNode(" with an ", TextType.TEXT),
                TextNode("italic", TextType.ITALIC),
                TextNode(" word and a ", TextType.TEXT),
                TextNode("code block", TextType.CODE),
                TextNode(" and an ", TextType.TEXT),
                TextNode("obi wan image", TextType.IMAGE, "https://i.imgur.com/fJRm4Vk.jpeg"),
                TextNode(" and a ", TextType.TEXT),
                TextNode("link", TextType.LINK, "https://boot.dev"),
            ],
            text_to_textnodes(text),
        )

    # No markdown at all: one plain text node.
    def test_plain_text(self):
        self.assertListEqual(
            [TextNode("Just plain text", TextType.TEXT)],
            text_to_textnodes("Just plain text"),
        )

    # Each type on its own, to show no pass depends on the others.
    def test_bold_only(self):
        self.assertListEqual(
            [TextNode("bold", TextType.BOLD)],
            text_to_textnodes("**bold**"),
        )

    def test_italic_only(self):
        self.assertListEqual(
            [TextNode("italic", TextType.ITALIC)],
            text_to_textnodes("_italic_"),
        )

    def test_code_only(self):
        self.assertListEqual(
            [TextNode("code", TextType.CODE)],
            text_to_textnodes("`code`"),
        )

    def test_image_only(self):
        self.assertListEqual(
            [TextNode("cat", TextType.IMAGE, "/cat.png")],
            text_to_textnodes("![cat](/cat.png)"),
        )

    def test_link_only(self):
        self.assertListEqual(
            [TextNode("about", TextType.LINK, "/about")],
            text_to_textnodes("[about](/about)"),
        )

    # An empty string yields no nodes at all.
    def test_empty_string(self):
        self.assertListEqual([], text_to_textnodes(""))

    # Several of the same type in one string.
    def test_multiple_bold(self):
        self.assertListEqual(
            [
                TextNode("one", TextType.BOLD),
                TextNode(" and ", TextType.TEXT),
                TextNode("two", TextType.BOLD),
            ],
            text_to_textnodes("**one** and **two**"),
        )

    # An image and a link side by side: the image pass must not eat the
    # link, and the link pass must not claim the image.
    def test_image_and_link_adjacent(self):
        self.assertListEqual(
            [
                TextNode("pic", TextType.IMAGE, "/a.png"),
                TextNode("here", TextType.LINK, "/b"),
            ],
            text_to_textnodes("![pic](/a.png)[here](/b)"),
        )

    # Markdown right at the start, with no leading plain text.
    def test_starts_with_markdown(self):
        self.assertListEqual(
            [
                TextNode("bold", TextType.BOLD),
                TextNode(" then text", TextType.TEXT),
            ],
            text_to_textnodes("**bold** then text"),
        )

    # The types can appear in any order in the source string.
    def test_types_in_different_order(self):
        self.assertListEqual(
            [
                TextNode("a", TextType.LINK, "/a"),
                TextNode(" ", TextType.TEXT),
                TextNode("c", TextType.CODE),
                TextNode(" ", TextType.TEXT),
                TextNode("i", TextType.ITALIC),
                TextNode(" ", TextType.TEXT),
                TextNode("b", TextType.BOLD),
            ],
            text_to_textnodes("[a](/a) `c` _i_ **b**"),
        )

    # Bold and italic next to each other, which is where a naive pass
    # order would confuse "**" with two "_" delimiters.
    def test_bold_and_italic_together(self):
        self.assertListEqual(
            [
                TextNode("bold", TextType.BOLD),
                TextNode(" and ", TextType.TEXT),
                TextNode("italic", TextType.ITALIC),
            ],
            text_to_textnodes("**bold** and _italic_"),
        )

    # Links are parsed before the delimiters, so markup inside an anchor
    # does not break the link. Running "**" first would destroy it.
    def test_link_anchor_containing_bold_markup(self):
        self.assertListEqual(
            [TextNode("**bold** link", TextType.LINK, "/x")],
            text_to_textnodes("[**bold** link](/x)"),
        )

    # Invalid markdown still raises, through the delimiter splitter.
    def test_unmatched_delimiter_raises(self):
        with self.assertRaises(ValueError):
            text_to_textnodes("This is **unfinished")


if __name__ == "__main__":
    unittest.main()
