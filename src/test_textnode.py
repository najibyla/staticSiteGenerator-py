import unittest
from textnode import TextNode, TextType, text_node_to_html_node


class TestTextNode(unittest.TestCase):
    # Two nodes built with the same values should be equal, even though
    # they are separate objects. This is what __eq__ gives us.
    def test_eq(self):
        node = TextNode("This is a text node", TextType.BOLD)
        node2 = TextNode("This is a text node", TextType.BOLD)
        self.assertEqual(node, node2)

    # Equality also has to take the url into account, not just text and
    # text_type.
    def test_eq_with_url(self):
        node = TextNode("Boot.dev", TextType.LINK, "https://www.boot.dev")
        node2 = TextNode("Boot.dev", TextType.LINK, "https://www.boot.dev")
        self.assertEqual(node, node2)

    # Leaving the url out should give None, so a node created without one
    # matches a node explicitly passed None.
    def test_url_defaults_to_none(self):
        node = TextNode("No link here", TextType.TEXT)
        self.assertIsNone(node.url)
        self.assertEqual(node, TextNode("No link here", TextType.TEXT, None))

    # Different text means different nodes.
    def test_not_eq_different_text(self):
        node = TextNode("This is a text node", TextType.ITALIC)
        node2 = TextNode("This is another text node", TextType.ITALIC)
        self.assertNotEqual(node, node2)

    # Same text, but a different type, is still a different node.
    def test_not_eq_different_text_type(self):
        node = TextNode("Same words", TextType.BOLD)
        node2 = TextNode("Same words", TextType.ITALIC)
        self.assertNotEqual(node, node2)

    # A missing url must not match a real one: this is the edge case where
    # only the url differs.
    def test_not_eq_url_none_vs_set(self):
        node = TextNode("Click me", TextType.LINK)
        node2 = TextNode("Click me", TextType.LINK, "https://www.boot.dev")
        self.assertNotEqual(node, node2)

    # Two different urls, everything else the same.
    def test_not_eq_different_url(self):
        node = TextNode("Click me", TextType.LINK, "https://www.boot.dev")
        node2 = TextNode("Click me", TextType.LINK, "https://www.example.com")
        self.assertNotEqual(node, node2)

    # Comparing against something that isn't a TextNode should just be
    # False, not an error.
    def test_not_eq_other_type(self):
        node = TextNode("This is a text node", TextType.TEXT)
        self.assertNotEqual(node, "This is a text node")

    # __repr__ prints the text type's string value (e.g. "image"), not the
    # enum member name.
    def test_repr(self):
        node = TextNode("alt text", TextType.IMAGE, "/img.png")
        self.assertEqual(repr(node), "TextNode(alt text, image, /img.png)")

    # A node with no url shows None in its repr.
    def test_repr_without_url(self):
        node = TextNode("plain", TextType.TEXT)
        self.assertEqual(repr(node), "TextNode(plain, text, None)")


class TestTextNodeToHTMLNode(unittest.TestCase):
    # Plain text gets no tag at all, so it renders as raw text.
    def test_text(self):
        node = TextNode("This is a text node", TextType.TEXT)
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, None)
        self.assertEqual(html_node.value, "This is a text node")

    def test_bold(self):
        node = TextNode("This is bold", TextType.BOLD)
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "b")
        self.assertEqual(html_node.value, "This is bold")
        self.assertEqual(html_node.to_html(), "<b>This is bold</b>")

    def test_italic(self):
        node = TextNode("This is italic", TextType.ITALIC)
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "i")
        self.assertEqual(html_node.to_html(), "<i>This is italic</i>")

    def test_code(self):
        node = TextNode("print('hi')", TextType.CODE)
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "code")
        self.assertEqual(html_node.to_html(), "<code>print('hi')</code>")

    # A link keeps its text as the anchor text and its url as href.
    def test_link(self):
        node = TextNode("Boot.dev", TextType.LINK, "https://www.boot.dev")
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "a")
        self.assertEqual(html_node.value, "Boot.dev")
        self.assertEqual(html_node.props, {"href": "https://www.boot.dev"})
        self.assertEqual(
            html_node.to_html(),
            '<a href="https://www.boot.dev">Boot.dev</a>',
        )

    # An image carries no text of its own: the text becomes alt, and the
    # url becomes src.
    def test_image(self):
        node = TextNode("a cute cat", TextType.IMAGE, "/images/cat.png")
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "img")
        self.assertEqual(html_node.value, "")
        self.assertEqual(
            html_node.props,
            {"src": "/images/cat.png", "alt": "a cute cat"},
        )

    # None of the text types carry children: they are all leaves.
    def test_all_types_have_no_children(self):
        for text_type in TextType:
            node = TextNode("some text", text_type, "https://www.boot.dev")
            self.assertIsNone(text_node_to_html_node(node).children)

    # Anything that isn't a TextType can't be rendered.
    def test_invalid_text_type_raises(self):
        node = TextNode("This is a text node", "not_a_real_type")
        with self.assertRaises(ValueError):
            text_node_to_html_node(node)


if __name__ == "__main__":
    unittest.main()
