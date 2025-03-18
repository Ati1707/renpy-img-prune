import os
import re
from pathlib import Path


def get_used_images(script_dir):
    """
    Parse all .rpy files in the given directory and return a set
    of image names used with 'show' or 'scene' commands.
    """
    used_images = set()
    # Regex to capture the image name after "show" or "scene"
    pattern = re.compile(r'^\s*(?:show|scene)\s+([\w_-]+)', re.IGNORECASE)

    # Iterate over all files in the script directory.
    for path, subdirs, files in os.walk(script_dir):
        for filename in files:
            if filename.endswith('.rpy'):
                filepath = os.path.join(path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as file:
                        for line in file:
                            match = pattern.search(line)
                            if match:
                                image_name = match.group(1)
                                used_images.add(image_name)
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
    return used_images


def get_all_images(images_dir):
    """
    Get all image file names in the specified directory with specified extensions.
    """
    all_images = set()
    for path, subdirs, files in os.walk(images_dir):
        for filename in files:
            name, ext = os.path.splitext(filename)
            all_images.add(name)  # Store the name without extension
    return all_images


def main():
    # Ask the user for the project game directory.
    project_dir = input(r"Enter the full path of the project game directory(D:\renpy\Project\game_name\game) or type 1 to define your own paths: ").strip()
    if project_dir != '1':
        project_dir = os.path.abspath(project_dir)

        # Validate that the project directory exists.
        if not os.path.isdir(project_dir):
            print(f"The directory '{project_dir}' does not exist.")
            return

        # Construct script and images directories.
        script_dir = os.path.join(project_dir, 'script')
        images_dir = os.path.join(project_dir, 'images')
    else:
        images_dir = input(r"Enter the full path of the images directory: ").strip()
        script_dir = input(r"Enter the full path of the script directory: ").strip()

    # Ensure these subdirectories exist
    if not os.path.isdir(script_dir):
        print(f"The 'script' folder does not exist in.")
        return
    if not os.path.isdir(images_dir):
        print(f"The 'images' folder does not exist in.")
        return

    # Define acceptable image file extensions.
    image_extensions = {'.png', '.jpg', '.avif', '.webp', '.svg'}

    # Get all image names in the images directory
    all_images = get_all_images(images_dir)

    # Get the set of image names used in the scripts.
    used_images = get_used_images(script_dir)
    print(len(used_images))
    print("Used images found in scripts:", used_images)


    # Find the unused images by taking the set difference.
    unused_images = all_images - used_images

    # Report the unused images.
    if not unused_images:
        print("No unused image files found.")
        return

    print("\nUnused image files:")
    unused_files = []
    for path, subdirs, files in os.walk(images_dir):
        for file in files:
            name, ext = os.path.splitext(file)
            if name in unused_images:
                unused_files.append(os.path.join(path, file))


    for file in unused_files:
        print(file)

    confirm = input("\nDo you want to delete all these files? (y/n): ").strip().lower()

    if confirm == 'y':
        for file in unused_files:
            if os.path.commonpath([os.path.dirname(file), images_dir]) != images_dir:
                print(f"Skipping {file}: not located within the images directory.")
                continue
            try:
                os.remove(file)
                print(f"Deleted {file}")
            except Exception as e:
                print(f"Error deleting {file}: {e}")
    else:
        for file in unused_files:
            if os.path.commonpath([os.path.dirname(file), images_dir]) != images_dir:
                print(f"Skipping {file}: not located within the images directory.")
                continue
            print("No files were deleted.")

if __name__ == "__main__":
    main()