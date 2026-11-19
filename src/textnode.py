from enum import Enum

from htmlnode import LeafNode


# The inline text types we need to represent. The string values are what
# get printed by __repr__ below, through .value.
class TextType(Enum):
    TEXT = "text"
    BOLD = "bold"
    ITALIC = "italic"
    CODE = "code"
    LINK = "link"
    IMAGE = "image"


class TextNode:
    def __init__(self, text, text_type, url=None):
        self.text = text
        self.text_type = text_type
        # Only links and images have a URL, so it defaults to None for the
        # other types.
        self.url = url

    # __eq__ is what makes "==" work on two TextNodes, which the unit tests
    # rely on. Without it Python compares object identity, so two separate
    # nodes holding the same values would not be equal.
    def __eq__(self, other):
        # The isinstance check keeps a comparison against some other type
        # from raising AttributeError; it just returns False instead.
        return (
            isinstance(other, TextNode)
            and self.text == other.text
            and self.text_type == other.text_type
            and self.url == other.url
        )

    # __repr__ is the string print() shows for the object.
    def __repr__(self):
        return f"TextNode({self.text}, {self.text_type.value}, {self.url})"


# Bridges the two representations: a TextNode describes inline text, and
# this turns it into the LeafNode that knows how to render itself as HTML.
def text_node_to_html_node(text_node: TextNode) -> LeafNode:
    if text_node.text_type == TextType.TEXT:
        # No tag, so it renders as raw text with no markup around it.
        return LeafNode(None, text_node.text)
    if text_node.text_type == TextType.BOLD:
        return LeafNode("b", text_node.text)
    if text_node.text_type == TextType.ITALIC:
        return LeafNode("i", text_node.text)
    if text_node.text_type == TextType.CODE:
        return LeafNode("code", text_node.text)
    if text_node.text_type == TextType.LINK:
        # The text becomes the anchor text, and the url becomes href.
        return LeafNode("a", text_node.text, {"href": text_node.url})
    if text_node.text_type == TextType.IMAGE:
        # An image shows no text of its own, so the value is empty: the
        # text is the alt description and the url is the image source.
        return LeafNode("img", "", {"src": text_node.url, "alt": text_node.text})

    # Anything else isn't a text type we know how to render.
    raise ValueError(f"invalid text type: {text_node.text_type}")
