import os
from pathlib import Path

from block_markdown import markdown_to_html_node, extract_title


def generate_page(
    from_path: str, template_path: str, dest_path: str, basepath: str = "/"
) -> None:
    # Turn one markdown file into a finished HTML page by dropping its
    # title and rendered content into the template.
    print(f"Generating page from {from_path} to {dest_path} using {template_path}")

    with open(from_path) as f:
        markdown = f.read()

    with open(template_path) as f:
        template = f.read()

    # The whole document becomes one <div> of HTML, and the "#" heading
    # supplies the page title.
    content = markdown_to_html_node(markdown).to_html()
    title = extract_title(markdown)

    page = template.replace("{{ Title }}", title).replace("{{ Content }}", content)

    # Every link and image in the markdown is written as a root-relative
    # path like "/blog/tom". On GitHub Pages the site lives under
    # /REPO_NAME/ instead of at the domain root, so those paths need the
    # base path in front of them or they all 404.
    page = page.replace('href="/', f'href="{basepath}')
    page = page.replace('src="/', f'src="{basepath}')

    # The destination may be nested (public/blog/index.html), and those
    # directories may not exist yet. exist_ok keeps a rerun from failing.
    dest_dir = os.path.dirname(dest_path)
    if dest_dir != "":
        os.makedirs(dest_dir, exist_ok=True)

    with open(dest_path, "w") as f:
        f.write(page)


def generate_pages_recursive(
    dir_path_content: str,
    template_path: str,
    dest_dir_path: str,
    basepath: str = "/",
) -> None:
    # Walk the whole content tree and turn every markdown file into an
    # HTML page, mirroring the directory structure into dest_dir_path.
    for entry in os.listdir(dir_path_content):
        source_path = os.path.join(dir_path_content, entry)
        dest_path = os.path.join(dest_dir_path, entry)

        if os.path.isfile(source_path):
            # Only markdown becomes a page; anything else in content/ is
            # left alone.
            if source_path.endswith(".md"):
                # index.md becomes index.html, in the matching folder, so
                # content/blog/tom/index.md serves at /blog/tom.
                html_path = str(Path(dest_path).with_suffix(".html"))
                generate_page(source_path, template_path, html_path, basepath)
        else:
            # A subdirectory: same job one level down. generate_page
            # creates the destination folders as it writes each file, so
            # there is nothing to make here.
            generate_pages_recursive(
                source_path, template_path, dest_path, basepath
            )
