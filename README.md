This script helps you identify unused images in your Ren'Py project and optionally deletes them.

## Requirements
  Python 3.12 or higher
  Pillow 11.1.0
  sv-ttk 2.6.0
  (optional)
  pip install cairosvg if you use svg images
  
## Usage
This script works with Ren'Py projects that have separate folders for images and scripts. Follow these steps to use the script:

1. **Run the Script or use the Binary in [Release](https://github.com/Ati1707/renpy-img-prune/releases)**:

```bash
python main.py
```
2. **Directory Structure**:

If your folders are named images and scripts, enter the full path of your project's directory when prompted. For example:
```bash
D:\renpy\Project\game_name
```
If your folders have different names, type 1 when prompted and provide the full paths for your images and scripts directories.

3. **Script Execution**:

The script will scan your images directory and the scripts directory.  
It will identify images that are not used in your scripts and list them.  
You will have the option to delete the unused images.  
