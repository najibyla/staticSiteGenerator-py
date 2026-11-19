import os
import shutil


def copy_files_recursive(source_dir: str, dest_dir: str) -> None:
    # Copy everything from source_dir into dest_dir, walking into
    # subdirectories as it goes. The destination is assumed to be empty
    # or absent; copy_static below clears it first.

    # Each level of recursion needs its own directory on the far side
    # before anything can be copied into it.
    if not os.path.exists(dest_dir):
        os.mkdir(dest_dir)

    for entry in os.listdir(source_dir):
        source_path = os.path.join(source_dir, entry)
        dest_path = os.path.join(dest_dir, entry)

        if os.path.isfile(source_path):
            # Logging each file makes it obvious what the copy did, and
            # which file it was on if something goes wrong.
            print(f" * {source_path} -> {dest_path}")
            shutil.copy(source_path, dest_path)
        else:
            # A subdirectory: same job one level down, which is where the
            # recursion comes in.
            copy_files_recursive(source_path, dest_path)


def copy_static(source_dir: str = "static", dest_dir: str = "public") -> None:
    # Rebuild dest_dir from scratch out of source_dir.

    # Deleting first means files removed from static also disappear from
    # public, instead of lingering from an earlier build.
    if os.path.exists(dest_dir):
        print(f"Deleting {dest_dir} directory...")
        shutil.rmtree(dest_dir)

    print(f"Copying static files from {source_dir} to {dest_dir}...")
    copy_files_recursive(source_dir, dest_dir)
