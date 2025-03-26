# Set of image file extensions to look for (lowercase)
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.avif', '.webp', '.svg'}

# Regex for finding image usage (show/scene) in .rpy files
# Handles optional attributes after the image name
# Example: show eileen happy
# Example: scene bg room
SHOW_SCENE_PATTERN = r'^\s*(?:show|scene)\s+([\w\/-]+)(?:\s+.*)?$' # Allow '/' for paths like gui/button

# Regex for finding image definitions in .rpy files
# Example: image logo = "images/logo.png"
# Catches the defined name (e.g., 'logo')
DEFINE_IMAGE_PATTERN = r'^\s*image\s+([\w\/-]+)\s*=\s*".*?"' # Allow '/' for paths

# Regex for finding imagebutton definitions and extracting image paths
# Example: imagebutton auto "images/button_%s.png" action NullAction()
IMAGEBUTTON_PATTERN = r'imagebutton\s+(?:auto\s+)?(?:hover\s*)?"(.*?)"'

# Directory names commonly used for scripts in Ren'Py projects
SCRIPT_DIR_NAMES = ["game", "script", "scripts"]