class HTMLNode:
    # Every member is optional, so a node can be built in whichever shape
    # it needs: raw text (no tag), a leaf with a value, or a parent with
    # children.
    def __init__(self, tag=None, value=None, children=None, props=None):
        # The HTML tag name, e.g. "p" or "a". None means render as raw
        # text with no surrounding tag.
        self.tag = tag
        # The text inside the tag. A node with no value is assumed to have
        # children instead.
        self.value = value
        # A list of child HTMLNode objects. A node with no children is
        # assumed to have a value instead.
        self.children = children
        # A dict of HTML attributes, e.g. {"href": "https://boot.dev"}.
        # None means the tag has no attributes.
        self.props = props

    # Child classes (leaf and parent nodes, in the next lessons) override
    # this to render themselves. The base class has no sensible way to do
    # it, so it refuses rather than returning something wrong.
    def to_html(self):
        raise NotImplementedError

    def props_to_html(self):
        # No attributes at all: return "" so nothing is added to the tag.
        # This covers both None and an empty dict.
        if not self.props:
            return ""

        # Each attribute needs a leading space, because it sits directly
        # after the tag name or the previous attribute:
        #   <a href="..." target="_blank">
        result = ""
        for key, value in self.props.items():
            result += f' {key}="{value}"'
        return result

    # Shows all four members, which makes debugging the node tree easier.
    def __repr__(self):
        return f"HTMLNode({self.tag}, {self.value}, {self.children}, {self.props})"


# A leaf is a node with no children: a single tag wrapping a value, like
# <p>some text</p>. It inherits props_to_html from HTMLNode.
class LeafNode(HTMLNode):
    def __init__(self, tag, value, props=None):
        # tag and value are required here (unlike in HTMLNode), and
        # children is always None, since a leaf has none by definition.
        super().__init__(tag, value, None, props)

    def to_html(self):
        # A leaf with nothing to render is a mistake, so refuse instead of
        # producing an empty tag. (An empty string is still a value: only
        # None counts as missing.)
        if self.value is None:
            raise ValueError("all leaf nodes must have a value")

        # No tag means the value is raw text, with nothing wrapped around
        # it.
        if self.tag is None:
            return self.value

        # props_to_html() already supplies its own leading space, so it
        # goes straight after the tag name.
        return f"<{self.tag}{self.props_to_html()}>{self.value}</{self.tag}>"

    # Same idea as HTMLNode's, minus children, which a leaf never has.
    def __repr__(self):
        return f"LeafNode({self.tag}, {self.value}, {self.props})"


# A parent is a node that holds other nodes instead of a value, like a
# <div> wrapping several <span>s. The exact opposite of LeafNode.
class ParentNode(HTMLNode):
    def __init__(self, tag, children, props=None):
        # tag and children are required here, and there is no value: the
        # content comes from the children.
        super().__init__(tag, None, children, props)

    def to_html(self):
        # Without a tag there is nothing to wrap the children in.
        if self.tag is None:
            raise ValueError("all parent nodes must have a tag")

        # Missing children means there is no content to render. (An empty
        # list is different: that's a parent that legitimately holds
        # nothing, and renders as an empty tag.)
        if self.children is None:
            raise ValueError("all parent nodes must have children")

        # This is the recursive part: each child renders itself with its
        # own to_html(). A child that is a leaf returns its tag and text;
        # a child that is another parent recurses again, however deep the
        # tree goes.
        inner_html = ""
        for child in self.children:
            inner_html += child.to_html()

        return f"<{self.tag}{self.props_to_html()}>{inner_html}</{self.tag}>"

    # Same idea as HTMLNode's, minus value, which a parent never has.
    def __repr__(self):
        return f"ParentNode({self.tag}, {self.children}, {self.props})"
