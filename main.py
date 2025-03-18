import re
from pathlib import Path

IMAGE_EXTENSIONS = {'.png', '.jpg', '.avif', '.webp', '.svg'}

def get_used_images(script_dir):
    """
    Parse all .rpy files in the given directory and return a set
    of image names used with 'show' or 'scene' commands.
    """
    used_images = set()
    pattern = re.compile(r'^\s*(?:show|scene)\s+([\w_-]+)', re.IGNORECASE)

    for filepath in Path(script_dir).rglob('*.rpy'):
        try:
            with filepath.open('r', encoding='utf-8') as file:
                for line in file:
                    match = pattern.search(line)
                    if match:
                        used_images.add(match.group(1))
        except Exception as e:
            print(f"Error reading {filepath}: {e}")

    return used_images

def get_all_images(images_dir):
    """
    Get all image file names in the specified directory with specified extensions.
    """
    all_images = set()
    for filepath in Path(images_dir).rglob('*'):
        if filepath.suffix in IMAGE_EXTENSIONS:
            all_images.add(filepath.stem)
    return all_images

def main():
    project_dir = input("Enter the full path of the project game directory or type 1 to define your own paths: ").strip()

    if project_dir != '1':
        project_dir = Path(project_dir).resolve()
        if not project_dir.is_dir():
            print(f"The directory '{project_dir}' does not exist.")
            return
        script_dir = project_dir / 'script'
        images_dir = project_dir / 'images'
    else:
        images_dir = Path(input("Enter the full path of the images directory: ").strip()).resolve()
        script_dir = Path(input("Enter the full path of the script directory: ").strip()).resolve()

    if not script_dir.is_dir():
        print(f"The 'script' folder does not exist.")
        return
    if not images_dir.is_dir():
        print(f"The 'images' folder does not exist.")
        return

    all_images = get_all_images(images_dir)
    used_images = get_used_images(script_dir)

    #We redefine the set to remove internal images like scene black etc.
    used_images = {image for image in used_images if image in all_images}

    print(f"Total images in the 'images' folder is: {len(all_images)}")
    print(f"Used images found in scripts ({len(used_images)}):")

    unused_images = all_images - used_images
    if not unused_images:
        print("No unused image files found.")
        return

    print("\nUnused image files:")
    unused_files = [filepath for filepath in images_dir.rglob('*') if filepath.stem in unused_images]

    for file in unused_files:
        print(file)

    confirm = input("\nDo you want to delete all these files? (y/n): ").strip().lower()
    if confirm == 'y':
        for file in unused_files:
            if images_dir not in file.parents:
                print(f"Skipping {file}: not located within the images directory.")
                continue
            try:
                file.unlink()
                print(f"Deleted {file}")
            except Exception as e:
                print(f"Error deleting {file}: {e}")
    else:
        print("No files were deleted.")

if __name__ == "__main__":
    main()
