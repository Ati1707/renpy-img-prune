"""
Functions for parsing Ren'Py (.rpy) script files to find image references.
"""

import re
from pathlib import Path
from typing import Set

from config import SHOW_SCENE_PATTERN, DEFINE_IMAGE_PATTERN, IMAGEBUTTON_PATTERN

def extract_image_references(script_dir: Path) -> Set[str]:
    """
    Parses all .rpy files in the given directory and its subdirectories
    to find image names/paths used with 'show', 'scene', 'image', or 'imagebutton'.

    Args:
        script_dir: The Path object representing the directory containing .rpy files.

    Returns:
        A set of unique image stems or relative paths (using '/') found in the scripts.
    """
    used_image_references: Set[str] = set()

    if not script_dir.is_dir():
        print(f"Warning: Script directory does not exist: {script_dir}")
        return used_image_references

    # Compile regex patterns for efficiency
    show_scene_re = re.compile(SHOW_SCENE_PATTERN, re.IGNORECASE | re.MULTILINE)
    define_image_re = re.compile(DEFINE_IMAGE_PATTERN, re.IGNORECASE | re.MULTILINE)
    imagebutton_re = re.compile(IMAGEBUTTON_PATTERN, re.IGNORECASE)

    print(f"Scanning for script files in: {script_dir.resolve()}")

    for filepath in script_dir.rglob('*.rpy'):
        try:
            with filepath.open('r', encoding='utf-8') as file:
                content = file.read()

                # Find images used in show/scene
                for match in show_scene_re.finditer(content):
                    ref = match.group(1).strip()
                    # Normalize path separators just in case
                    used_image_references.add(ref.replace('\\', '/'))

                # Find images defined with 'image' keyword (extract the defined name)
                for match in define_image_re.finditer(content):
                    ref = match.group(1).strip()
                    used_image_references.add(ref.replace('\\', '/'))

                # Find images used in imagebutton definitions (extract the path)
                for match in imagebutton_re.finditer(content):
                    path_pattern = match.group(1).strip()
                    # Extract the base path part, removing placeholders like %s, %d
                    # This is a simplification; complex patterns might not be fully covered.
                    # It assumes paths like "images/button_%s.png" or "button_%s"
                    base_path = re.sub(r'%.', '', path_pattern).strip()
                    # Remove extension if present
                    base_path_no_ext = Path(base_path).with_suffix('').as_posix()
                    if base_path_no_ext:
                         # Normalize and add relative path if applicable
                         # Assume paths starting without 'images/' might be relative to images dir
                         if not base_path_no_ext.startswith('images/'):
                              # This logic might need refinement based on project structure.
                              # Let's add it as found for now. The comparison later handles it.
                              pass # Keep the reference as found e.g. "mybutton_"

                         used_image_references.add(base_path_no_ext)


        except UnicodeDecodeError:
             print(f"Warning: Could not decode {filepath} as UTF-8. Skipping.")
        except Exception as e:
            print(f"Warning: Error reading or parsing {filepath}: {e}")

    print(f"Found {len(used_image_references)} unique image references in scripts.")
    return used_image_references