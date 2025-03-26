"""
Utility functions for finding and potentially managing image files.
"""

from pathlib import Path
from typing import Set, Any

from config import IMAGE_EXTENSIONS

def get_image_names(images_dir: Path) -> set[Any] | tuple[set[str], set[str]]:
    """
    Recursively finds all image files in the specified directory and returns
    a set of their base names (filename + extension).

    Args:
        images_dir: The Path object representing the root images directory.

    Returns:
        A set containing the unique names (e.g., 'image1.png', 'photo.jpg')
        of all image files found. Duplicate filenames found in different
        subdirectories will only appear once in the set.
    """
    image_paths: Set[str] = set()
    image_names: Set[str] = set()

    print(f"Scanning for images in: {images_dir.resolve()}") # Using resolve() for a clear absolute path in the message

    if not images_dir.is_dir():
        print(f"Warning: Images directory does not exist: {images_dir}")
        return set() # Return an empty set

    for filepath in images_dir.rglob("*"):
        if filepath.is_file() and filepath.suffix.lower() in IMAGE_EXTENSIONS:
            image_paths.add(filepath.absolute().as_posix())
            image_names.add(filepath.stem)

    print(f"Found {len(image_paths)} unique image filenames.")
    return image_paths, image_names


def perform_safe_deletion(files_to_delete: Set[Path], base_images_dir: Path) -> tuple[int, int]:
    """
    Safely deletes the specified files, ensuring they are within the base_images_dir.

    Args:
        files_to_delete: A set of Path objects for files marked for deletion.
        base_images_dir: The root directory where images were scanned. Files outside
                         this directory (considering subdirectories) will not be deleted.

    Returns:
        A tuple containing (number_of_files_deleted, number_of_errors_or_skips).
    """
    deleted_count = 0
    error_count = 0
    base_images_dir_abs = base_images_dir.resolve()
    print("\n--- Starting Deletion ---")

    files_to_process = sorted(list(files_to_delete)) # Process in a consistent order

    for file_path in files_to_process:
        try:
            file_path_abs = file_path.resolve()
            # Crucial Safety Check: Ensure the file is truly within the base images directory
            if base_images_dir_abs not in file_path_abs.parents:
                 # Also handle case where file is directly IN base_images_dir_abs
                 if file_path_abs.parent != base_images_dir_abs:
                    print(f"Safety Skip: {file_path.name} resolved to {file_path_abs}, which is outside the intended base images directory {base_images_dir_abs}")
                    error_count += 1
                    continue

            if file_path_abs.exists():
                file_path_abs.unlink()
                try:
                    # Show relative path for clarity if possible
                    relative_path = file_path_abs.relative_to(base_images_dir_abs)
                    print(f"Deleted: {relative_path}")
                except ValueError:
                    print(f"Deleted: {file_path_abs}") # Fallback if relative path fails
                deleted_count += 1
            else:
                try:
                    relative_path = file_path_abs.relative_to(base_images_dir_abs)
                    print(f"Skipped (already deleted?): {relative_path}")
                except ValueError:
                    print(f"Skipped (already deleted?): {file_path_abs}")

        except Exception as e:
            try:
                relative_path = file_path.relative_to(base_images_dir)
                print(f"Error deleting {relative_path}: {e}")
            except ValueError:
                 print(f"Error deleting {file_path}: {e}")
            error_count += 1

    print(f"--- Deletion Summary: {deleted_count} deleted, {error_count} errors/skipped. ---")
    return deleted_count, error_count