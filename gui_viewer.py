"""
Tkinter-based GUI for reviewing and marking unused image files for deletion.
(Version with Delete button triggering deletion of marked files)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Set, List, Optional
import io  # For SVG handling

from PIL import Image, ImageTk, UnidentifiedImageError, ImageFile


def perform_safe_deletion(files_to_delete, base_dir):
    print(f"--- Placeholder Deletion ---")
    deleted_count = 0
    error_count = 0
    if not files_to_delete:
        print("No files marked for deletion.")
        return 0, 0
    print(f"Would delete {len(files_to_delete)} files from {base_dir}:")
    files_successfully_deleted = set() # Keep track of simulated successes
    for f in sorted(list(files_to_delete)):
        try:
            rel_path = f.relative_to(base_dir)
        except ValueError:
            rel_path = f
        try:
            f.unlink() # Or use send2trash
            print(f"   [DELETED] {rel_path}")
            deleted_count += 1
            files_successfully_deleted.add(f) # Track success
        except Exception as e:
            print(f"   [ERROR] Failed to delete {rel_path}: {e}")
            error_count += 1

    # Simulate all deletions successful for placeholder
    deleted_count = len(files_to_delete)
    error_count = 0
    files_successfully_deleted = set(files_to_delete)
    print(f"--- End Placeholder Deletion (Simulated: {deleted_count} deleted, {error_count} errors) ---")
    # Return simulated counts and the set of files 'deleted'
    return deleted_count, error_count, files_successfully_deleted
# --- End Placeholder ---


# Handle truncated images (optional, but often useful)
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Attempt to import cairosvg for SVG support
try:
    import cairosvg

    SVG_SUPPORT = True
except ImportError:
    cairosvg = None
    SVG_SUPPORT = False
    print("Optional dependency 'cairosvg' not found. SVG preview will be disabled.")
    print("Install using: pip install cairosvg")


class UnusedImageViewer:
    """
    GUI window to display potentially unused images and allow marking for deletion.
    """

    # pylint: disable=too-many-instance-attributes # GUI classes often have many attributes
    def __init__(self, master: tk.Tk, unused_files: Set[Path], base_images_dir: Path):
        """
        Initializes the image viewer GUI.

        Args:
            master: The root Tkinter window.
            unused_files: A set of Path objects for the unused image files.
            base_images_dir: The root directory where images were scanned.
        """
        self.master = master
        # Sort files for consistent navigation order
        self.unused_files: List[Path] = sorted(list(unused_files))
        self.base_images_dir = base_images_dir.resolve()  # Ensure absolute path
        self.current_index: int = 0
        self.files_to_delete: Set[Path] = set()
        self.image_cache: Optional[ImageTk.PhotoImage] = None  # Keep reference

        # Variable for the delete checkbox
        self.delete_var = tk.BooleanVar()

        if not self.unused_files:
            messagebox.showinfo("No Unused Images", "No unused image files found to review.")
            self.master.destroy()
            return

        self._setup_ui()
        self._bind_events()

        # Delay initial load slightly to allow window rendering
        self.master.after(100, self.load_image)

    def _setup_ui(self):
        """Configures the Tkinter widgets."""
        self.master.title("Renpy Image Prune")
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.master.minsize(600, 450)
        self.master.geometry("800x650")

        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1) # Image area expands

        self.image_frame = ttk.Frame(main_frame, borderwidth=1, relief=tk.SUNKEN)
        self.image_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        self.image_frame.columnconfigure(0, weight=1)
        self.image_frame.rowconfigure(0, weight=1)

        self.image_label = ttk.Label(self.image_frame, text="Loading...", anchor=tk.CENTER)
        self.image_label.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.image_frame.bind("<Configure>", self._on_resize)
        self._last_frame_size = (0, 0)

        # Control Frame Layout
        self.control_frame = ttk.Frame(main_frame)
        self.control_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
        self.control_frame.columnconfigure(0, weight=1)
        self.control_frame.columnconfigure(1, weight=0)

        self.status_label = ttk.Label(self.control_frame, text="", anchor=tk.W)
        self.status_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)

        # Frame for buttons + checkbox
        button_container = ttk.Frame(self.control_frame)
        button_container.grid(row=0, column=1, sticky=tk.E)

        # Delete Checkbox
        self.delete_checkbox = ttk.Checkbutton(
            button_container,
            text="Mark for Deletion",
            variable=self.delete_var,
            command=self._toggle_delete_mark
        )
        self.delete_checkbox.grid(row=0, column=3, padx=(10, 0), sticky=tk.E) # Column 3

        # Buttons
        # --- "Delete Marked" Button ---
        self.commit_delete_button = ttk.Button(button_container, text="Delete Marked", command=self.commit_deletions)
        self.commit_delete_button.grid(row=0, column=2, padx=5) # Column 2 (was delete_button)

        self.next_nav_button = ttk.Button(button_container, text=">", width=3, command=self.next_image)
        self.next_nav_button.grid(row=0, column=1, padx=(0, 5)) # Column 1

        self.prev_nav_button = ttk.Button(button_container, text="<", width=3, command=self.prev_image)
        self.prev_nav_button.grid(row=0, column=0, padx=(0, 0)) # Column 0


    def _bind_events(self):
        """Binds keyboard shortcuts and window events."""
        self.master.bind("<Left>", self.prev_image)
        self.master.bind("<Prior>", self.prev_image)  # Page Up
        self.master.bind("<Right>", self.next_image)
        self.master.bind("<Next>", self.next_image)  # Page Down
        # --- Delete key now toggles mark status ---
        self.master.bind("<Delete>", self._toggle_delete_mark_event)
        self.master.bind("<Escape>", self.confirm_quit)
        # Bind spacebar to toggle checkbox
        self.master.bind("<space>", self._toggle_delete_mark_event)
        self.master.protocol("WM_DELETE_WINDOW", self.confirm_quit)

    def _on_resize(self, event=None):
        """Handle window resize events to reload image with new thumbnail size."""
        new_size = (self.image_frame.winfo_width(), self.image_frame.winfo_height())
        if new_size != self._last_frame_size and new_size[0] > 1 and new_size[1] > 1:
            if self.master.winfo_viewable():
                self._last_frame_size = new_size
                if hasattr(self, '_after_id') and self._after_id:
                    self.master.after_cancel(self._after_id)
                self._after_id = self.master.after(200, self._load_image_if_ready)

    def _load_image_if_ready(self):
        """Check if frame size is stable before loading"""
        self._after_id = None
        if self.image_frame.winfo_exists() and self.image_frame.winfo_width() > 1 and self.image_frame.winfo_height() > 1:
             self.load_image()

    def _update_status(self):
        """Updates the status label, checkbox, and button states based on current image and marked files."""
        list_len = len(self.unused_files)
        is_list_empty = list_len == 0
        is_last_image = not is_list_empty and (self.current_index == list_len - 1)
        are_files_marked = bool(self.files_to_delete)

        if is_list_empty or self.current_index >= list_len:
            # Handle case where list is empty or index is out of bounds (e.g., after deletion)
            if is_list_empty:
                self.status_label.config(text="No images left to review.")
            else:
                # This state might be briefly hit if deletion happens and list isn't refreshed immediately
                self.status_label.config(text="Updating view...")

            self.delete_var.set(False)
            self.delete_checkbox.config(state=tk.DISABLED)
            self.prev_nav_button.config(state=tk.DISABLED)
            self.next_nav_button.config(state=tk.DISABLED)
            # Disable commit button if list is empty, enable if items are marked (even if list view is empty now)
            self.commit_delete_button.config(state=tk.NORMAL if are_files_marked else tk.DISABLED)
            return

        # --- Normal status update for a valid image ---
        current_path = self.unused_files[self.current_index]
        is_current_marked = current_path in self.files_to_delete

        try:
            relative_path = current_path.relative_to(self.base_images_dir)
        except ValueError:
            relative_path = current_path

        status = f"Image {self.current_index + 1} of {list_len}: {relative_path}"
        if is_current_marked:
            status += " (Marked for Deletion)"
        self.status_label.config(text=status)

        # Update checkbox state
        self.delete_var.set(is_current_marked)
        self.delete_checkbox.config(state=tk.NORMAL)

        # Update button states
        self.prev_nav_button.config(state=tk.NORMAL if self.current_index > 0 else tk.DISABLED)
        self.next_nav_button.config(state=tk.DISABLED if is_last_image else tk.NORMAL)
        # Enable commit button only if there are files marked for deletion
        self.commit_delete_button.config(state=tk.NORMAL if are_files_marked else tk.DISABLED)

    def _toggle_delete_mark(self):
        """Toggles the deletion mark for the current image via checkbox click."""
        if not self.unused_files or self.current_index >= len(self.unused_files):
            return

        current_file = self.unused_files[self.current_index]
        is_marked_now = self.delete_var.get() # State AFTER click

        if is_marked_now:
            if current_file not in self.files_to_delete:
                self.files_to_delete.add(current_file)
                print(f"Marked: {current_file.name}")
        else:
            if current_file in self.files_to_delete:
                self.files_to_delete.discard(current_file)
                print(f"Unmarked: {current_file.name}")

        # Update status label and button states (especially commit button)
        self._update_status()

    def _toggle_delete_mark_event(self, event=None):
        """Handles keyboard events (Space, Delete) to toggle the checkbox/mark."""
        if str(self.delete_checkbox.cget('state')) == tk.NORMAL:
            self.delete_checkbox.invoke() # Simulate a click, triggers _toggle_delete_mark

    def _display_error(self, filepath: Path, message: str):
        """Helper to display an error message in the image label."""
        try:
            relative_path = filepath.relative_to(self.base_images_dir)
        except ValueError:
            relative_path = filepath.name
        error_text = f"{message}:\n{relative_path}"
        self.image_label.config(image='', text=error_text)
        self.image_cache = None
        self.image_label.image = None
        self._update_status() # Update status/buttons even on error

    def _load_svg(self, filepath: Path, target_w: int, target_h: int) -> Optional[Image.Image]:
        """Loads and renders an SVG file if cairosvg is available."""
        if not SVG_SUPPORT or cairosvg is None:
            self._display_error(filepath, "SVG preview requires 'cairosvg'")
            return None
        try:
            png_bytes = cairosvg.svg2png(
                url=str(filepath),
                output_width=target_w,
                output_height=target_h,
                parent_width=target_w,
                parent_height=target_h
            )
            if not png_bytes:
                raise ValueError("cairosvg returned empty output")
            return Image.open(io.BytesIO(png_bytes))
        except Exception as svg_e:
            print(f"Error rendering SVG {filepath}: {svg_e}")
            self._display_error(filepath, f"Error rendering SVG: {svg_e}")
            return None

    def load_image(self, event=None):
        """Loads and displays the image at the current index."""
        if not self.unused_files:
            self.image_label.config(image='', text="No images left to review.")
            self._update_status() # Updates status/buttons for empty list
            # Don't call _disable_controls here, _update_status handles button states
            return

        list_len = len(self.unused_files)
        if self.current_index >= list_len:
            self.current_index = list_len - 1 if list_len > 0 else 0
        if self.current_index < 0:
            self.current_index = 0

        if not self.unused_files: # Check again after index adjustment
             self.image_label.config(image='', text="No images left to review.")
             self._update_status()
             return

        filepath = self.unused_files[self.current_index]

        frame_w = self.image_frame.winfo_width()
        frame_h = self.image_frame.winfo_height()
        target_w = max(100, frame_w - 20)
        target_h = max(100, frame_h - 20)

        self.image_label.config(image='', text=f"Loading {filepath.name}...")
        self._update_status() # Update status/buttons before potentially slow load

        self.master.after(10, self._load_image_task, filepath, target_w, target_h)


    def _load_image_task(self, filepath, target_w, target_h):
        """The actual image loading part, run via 'after'."""
        # Check if index/file changed while load was pending
        if not self.unused_files or self.current_index >= len(self.unused_files) or self.unused_files[self.current_index] != filepath:
            print(f"Skipping load for {filepath.name}, index changed.")
            return

        try:
            img: Optional[Image.Image] = None
            is_svg = filepath.suffix.lower() == '.svg'

            if is_svg:
                img = self._load_svg(filepath, target_w, target_h)
            else:
                img = Image.open(filepath)
                # Convert modes for Tkinter compatibility
                if img.mode == 'P': img = img.convert('RGBA')
                elif img.mode == 'LA': img = img.convert('RGBA')
                elif img.mode not in ('RGB', 'RGBA'):
                    try: img = img.convert('RGBA')
                    except Exception:
                        try: img = img.convert('RGB')
                        except Exception as conv_e:
                            raise ValueError(f"Unsupported image mode: {img.mode}") from conv_e
                img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)

            if img is None: return # Error handled in specific loader

            if img.width <= 0 or img.height <= 0:
                self._display_error(filepath, "Image processed to zero size")
                return

            self.image_cache = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.image_cache, text="")
            self.image_label.image = self.image_cache
            # Update status again after successful load to ensure correct button states
            self._update_status()

        except UnidentifiedImageError:
            self._display_error(filepath, "Cannot open or identify image file")
        except FileNotFoundError:
            self._display_error(filepath, "File not found (already deleted?)")
            self._remove_current_file_from_list(update_view=True) # Remove and reload view
        except Exception as e:
            print(f"Error loading image {filepath}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            self._display_error(filepath, f"Error loading image: {type(e).__name__}")

    def next_image(self, event=None):
        """Moves to the next image if possible."""
        if not self.unused_files or self.current_index >= len(self.unused_files) - 1:
            print("Next requested, but already at the end.")
            return
        self.current_index += 1
        self.load_image()

    def prev_image(self, event=None):
        """Moves to the previous image."""
        if not self.unused_files or self.current_index <= 0:
            print("Prev requested, but already at the beginning.")
            return
        self.current_index -= 1
        self.load_image()

    # --- Removed mark_for_delete method; Delete key now calls _toggle_delete_mark_event ---

    def _remove_current_file_from_list(self, update_view: bool = False):
        """Removes the current file from the list (e.g., if not found)."""
        if not self.unused_files or self.current_index >= len(self.unused_files):
            return

        current_file = self.unused_files[self.current_index]
        print(f"Removing file from review list: {current_file.name}")
        self.unused_files.pop(self.current_index)
        self.files_to_delete.discard(current_file) # Ensure it's not marked

        # Adjust index if necessary (stay at current index unless it was the last)
        if self.current_index >= len(self.unused_files) and len(self.unused_files) > 0:
            self.current_index = len(self.unused_files) - 1

        if update_view:
            if self.unused_files:
                self.load_image() # Reload the image at the (potentially adjusted) index
            else:
                 # List became empty
                 self.image_label.config(image='', text="No images left to review.")
                 self._update_status() # Update buttons for empty list

    def _disable_ui_during_action(self):
        """Disables interactive elements during a potentially long action like deletion."""
        self.commit_delete_button.config(state=tk.DISABLED)
        self.next_nav_button.config(state=tk.DISABLED)
        self.prev_nav_button.config(state=tk.DISABLED)
        self.delete_checkbox.config(state=tk.DISABLED)
        # Keep Escape key binding maybe? Or disable all interaction? Let's unbind nav/action keys.
        self.master.unbind("<Left>")
        self.master.unbind("<Right>")
        self.master.unbind("<Delete>")
        self.master.unbind("<Prior>")
        self.master.unbind("<Next>")
        self.master.unbind("<space>")
        self.master.update_idletasks() # Force UI update

    def _reenable_ui_after_action(self):
        """Re-enables UI elements and re-binds keys after an action."""
        self._bind_events() # Rebind keys
        self._update_status() # Update button states based on current status

    def _prompt_and_perform_deletion(self) -> bool:
        """
        Asks for confirmation and performs deletion of marked files.
        Updates the internal lists and view after deletion.
        Returns True if the user confirmed (Yes or No), False if they Cancelled.
        Closes the window if deletion is performed or user chooses "No".
        """
        if not self.files_to_delete:
            messagebox.showinfo("No Action", "No images are currently marked for deletion.")
            return True # No cancellation, just nothing to do.

        count = len(self.files_to_delete)
        msg = f"{count} image{'s' if count != 1 else ''} marked for deletion.\n\n" \
              f"Permanently delete {'these' if count != 1 else 'this'} file{'s' if count != 1 else ''}?"
        confirm = messagebox.askyesnocancel("Confirm Deletion", msg, icon='warning')

        if confirm is True:  # Yes, delete
            print(f"Proceeding to delete {count} files...")
            self._disable_ui_during_action()
            self.status_label.config(text=f"Deleting {count} files...")
            self.master.update_idletasks()

            # Perform deletion
            # IMPORTANT: Use a copy of the set for iteration if modifying the list below
            files_to_attempt_delete = self.files_to_delete.copy()
            deleted_count, error_count, successfully_deleted_files = perform_safe_deletion(
                files_to_attempt_delete, self.base_images_dir
            )

            info_msg = f"Deletion finished.\nDeleted: {deleted_count}\nErrors/Skipped: {error_count}"
            messagebox.showinfo("Deletion Complete", info_msg)

            # --- Update internal state ---
            # Remove successfully deleted files from the main list and the marked set
            self.files_to_delete.difference_update(successfully_deleted_files) # Remove deleted from marked set
            original_list_len = len(self.unused_files)
            self.unused_files = [f for f in self.unused_files if f not in successfully_deleted_files]
            files_removed_from_list = original_list_len - len(self.unused_files)
            print(f"Removed {files_removed_from_list} files from the review list.")

            if not self.unused_files:
                self.current_index = 0
                self.image_label.config(image='', text="No images left to review.")
                self._update_status() # Update controls for empty list
            elif self.current_index >= len(self.unused_files):
                self.current_index = len(self.unused_files) - 1
                self.load_image() # Load last image
            else:
                # Still valid files, load image at current index (which might be a new image)
                self.load_image()
            self._reenable_ui_after_action() # Re-enable UI
            return True


        elif confirm is False:  # No, don't delete, just quit
            print("Quitting without deleting marked files.")
            self.master.quit()
            self.master.destroy()
            return True # User made a choice (Yes/No)
        else:  # Cancel
            print("Deletion cancelled.")
            # Re-enable UI if it was disabled (though it wasn't in the Cancel path yet)
            # self._reenable_ui_after_action() # Not strictly needed here, but good practice
            return False # User cancelled

    def commit_deletions(self, event=None):
        """Handles the 'Delete Marked' button click."""
        self._prompt_and_perform_deletion()

    def confirm_quit(self, event=None):
        """Handles window close or Escape key."""
        if self.files_to_delete:
            # If files are marked, use the standard deletion prompt which handles Yes/No/Cancel
            self._prompt_and_perform_deletion()
            # If prompt_and_perform_deletion was cancelled, we stay in the app.
            # If it was Yes/No, it closes the app.
        else:
            # No files marked, just ask to quit
            if messagebox.askyesno("Quit", "No images marked for deletion.\nQuit review?"):
                self.master.quit()
                self.master.destroy()