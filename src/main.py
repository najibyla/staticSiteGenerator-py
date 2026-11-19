import sys

from copystatic import copy_static
from generate import generate_pages_recursive


def main():
    # The site can be served from the root of a domain or from a
    # subdirectory (GitHub Pages serves it at /REPO_NAME/). The first CLI
    # argument says which; local testing uses the default "/".
    basepath = "/"
    if len(sys.argv) > 1:
        basepath = sys.argv[1]

    # Rebuild docs/ from the contents of static/, then write a page on
    # top of it for every markdown file under content/. The output goes
    # to docs/ because that is the directory GitHub Pages deploys from.
    copy_static("static", "docs")
    generate_pages_recursive("content", "template.html", "docs", basepath)


main()
