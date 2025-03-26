import sys
import tkinter as tk
import sv_ttk
from pathlib import Path
from typing import Optional, Tuple

from config import SCRIPT_DIR_NAMES
from file_utils import get_image_names
from gui_viewer import UnusedImageViewer
from script_parser import extract_image_references


def find_project_paths(base_dir: Path) -> Tuple[Optional[Path], Optional[Path]]:
    """
    Attempts to automatically find the script and images directories
    based on standard Ren'Py project structure.

    Args:
        base_dir: The root directory of the Ren'Py project.

    Returns:
        A tuple containing (script_dir_path, images_dir_path), or (None, None)
        if the standard structure isn't found.
    """
    script_dir = None

    game_dir = base_dir / 'game'
    if not game_dir.is_dir():
        print(f"Error: Standard 'game' directory not found in '{base_dir}'.")
        print("Please provide the path to the base project directory containing 'game'.")
        return None, None

    # Find script directory (game/scripts or just game)
    for name in SCRIPT_DIR_NAMES:
         potential_script_dir = game_dir / name
         if potential_script_dir.is_dir() and any(potential_script_dir.rglob('*.rpy')):
              script_dir = potential_script_dir
              print(f"Found script directory: {script_dir}")
              break # Prefer game/script if it exists and has files

    if not script_dir:
         # Fallback to game dir itself if it has .rpy files directly
         if any(game_dir.rglob('*.rpy')):
              script_dir = game_dir
              print(f"Found script files directly in: {script_dir}")
         else:
              print(f"Error: Could not find a suitable script directory with .rpy files "
                    f"(checked {SCRIPT_DIR_NAMES} within 'game' and 'game' itself).")
              return None, None

    # Find images directory (usually game/images)
    potential_images_dir = game_dir / 'images'
    if potential_images_dir.is_dir():
        images_dir = potential_images_dir
        print(f"Found images directory: {images_dir}")
    else:
        print(f"Error: Standard 'game/images' directory not found in '{base_dir}'.")
        return None, None

    return script_dir, images_dir


def get_paths_from_user() -> Tuple[Optional[Path], Optional[Path]]:
    """
    Prompts the user to enter paths manually.

    Returns:
        A tuple containing (script_dir_path, images_dir_path), or (None, None)
        if input is invalid or directories don't exist.
    """
    try:
        images_dir_input = input("Enter the full path of the 'images' directory: ").strip()
        script_dir_input = input("Enter the full path of the script directory (e.g., 'game' or 'game/script'): ").strip()

        images_dir = Path(images_dir_input).resolve()
        script_dir = Path(script_dir_input).resolve()

        valid = True
        if not images_dir.is_dir():
            print(f"Error: Images directory not found: {images_dir}")
            valid = False
        if not script_dir.is_dir():
            print(f"Error: Script directory not found: {script_dir}")
            valid = False
        elif not any(script_dir.rglob('*.rpy')):
             print(f"Warning: No .rpy files found in the specified script directory: {script_dir}")
             # Allow proceeding but warn user

        return (script_dir, images_dir) if valid else (None, None)

    except Exception as e:
        print(f"An error occurred during path input: {e}")
        return None, None

def run_analysis():
    """
    Main execution function. Gets paths, runs analysis, launches GUI.
    """
    script_dir: Optional[Path] = None
    images_dir: Optional[Path] = None

    project_dir_input = input(
        "Enter the full path of the Ren'Py project's base directory\n"
        "(the one containing 'game', 'lib', etc.), or type '1' to define paths manually: "
    ).strip()

    if project_dir_input == '1':
        script_dir, images_dir = get_paths_from_user()
    else:
        project_dir = Path(project_dir_input).resolve()
        if not project_dir.is_dir():
            print(f"Error: The project directory '{project_dir}' does not exist.")
            sys.exit(1)
        script_dir, images_dir = find_project_paths(project_dir)

    # Validate paths before proceeding
    if not script_dir or not images_dir:
        print("\nCould not determine valid script and image directories. Exiting.")
        sys.exit(1)
    if not script_dir.is_dir() or not images_dir.is_dir():
         print("\nOne or more specified directories do not exist. Exiting.")
         sys.exit(1)

    print("\nScanning image files...")
    # Dict: relative_stem (using '/') -> Absolute Path object
    all_image_paths, all_image_names = get_image_names(images_dir)

    print("\nScanning script files for image references...")
    # Set of stems/relative paths (using '/') found in scripts
    used_image_references = extract_image_references(script_dir)

    # --- Determine Unused Images ---
    # An image is considered used if its relative stem (e.g., "chars/eileen_happy", "bg_room")
    # matches a reference found in the scripts.
    unused_stems = all_image_names.difference(used_image_references)

    print(f"\nFound {len(all_image_names)} unique image files (by stem/relative path).")
    print(f"Found {len(used_image_references)} unique image references in scripts.")
    print(f"Found {len(unused_stems)} unused image files.")


    if not unused_stems:
        print("\nSuccess: No unused image files found (excluding internal images).")
        return # Exit gracefully

    print(f"\nFound {len(unused_stems)} potentially unused image files (excluding internal).")

    # Get the full Path objects for the unused stems
    unused_files_paths = [
        Path(path)  # <-- Explicitly convert to Path object here
        for path in all_image_paths
        if Path(path).stem in unused_stems
    ]

    print("\nLaunching Unused Image Reviewer...")
    print("-------------------------------------")
    print(" Instructions:")
    print("  - Left/Right Arrows or < / > buttons: Navigate images.")
    print("  - Delete Key or 'Delete' button: Deletes marked images.")
    print("  - Esc Key or Window Close [X]: Opens deletion confirmation dialog.")
    print("-------------------------------------")


    root = tk.Tk()
    app = UnusedImageViewer(root, set(unused_files_paths), images_dir)

    # --- Bring window to front and give focus ---
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)
    root.focus_force()
    # ---

    sv_ttk.set_theme("dark")

    root.mainloop()

    print("\nReview process finished.")


if __name__ == "__main__":
    try:
        run_analysis()
    except KeyboardInterrupt:
         print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback