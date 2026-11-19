import re

from textnode import TextNode, TextType


def split_nodes_delimiter(
    old_nodes: list[TextNode], delimiter: str, text_type: TextType
) -> list[TextNode]:
    # Split every plain-text node on one delimiter (e.g. "`" or "**"),
    # turning the delimited pieces into text_type nodes and leaving the
    # rest as plain text. Call it once per delimiter: each pass only
    # touches TEXT nodes, so nodes created by earlier passes survive
    # untouched.
    new_nodes = []

    for old_node in old_nodes:
        # Already-parsed nodes (bold, code, links...) are kept as they
        # are. Only plain text can still contain unparsed markdown.
        if old_node.text_type != TextType.TEXT:
            new_nodes.append(old_node)
            continue

        # Splitting on the delimiter alternates between outside and inside
        # it: "a `b` c" -> ["a ", "b", " c"], where the odd indexes are
        # the delimited parts.
        parts = old_node.text.split(delimiter)

        # Every opening delimiter needs a closing one, which always gives
        # an odd number of parts. An even count means one is unmatched.
        if len(parts) % 2 == 0:
            raise ValueError(
                f"invalid markdown: no closing {delimiter} in {old_node.text!r}"
            )

        for i, part in enumerate(parts):
            # A delimiter at the very start or end produces an empty part,
            # which would otherwise become a pointless empty node.
            if part == "":
                continue
            if i % 2 == 0:
                new_nodes.append(TextNode(part, TextType.TEXT))
            else:
                new_nodes.append(TextNode(part, text_type))

    return new_nodes


# Markdown image syntax: ![alt text](url)
#   !\[            a literal "!" then "[", which is what marks an image
#   ([^\[\]]*)     group 1, the alt text: anything except more brackets
#   \]\(           the "](" between the alt text and the url
#   ([^\(\)]*)     group 2, the url: anything except more parentheses
#   \)             the closing parenthesis
IMAGE_PATTERN = r"!\[([^\[\]]*)\]\(([^\(\)]*)\)"

# Markdown link syntax: [anchor text](url). Same as above but without the
# "!", and with (?<!!) in front: a "negative lookbehind" saying the "[" must
# not be preceded by "!". Without it, every image would also match as a
# link, since an image is just a link with a "!" stuck on the front.
LINK_PATTERN = r"(?<!!)\[([^\[\]]*)\]\(([^\(\)]*)\)"


def extract_markdown_images(text: str) -> list[tuple[str, str]]:
    # findall with two groups in the pattern returns a list of
    # (group 1, group 2) tuples, which is exactly (alt text, url).
    return re.findall(IMAGE_PATTERN, text)


def extract_markdown_links(text: str) -> list[tuple[str, str]]:
    # Same shape, but each tuple is (anchor text, url).
    return re.findall(LINK_PATTERN, text)


def _split_nodes_on_markdown(old_nodes, extract, text_type, prefix):
    # Shared by split_nodes_image and split_nodes_link, which differ only
    # in which extractor they use, which TextType they produce, and
    # whether the markdown starts with "!".
    new_nodes = []

    for old_node in old_nodes:
        # Only plain text can still contain unparsed markdown; nodes from
        # earlier passes are kept exactly as they are.
        if old_node.text_type != TextType.TEXT:
            new_nodes.append(old_node)
            continue

        # Whatever is still unprocessed. Each match below chops off the
        # part up to and including that image or link.
        remaining = old_node.text

        for label, url in extract(remaining):
            # Rebuild the exact markdown this match came from, so we can
            # find it in the text: "![alt](url)" or "[anchor](url)".
            markdown = f"{prefix}[{label}]({url})"

            # maxsplit=1 splits at the first occurrence only, giving the
            # text before this match and everything after it. The part
            # after becomes the new remaining text for the next match.
            before, remaining = remaining.split(markdown, 1)

            # Markdown at the very start (or two in a row) leaves an empty
            # "before", which would otherwise become a pointless node.
            if before != "":
                new_nodes.append(TextNode(before, TextType.TEXT))

            new_nodes.append(TextNode(label, text_type, url))

        # Whatever text is left after the last match. When there were no
        # matches at all, this is the whole original text, so the node
        # comes back unchanged.
        if remaining != "":
            new_nodes.append(TextNode(remaining, TextType.TEXT))

    return new_nodes


def split_nodes_image(old_nodes: list[TextNode]) -> list[TextNode]:
    # Split every plain-text node on its markdown images, turning each one
    # into an IMAGE node holding the alt text and the url.
    return _split_nodes_on_markdown(
        old_nodes, extract_markdown_images, TextType.IMAGE, "!"
    )


def split_nodes_link(old_nodes: list[TextNode]) -> list[TextNode]:
    # Same, for markdown links. No "!" prefix, which is the only thing
    # that distinguishes link markdown from image markdown.
    return _split_nodes_on_markdown(
        old_nodes, extract_markdown_links, TextType.LINK, ""
    )


def text_to_textnodes(text: str) -> list[TextNode]:
    # Parse a raw markdown string into its inline nodes by running every
    # splitter in turn. Each pass only touches TEXT nodes, so whatever an
    # earlier pass produced is carried through untouched.
    nodes = [TextNode(text, TextType.TEXT)]

    # Images and links must come first. Their markdown can contain
    # characters the delimiter passes would chop up: "[**bold** link](/x)"
    # loses its link syntax entirely if "**" is split out before the link
    # is recognised. (Image before link or the other way round makes no
    # difference, since the link pattern already refuses to match images.)
    nodes = split_nodes_image(nodes)
    nodes = split_nodes_link(nodes)

    # These three use different delimiters and never see each other's
    # markup, so their order among themselves does not matter.
    nodes = split_nodes_delimiter(nodes, "**", TextType.BOLD)
    nodes = split_nodes_delimiter(nodes, "_", TextType.ITALIC)
    nodes = split_nodes_delimiter(nodes, "`", TextType.CODE)

    return nodes
