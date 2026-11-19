import unittest
from htmlnode import HTMLNode, LeafNode, ParentNode


class TestHTMLNode(unittest.TestCase):
    # Every member should default to None, so an empty node is valid.
    def test_defaults_to_none(self):
        node = HTMLNode()
        self.assertIsNone(node.tag)
        self.assertIsNone(node.value)
        self.assertIsNone(node.children)
        self.assertIsNone(node.props)

    # The documented example: two attributes, each with a leading space.
    def test_props_to_html_multiple(self):
        node = HTMLNode(
            "a",
            "Boot.dev",
            None,
            {"href": "https://www.google.com", "target": "_blank"},
        )
        self.assertEqual(
            node.props_to_html(),
            ' href="https://www.google.com" target="_blank"',
        )

    # A single attribute still gets the leading space.
    def test_props_to_html_single(self):
        node = HTMLNode("a", "Boot.dev", None, {"href": "https://www.boot.dev"})
        self.assertEqual(node.props_to_html(), ' href="https://www.boot.dev"')

    # No props given: nothing to add to the tag.
    def test_props_to_html_none(self):
        node = HTMLNode("p", "Just a paragraph")
        self.assertEqual(node.props_to_html(), "")

    # An empty dict must behave the same as None.
    def test_props_to_html_empty_dict(self):
        node = HTMLNode("p", "Just a paragraph", None, {})
        self.assertEqual(node.props_to_html(), "")

    # The base class can't render itself; child classes will.
    def test_to_html_raises(self):
        node = HTMLNode("p", "Just a paragraph")
        with self.assertRaises(NotImplementedError):
            node.to_html()

    # A node holding children rather than a value.
    def test_children_are_stored(self):
        child = HTMLNode("span", "child text")
        parent = HTMLNode("div", None, [child])
        self.assertEqual(parent.children, [child])
        self.assertIsNone(parent.value)

    # repr shows all four members, for debugging.
    def test_repr(self):
        node = HTMLNode("p", "Hello", None, {"class": "greeting"})
        self.assertEqual(
            repr(node),
            "HTMLNode(p, Hello, None, {'class': 'greeting'})",
        )


class TestLeafNode(unittest.TestCase):
    # The simplest case: a tag wrapped around some text.
    def test_leaf_to_html_p(self):
        node = LeafNode("p", "Hello, world!")
        self.assertEqual(node.to_html(), "<p>Hello, world!</p>")

    # A different tag, to show nothing is hard-coded to "p".
    def test_leaf_to_html_b(self):
        node = LeafNode("b", "This is bold text.")
        self.assertEqual(node.to_html(), "<b>This is bold text.</b>")

    def test_leaf_to_html_span(self):
        node = LeafNode("span", "inline text")
        self.assertEqual(node.to_html(), "<span>inline text</span>")

    def test_leaf_to_html_h1(self):
        node = LeafNode("h1", "A Heading")
        self.assertEqual(node.to_html(), "<h1>A Heading</h1>")

    # With props, the attributes land inside the opening tag.
    def test_leaf_to_html_a_with_props(self):
        node = LeafNode("a", "Click me!", {"href": "https://www.google.com"})
        self.assertEqual(
            node.to_html(),
            '<a href="https://www.google.com">Click me!</a>',
        )

    # More than one attribute, in the order given.
    def test_leaf_to_html_multiple_props(self):
        node = LeafNode("a", "Boot.dev", {"href": "https://www.boot.dev", "target": "_blank"})
        self.assertEqual(
            node.to_html(),
            '<a href="https://www.boot.dev" target="_blank">Boot.dev</a>',
        )

    # No tag: the value comes back as raw text, with no markup.
    def test_leaf_to_html_no_tag(self):
        node = LeafNode(None, "Just raw text")
        self.assertEqual(node.to_html(), "Just raw text")

    # A missing value is an error, since there is nothing to render.
    def test_leaf_to_html_no_value_raises(self):
        node = LeafNode("p", None)
        with self.assertRaises(ValueError):
            node.to_html()

    # An empty string is a value, so it renders an empty tag rather than
    # raising.
    def test_leaf_to_html_empty_value(self):
        node = LeafNode("p", "")
        self.assertEqual(node.to_html(), "<p></p>")

    # A leaf never has children, whatever else is passed.
    def test_leaf_has_no_children(self):
        node = LeafNode("p", "Hello")
        self.assertIsNone(node.children)

    # repr leaves children out, unlike HTMLNode's.
    def test_leaf_repr(self):
        node = LeafNode("a", "Click me!", {"href": "https://www.boot.dev"})
        self.assertEqual(
            repr(node),
            "LeafNode(a, Click me!, {'href': 'https://www.boot.dev'})",
        )


class TestParentNode(unittest.TestCase):
    # One child, rendered inside the parent's tag.
    def test_to_html_with_children(self):
        child_node = LeafNode("span", "child")
        parent_node = ParentNode("div", [child_node])
        self.assertEqual(parent_node.to_html(), "<div><span>child</span></div>")

    # A parent inside a parent: this is the recursion working.
    def test_to_html_with_grandchildren(self):
        grandchild_node = LeafNode("b", "grandchild")
        child_node = ParentNode("span", [grandchild_node])
        parent_node = ParentNode("div", [child_node])
        self.assertEqual(
            parent_node.to_html(),
            "<div><span><b>grandchild</b></span></div>",
        )

    # Four levels deep, to show the depth isn't limited.
    def test_to_html_deeply_nested(self):
        node = ParentNode(
            "div",
            [ParentNode("section", [ParentNode("p", [LeafNode("b", "deep")])])],
        )
        self.assertEqual(
            node.to_html(),
            "<div><section><p><b>deep</b></p></section></div>",
        )

    # Several children in a row, each rendered in order.
    def test_to_html_multiple_children(self):
        node = ParentNode(
            "ul",
            [
                LeafNode("li", "one"),
                LeafNode("li", "two"),
                LeafNode("li", "three"),
            ],
        )
        self.assertEqual(
            node.to_html(),
            "<ul><li>one</li><li>two</li><li>three</li></ul>",
        )

    # The example from the lesson: tagged and raw-text leaves mixed.
    def test_to_html_mixed_leaf_types(self):
        node = ParentNode(
            "p",
            [
                LeafNode("b", "Bold text"),
                LeafNode(None, "Normal text"),
                LeafNode("i", "italic text"),
                LeafNode(None, "Normal text"),
            ],
        )
        self.assertEqual(
            node.to_html(),
            "<p><b>Bold text</b>Normal text<i>italic text</i>Normal text</p>",
        )

    # A mix of leaf and parent children side by side.
    def test_to_html_leaf_and_parent_siblings(self):
        node = ParentNode(
            "div",
            [
                LeafNode("h1", "Title"),
                ParentNode("p", [LeafNode(None, "Some "), LeafNode("b", "bold")]),
            ],
        )
        self.assertEqual(
            node.to_html(),
            "<div><h1>Title</h1><p>Some <b>bold</b></p></div>",
        )

    # The parent's own attributes go in its opening tag.
    def test_to_html_with_props(self):
        node = ParentNode(
            "div",
            [LeafNode("span", "child")],
            {"class": "wrapper", "id": "main"},
        )
        self.assertEqual(
            node.to_html(),
            '<div class="wrapper" id="main"><span>child</span></div>',
        )

    # Both the parent and its child can carry attributes.
    def test_to_html_nested_props(self):
        node = ParentNode(
            "div",
            [LeafNode("a", "Boot.dev", {"href": "https://www.boot.dev"})],
            {"class": "links"},
        )
        self.assertEqual(
            node.to_html(),
            '<div class="links"><a href="https://www.boot.dev">Boot.dev</a></div>',
        )

    # No tag: nothing to wrap the children in.
    def test_to_html_no_tag_raises(self):
        node = ParentNode(None, [LeafNode("span", "child")])
        with self.assertRaises(ValueError):
            node.to_html()

    # Missing children: no content to render.
    def test_to_html_no_children_raises(self):
        node = ParentNode("div", None)
        with self.assertRaises(ValueError):
            node.to_html()

    # The two failures above must give different messages.
    def test_to_html_error_messages_differ(self):
        with self.assertRaises(ValueError) as no_tag:
            ParentNode(None, [LeafNode("span", "child")]).to_html()
        with self.assertRaises(ValueError) as no_children:
            ParentNode("div", None).to_html()
        self.assertNotEqual(str(no_tag.exception), str(no_children.exception))

    # An empty list is not the same as missing: it renders an empty tag.
    def test_to_html_empty_children_list(self):
        node = ParentNode("div", [])
        self.assertEqual(node.to_html(), "<div></div>")

    # A parent holds no value of its own.
    def test_parent_has_no_value(self):
        node = ParentNode("div", [LeafNode("span", "child")])
        self.assertIsNone(node.value)

    # repr leaves value out, unlike HTMLNode's.
    def test_parent_repr(self):
        child = LeafNode("span", "child")
        node = ParentNode("div", [child], {"class": "wrapper"})
        self.assertEqual(
            repr(node),
            f"ParentNode(div, [{repr(child)}], {{'class': 'wrapper'}})",
        )


if __name__ == "__main__":
    unittest.main()
