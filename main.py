# main.py
import customtkinter as ctk
import os
import subprocess
import sys
from tkinter import filedialog
import shutil
import sqlite3
from database import (get_filtered_movies, get_movie_details, update_movie_poster,
                      update_movie_content_type, get_all_tags, get_tags_for_movie,
                      add_new_tag, assign_tag_to_movie, remove_tag_from_movie,
                      rename_tag, delete_tag)
from PIL import Image
import functools

IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
VIDEO_EXTENSIONS = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm')
IMAGE_FILE_COUNT_THRESHOLD = 30
IMAGE_PERCENTAGE_THRESHOLD = 0.8


def create_placeholder_image_if_not_exists():
    placeholder_path = os.path.join('data', 'placeholder.png')
    if not os.path.exists(placeholder_path):
        try:
            img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
            img.save(placeholder_path, 'PNG')
        except Exception as e:
            print(f"Could not create placeholder image: {e}")
    return placeholder_path


class EditTagDialog(ctk.CTkInputDialog):
    def __init__(self, *args, initial_value="", **kwargs):
        super().__init__(*args, **kwargs)
        self._entry.insert(0, initial_value)


class TagEditorWindow(ctk.CTkToplevel):
    def __init__(self, master, movie_id):
        super().__init__(master)
        self.master_app = master
        self.movie_id = movie_id
        self.title("Edit Tags")
        self.geometry("600x400")
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grab_set()
        self.transient(master)
        self.new_tag_entry = ctk.CTkEntry(self, placeholder_text="Enter new tag name")
        self.new_tag_entry.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="ew")
        self.add_new_tag_button = ctk.CTkButton(self, text="Add New Global Tag", command=lambda: self._create_new_tag())
        self.add_new_tag_button.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self.available_tags_frame = ctk.CTkScrollableFrame(self, label_text="Available Tags (Click to add)")
        self.available_tags_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.assigned_tags_frame = ctk.CTkScrollableFrame(self, label_text="Assigned Tags (Click to remove)")
        self.assigned_tags_frame.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.refresh_tag_lists()

    def refresh_tag_lists(self):
        for widget in self.available_tags_frame.winfo_children(): widget.destroy()
        for widget in self.assigned_tags_frame.winfo_children(): widget.destroy()
        all_tags = get_all_tags()
        assigned_tags = get_tags_for_movie(self.movie_id)
        for tag in all_tags:
            if tag not in assigned_tags:
                btn = ctk.CTkButton(self.available_tags_frame, text=tag, fg_color="gray",
                                    command=lambda t=tag: self._add_tag(t))
                btn.pack(pady=2, padx=5, fill="x")
        for tag in assigned_tags:
            btn = ctk.CTkButton(self.assigned_tags_frame, text=tag, fg_color="#C0392B", hover_color="#E74C3C",
                                command=lambda t=tag: self._remove_tag(t))
            btn.pack(pady=2, padx=5, fill="x")

    def _add_tag(self, tag_name):
        assign_tag_to_movie(self.movie_id, tag_name)
        self.refresh_tag_lists()

    def _remove_tag(self, tag_name):
        remove_tag_from_movie(self.movie_id, tag_name)
        self.refresh_tag_lists()

    def _create_new_tag(self):
        new_tag = self.new_tag_entry.get().strip()
        if new_tag:
            add_new_tag(new_tag)
            self.new_tag_entry.delete(0, "end")
            self.refresh_tag_lists()

    def _on_close(self):
        self.master_app.populate_sidebar_tags()
        if self.master_app.current_selected_movie_id:
            self.master_app.show_movie_details(self.master_app.current_selected_movie_id)
        self.destroy()


class GlobalTagManagerWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master_app = master
        self.title("Global Tag Manager")
        self.geometry("500x600")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grab_set()
        self.transient(master)
        self.scrollable_frame = ctk.CTkScrollableFrame(self, label_text="All Tags")
        self.scrollable_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.refresh_list()

    def refresh_list(self):
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        for tag_name in get_all_tags():
            row_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=2, padx=5)
            row_frame.grid_columnconfigure(0, weight=1)
            label = ctk.CTkLabel(row_frame, text=tag_name)
            label.grid(row=0, column=0, padx=5, sticky="w")
            delete_button = ctk.CTkButton(row_frame, text="Delete", width=60, fg_color="#D35400", hover_color="#E67E22",
                                          command=lambda name=tag_name: self._delete_tag(name))
            delete_button.grid(row=0, column=2, padx=5)
            edit_button = ctk.CTkButton(row_frame, text="Edit", width=60,
                                        command=lambda name=tag_name: self._edit_tag(name))
            edit_button.grid(row=0, column=1, padx=5)

    def _edit_tag(self, old_name):
        dialog = EditTagDialog(text=f"Enter new name for tag '{old_name}':", title="Rename Tag", initial_value=old_name)
        new_name = dialog.get_input()
        if new_name and new_name.strip():
            rename_tag(old_name, new_name.strip())
            self.refresh_list()

    def _delete_tag(self, tag_name):
        delete_tag(tag_name)
        self.refresh_list()

    def _on_close(self):
        self.master_app.populate_sidebar_tags()
        if self.master_app.current_selected_movie_id:
            self.master_app.show_movie_details(self.master_app.current_selected_movie_id)
        self.destroy()


class ContextMenu(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=8)
        self.copy_button = ctk.CTkButton(self, text="Copy", command=self.copy_text, width=100)
        self.copy_button.pack(padx=5, pady=5)
        self.widget_to_copy_from = None

    def copy_text(self):
        if self.widget_to_copy_from:
            try:
                text = self.widget_to_copy_from.get()
                self.master.clipboard_clear()
                self.master.clipboard_append(text)
                print(f"Copied to clipboard: {text}")
            except Exception as e:
                print(f"Could not copy text: {e}")
        self.hide()

    def show(self, event, widget):
        self.widget_to_copy_from = widget
        self.place(x=event.x_root - self.master.winfo_rootx(), 
                   y=event.y_root - self.master.winfo_rooty())
        self.lift()

    def hide(self, event=None):
        self.place_forget()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.current_selected_movie_id = None
        self.current_folder_path = None  # путь к папке выбранного фильма
        self.tag_editor_window = None
        self.global_tag_manager_window = None
        self.active_filter_tags = set()
        self.tag_checkboxes = {}
        self.preview_window = None
        self.preview_after_id = None
        self.view_mode = "list"  # режим отображения: list или grid
        self.title("My Media Library")
        self.geometry("1400x750")
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Media Library",
                                       font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(padx=20, pady=(20, 10), fill="x")
        self.add_folder_button = ctk.CTkButton(self.sidebar_frame, text="Add Folder",
                                               command=lambda: self.add_folder_dialog())
        self.add_folder_button.pack(padx=20, pady=10, fill="x")
        self.manage_tags_button = ctk.CTkButton(self.sidebar_frame, text="Manage Tags",
                                                command=lambda: self.open_global_tag_manager())
        self.manage_tags_button.pack(padx=20, pady=10, fill="x")
        self.tag_filter_label = ctk.CTkLabel(self.sidebar_frame, text="Filter by Tags:",
                                             font=ctk.CTkFont(weight="bold"))
        self.tag_filter_label.pack(padx=20, pady=(10, 5), anchor="w")
        self.tag_filter_frame = ctk.CTkScrollableFrame(self.sidebar_frame, label_text="")
        self.tag_filter_frame.pack(padx=5, pady=5, fill="both", expand=True)
        self.clear_filters_button = ctk.CTkButton(self.sidebar_frame, text="Clear Filters",
                                                  command=lambda: self.clear_filters())
        self.clear_filters_button.pack(padx=20, pady=10, side="bottom", fill="x")
        self.movie_list_frame = ctk.CTkScrollableFrame(self, label_text="Titles")
        self.movie_list_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.toggle_view_button = ctk.CTkButton(self.movie_list_frame, text="Grid View", command=self.toggle_view_mode)
        self.toggle_view_button.pack(pady=5, padx=5, anchor="ne")
        self.grid_container = None  # контейнер для плиток
        self.details_frame = ctk.CTkFrame(self)
        self.details_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        self.details_frame.grid_columnconfigure(0, weight=1)
        placeholder_path = create_placeholder_image_if_not_exists()
        self.placeholder_image = ctk.CTkImage(Image.open(placeholder_path), size=(250, 375))
        self.details_poster_label = ctk.CTkLabel(self.details_frame, text="No Poster", image=self.placeholder_image,
                                                 compound="center", cursor="hand2")
        self.details_poster_label.pack(pady=10, padx=10)
        self.details_poster_label.bind("<Button-3>", self.open_current_movie_folder)  # ПКМ для открытия папки
        self.details_poster_label.image = self.placeholder_image
        self.title_string_var = ctk.StringVar()
        self.details_title_entry = ctk.CTkEntry(self.details_frame, textvariable=self.title_string_var,
                                                font=ctk.CTkFont(size=20, weight="bold"), state="readonly",
                                                border_width=0, fg_color="transparent")
        self.details_title_entry.pack(pady=10, padx=10, fill="x")
        self.set_poster_button = ctk.CTkButton(self.details_frame, text="Set/Edit Poster",
                                               command=lambda: self.set_poster_for_current_movie())
        self.set_poster_button.pack(pady=5, padx=10)

        # --- THE FIX: Using .pack() for all children of tags_frame ---
        self.tags_frame = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        self.tags_frame.pack(pady=(0, 5), padx=10, fill="x")
        # self.tags_frame.grid_columnconfigure(0, weight=1) # No longer needed
        self.tags_label = ctk.CTkLabel(self.tags_frame, text="Tags: -", wraplength=250, justify="left")
        self.tags_label.pack(side="left", fill="x", expand=True, padx=5)  # Using pack
        self.edit_tags_button = ctk.CTkButton(self.tags_frame, text="Edit Tags", width=80,
                                              command=lambda: self.open_tags_editor())
        self.edit_tags_button.pack(side="right", padx=5)  # Using pack

        self.type_control_frame = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        self.type_control_frame.pack(pady=5, padx=10, fill="x")
        # self.type_control_frame.grid_columnconfigure((1, 2), weight=1) # No longer needed
        self.details_type_label = ctk.CTkLabel(self.type_control_frame, text="Type: -")
        self.details_type_label.pack(side="left", padx=5)  # Using pack
        self.set_gallery_button = ctk.CTkButton(self.type_control_frame, text="Set as Gallery",
                                                command=lambda: self.set_current_movie_as_gallery())
        self.set_gallery_button.pack(side="right", padx=5)  # Using pack
        self.set_video_button = ctk.CTkButton(self.type_control_frame, text="Set as Video",
                                              command=lambda: self.set_current_movie_as_video())
        self.set_video_button.pack(side="right", padx=5)  # Using pack

        self.details_files_scrollable_frame = ctk.CTkScrollableFrame(self.details_frame, label_text="Files")
        self.details_files_scrollable_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.disable_details_buttons()
        self.populate_sidebar_tags()
        self.refresh_movie_list()
        self.context_menu = ContextMenu(self)
        self.bind("<Button-1>", self.context_menu.hide)
        self.bind_all_children(self.sidebar_frame, "<Button-2>", self.open_current_movie_folder)
        self.bind("<Control-c>", self._handle_global_copy)

    def populate_sidebar_tags(self):
        for widget in self.tag_filter_frame.winfo_children(): widget.destroy()
        self.tag_checkboxes.clear()
        all_tags = get_all_tags()
        for tag in all_tags:
            var = ctk.StringVar(value="off")
            cb = ctk.CTkCheckBox(self.tag_filter_frame, text=tag, variable=var, onvalue="on", offvalue="off",
                                 command=lambda: self.apply_filters())
            cb.pack(padx=10, pady=5, anchor="w", fill="x")
            self.tag_checkboxes[tag] = var

    def apply_filters(self):
        selected_tags = [tag for tag, var in self.tag_checkboxes.items() if var.get() == "on"]
        self.refresh_movie_list(selected_tags)

    def clear_filters(self):
        for var in self.tag_checkboxes.values(): var.set("off")
        self.apply_filters()

    def refresh_movie_list(self, tags_to_filter=None):
        # Удаляем все виджеты кроме кнопки-переключателя и grid_container (если есть)
        for widget in self.movie_list_frame.winfo_children():
            if widget is not self.toggle_view_button and widget is not self.grid_container:
                widget.destroy()
        # Удаляем grid_container, если он был создан ранее
        if self.grid_container is not None:
            self.grid_container.destroy()
            self.grid_container = None
        movies = get_filtered_movies(tags_to_filter)
        if self.view_mode == "list":
            for movie_id, title, folder_path in movies:
                is_selected = (movie_id == self.current_selected_movie_id)
                base_color = "#9C27B0" if is_selected else "transparent"
                hover_color = ("#7B1FA2", "#9C27B0") if is_selected else ("#333333", "#555555")
                movie_frame = ctk.CTkFrame(self.movie_list_frame, corner_radius=5, fg_color=base_color)
                movie_frame.pack(pady=2, padx=5, fill="x")
                movie_frame.bind("<Button-1>", lambda e, mid=movie_id: self.show_movie_details(mid))
                movie_frame.bind("<Button-2>", lambda e, path=folder_path: self.open_folder_in_explorer(path))
                title_var = ctk.StringVar(value=title)
                title_entry = ctk.CTkEntry(movie_frame, textvariable=title_var, state="normal", border_width=0,
                                           fg_color="transparent", font=ctk.CTkFont(size=14))
                title_entry.pack(side="left", padx=10, pady=5, fill="x", expand=True)
                title_entry.configure(state="readonly")  # Set to readonly after packing to allow selection
                title_entry.bind("<Button-1>", lambda e, mid=movie_id: self.show_movie_details(mid))
                title_entry.bind("<Button-2>", lambda e, path=folder_path: self.open_folder_in_explorer(path))
                title_entry.bind("<Button-3>", lambda e, w=title_entry: self._handle_title_right_click(e, w))
                self.bind_all_children(title_entry, "<Control-c>", lambda e, w=title_entry: self._copy_to_clipboard(w))
                def on_enter(event, w=movie_frame, sel=is_selected, hc=hover_color, mid=movie_id, te=title_entry):
                    # Don't change the background color on hover
                    # Only show preview
                    if self.preview_after_id:
                        self.after_cancel(self.preview_after_id)
                    self.preview_after_id = self.after(200, lambda: self.show_preview(mid, te))

                def on_leave(event, w=movie_frame, sel=is_selected, bc=base_color):
                    # Check if this is the currently selected movie
                    is_current = False
                    if self.current_selected_movie_id is not None:
                        for child in w.winfo_children():
                            if isinstance(child, ctk.CTkEntry):
                                movie_title = child.get()
                                details = get_movie_details(self.current_selected_movie_id)
                                if details and details["title"] == movie_title:
                                    is_current = True
                    
                    if is_current:
                        w.configure(fg_color="#9C27B0")
                    else:
                        w.configure(fg_color="transparent")
                        
                    if self.preview_after_id:
                        self.after_cancel(self.preview_after_id)
                        self.preview_after_id = None
                    self.hide_preview()
                movie_frame.bind("<Enter>", on_enter)
                movie_frame.bind("<Leave>", on_leave)
                title_entry.bind("<Enter>", on_enter)
                title_entry.bind("<Leave>", on_leave)
        else:  # grid view
            self.grid_container = ctk.CTkFrame(self.movie_list_frame)
            self.grid_container.pack(fill="both", expand=True)
            columns = 4
            thumb_size = (100, 150)
            row = 0
            col = 0
            for movie_id, title, folder_path in movies:
                is_selected = (movie_id == self.current_selected_movie_id)
                base_color = "#9C27B0" if is_selected else "#222222"
                hover_color = ("#7B1FA2", "#9C27B0") if is_selected else ("#333333", "#555555")
                grid_frame = ctk.CTkFrame(self.grid_container, corner_radius=8, fg_color=base_color, width=120, height=210)
                grid_frame.grid(row=row, column=col, padx=10, pady=10, sticky="n")
                grid_frame.grid_propagate(False)
                details = get_movie_details(movie_id)
                poster_path = details.get("poster_path") if details else None
                if poster_path and os.path.exists(poster_path):
                    try:
                        pil_image = Image.open(poster_path)
                        poster_image = ctk.CTkImage(pil_image, size=thumb_size)
                        poster_label = ctk.CTkLabel(grid_frame, image=poster_image, text="")
                        poster_label.pack(pady=(10, 5))
                        poster_label._image = poster_image
                    except Exception:
                        poster_label = ctk.CTkLabel(grid_frame, text="No Poster")
                        poster_label.pack(pady=(10, 5))
                else:
                    poster_label = ctk.CTkLabel(grid_frame, text="No Poster")
                    poster_label.pack(pady=(10, 5))
                title_var = ctk.StringVar(value=title)
                title_entry = ctk.CTkEntry(grid_frame, textvariable=title_var, state="normal",
                                           font=ctk.CTkFont(size=13, weight="bold"), border_width=0,
                                           fg_color="transparent", justify="center")
                title_entry.pack(pady=(0, 10), padx=5, fill="x")
                title_entry.configure(state="readonly")  # Set to readonly after packing to allow selection
                title_entry.bind("<Button-1>", lambda e, mid=movie_id: self.show_movie_details(mid))
                title_entry.bind("<Button-2>", lambda e, path=folder_path: self.open_folder_in_explorer(path))
                
                # Bind events to poster_label
                poster_label.bind("<Button-1>", lambda e, mid=movie_id: self.show_movie_details(mid))
                poster_label.bind("<Button-2>", lambda e, path=folder_path: self.open_folder_in_explorer(path))
                
                # Bind events to title_entry
                title_entry.bind("<Button-1>", lambda e, mid=movie_id: self.show_movie_details(mid))
                title_entry.bind("<Button-2>", lambda e, path=folder_path: self.open_folder_in_explorer(path))
                title_entry.bind("<Button-3>", lambda e, w=title_entry: self._handle_title_right_click(e, w))
                self.bind_all_children(title_entry, "<Control-c>", lambda e, w=title_entry: self._copy_to_clipboard(w))
                
                # Hover effects
                grid_frame.bind("<Enter>", lambda e, w=grid_frame, sel=is_selected, mid=movie_id: self._on_grid_enter_updated(w, sel, mid))
                grid_frame.bind("<Leave>", lambda e, w=grid_frame, sel=is_selected: self._on_grid_leave_updated(w, sel))
                poster_label.bind("<Enter>", lambda e, w=grid_frame, sel=is_selected, mid=movie_id: self._on_grid_enter_updated(w, sel, mid))
                poster_label.bind("<Leave>", lambda e, w=grid_frame, sel=is_selected: self._on_grid_leave_updated(w, sel))
                title_entry.bind("<Enter>", lambda e, w=grid_frame, sel=is_selected, mid=movie_id: self._on_grid_enter_updated(w, sel, mid))
                title_entry.bind("<Leave>", lambda e, w=grid_frame, sel=is_selected: self._on_grid_leave_updated(w, sel))
                
                # Remove these duplicate bindings
                # grid_frame.bind("<Button-1>", functools.partial(self._on_grid_click, movie_id))
                # grid_frame.bind("<Button-2>", lambda e, path=folder_path: self.open_folder_in_explorer(path))
                # poster_label.bind("<Button-1>", functools.partial(self._on_grid_click, movie_id))
                col += 1
                if col >= columns:
                    col = 0
                    row += 1

    def _on_grid_enter_updated(self, grid_frame, is_selected, movie_id):
        # Don't change the background color on hover
        # Only show preview
        if self.preview_after_id:
            self.after_cancel(self.preview_after_id)
        self.preview_after_id = self.after(200, lambda: self.show_preview(movie_id, grid_frame))

    def _on_grid_leave_updated(self, grid_frame, is_selected):
        # Re-check if this is the currently selected movie
        is_current = False
        if self.current_selected_movie_id is not None:
            for child in grid_frame.winfo_children():
                if isinstance(child, ctk.CTkEntry):
                    movie_title = child.get()
                    details = get_movie_details(self.current_selected_movie_id)
                    if details and details["title"] == movie_title:
                        is_current = True
        
        if is_current:
            grid_frame.configure(fg_color="#9C27B0")
        else:
            grid_frame.configure(fg_color="#222222")
            
        if self.preview_after_id:
            self.after_cancel(self.preview_after_id)
            self.preview_after_id = None
        self.hide_preview()

    def disable_details_buttons(self):
        self.set_poster_button.configure(state="disabled")
        self.edit_tags_button.configure(state="disabled")
        self.set_video_button.configure(state="disabled")
        self.set_gallery_button.configure(state="disabled")

    def open_tags_editor(self):
        if self.current_selected_movie_id is None: return
        if self.tag_editor_window is None or not self.tag_editor_window.winfo_exists():
            self.tag_editor_window = TagEditorWindow(self, self.current_selected_movie_id)
        else:
            self.tag_editor_window.focus()

    def open_global_tag_manager(self):
        if self.global_tag_manager_window is None or not self.global_tag_manager_window.winfo_exists():
            self.global_tag_manager_window = GlobalTagManagerWindow(self)
        else:
            self.global_tag_manager_window.focus()

    def show_movie_details(self, movie_id):
        self.current_selected_movie_id = movie_id
        self.disable_details_buttons()
        self.set_poster_button.configure(state="normal")
        self.edit_tags_button.configure(state="normal")
        self.set_video_button.configure(state="normal")
        self.set_gallery_button.configure(state="normal")
        details = get_movie_details(movie_id)
        if not details:
            self.current_folder_path = None
            return
        self.current_folder_path = details.get("folder_path")  # сохраняем путь
        poster_path = details.get("poster_path")
        if poster_path and os.path.exists(poster_path):
            try:
                pil_image = Image.open(poster_path)
                poster_image = ctk.CTkImage(pil_image, size=(250, 375))
                self.details_poster_label.configure(image=poster_image, text="")
                self.details_poster_label.image = poster_image
            except Exception as e:
                self.details_poster_label.configure(image=self.placeholder_image, text="Error")
                self.details_poster_label.image = self.placeholder_image
        else:
            self.details_poster_label.configure(image=self.placeholder_image, text="No Poster")
            self.details_poster_label.image = self.placeholder_image
        self.title_string_var.set(details["title"])
        self.details_type_label.configure(text=f"Type: {details['content_type']}")
        if details["tags"]:
            self.tags_label.configure(text=f"Tags: {', '.join(details['tags'])}")
        else:
            self.tags_label.configure(text="Tags: None")
        for widget in self.details_files_scrollable_frame.winfo_children(): widget.destroy()
        if details["content_type"] == 'gallery':
            info_label = ctk.CTkLabel(self.details_files_scrollable_frame,
                                      text="Image gallery mode.\nFile list is hidden for performance.",
                                      text_color="gray")
            info_label.pack(pady=20)
        else:
            video_files = [f for f in details["files"] if os.path.splitext(f)[1].lower() in VIDEO_EXTENSIONS]
            if not video_files:
                info_label = ctk.CTkLabel(self.details_files_scrollable_frame, text="No video files found.",
                                          text_color="gray")
                info_label.pack(pady=20)
            else:
                for file_path in video_files:
                    file_name = os.path.basename(file_path)
                    file_label = ctk.CTkLabel(self.details_files_scrollable_frame, text=file_name, anchor="w",
                                              cursor="hand2")
                    file_label.pack(anchor="w", padx=10, pady=2)
                    file_label.bind("<Button-1>", lambda e, path=file_path: self.play_file(path))
        self.update_selection_highlight()

    def update_selection_highlight(self):
        # Обновляет выделение выбранного элемента без пересоздания всего списка/сетки
        if self.view_mode == "list":
            for widget in self.movie_list_frame.winfo_children():
                if widget is self.toggle_view_button or widget is self.grid_container:
                    continue
                if isinstance(widget, ctk.CTkFrame):
                    is_selected = False
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkEntry):
                            movie_title = child.get()
                            if self.current_selected_movie_id is not None:
                                details = get_movie_details(self.current_selected_movie_id)
                                if details and details["title"] == movie_title:
                                    is_selected = True
                    widget.configure(fg_color="#9C27B0" if is_selected else "transparent")
        else:
            if self.grid_container is not None:
                for grid_frame in self.grid_container.winfo_children():
                    if not isinstance(grid_frame, ctk.CTkFrame):
                        continue
                    is_selected = False
                    for child in grid_frame.winfo_children():
                        if isinstance(child, ctk.CTkEntry):
                            movie_title = child.get()
                            if self.current_selected_movie_id is not None:
                                details = get_movie_details(self.current_selected_movie_id)
                                if details and details["title"] == movie_title:
                                    is_selected = True
                    grid_frame.configure(fg_color="#9C27B0" if is_selected else "#222222")

    def bind_all_children(self, widget, sequence, func):
        widget.bind(sequence, func)
        for child in widget.winfo_children(): child.bind(sequence, func)

    def play_file(self, file_path):
        if sys.platform == "win32":
            os.startfile(file_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", file_path])
        else:
            subprocess.run(["xdg-open", file_path])

    def open_folder_in_explorer(self, path):
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])

    def add_folder_dialog(self):
        path = filedialog.askdirectory(title="Select a folder with movies")
        if path:
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path): self.add_movie_to_db(item, full_path)
            print("Scanning complete!")
            self.refresh_movie_list()
            self.populate_sidebar_tags()

    def set_current_movie_as_video(self):
        if self.current_selected_movie_id:
            update_movie_content_type(self.current_selected_movie_id, 'video')
            self.show_movie_details(self.current_selected_movie_id)

    def set_current_movie_as_gallery(self):
        if self.current_selected_movie_id:
            update_movie_content_type(self.current_selected_movie_id, 'gallery')
            self.show_movie_details(self.current_selected_movie_id)

    def set_poster_for_current_movie(self):
        if self.current_selected_movie_id is None: return
        source_poster_path = filedialog.askopenfilename(title="Select a poster image",
                                                        filetypes=[("Image Files", "*.jpg *.jpeg *.png *.webp"),
                                                                   ("All files", "*.*")])
        if not source_poster_path: return
        extension = os.path.splitext(source_poster_path)[1]
        destination_poster_path = os.path.join('data', 'posters', f"{self.current_selected_movie_id}{extension}")
        try:
            shutil.copy2(source_poster_path, destination_poster_path)
            update_movie_poster(self.current_selected_movie_id, destination_poster_path)
            self.show_movie_details(self.current_selected_movie_id)
        except Exception as e:
            print(f"Error copying poster file: {e}")

    def add_movie_to_db(self, title, folder_path):
        conn = sqlite3.connect('data/library.db')
        cursor = conn.cursor()
        content_type = 'video'
        try:
            items = os.listdir(folder_path)
            files_only = [f for f in items if os.path.isfile(os.path.join(folder_path, f))]
            if len(files_only) > 0 and len(files_only) > IMAGE_FILE_COUNT_THRESHOLD:
                image_count = sum(1 for f in files_only if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS)
                if (image_count / len(files_only)) > IMAGE_PERCENTAGE_THRESHOLD: content_type = 'gallery'
        except Exception as e:
            print(f"Could not analyze folder contents for content type: {e}")
        try:
            cursor.execute("INSERT INTO movies (title, folder_path, content_type) VALUES (?, ?, ?)",
                           (title, folder_path, content_type))
            movie_id = cursor.lastrowid
            if content_type == 'video':
                for root, _, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        cursor.execute("INSERT INTO files (movie_id, file_path) VALUES (?, ?)", (movie_id, file_path))
            conn.commit()
            print(f"Added title: {title} (Type: {content_type})")
        except sqlite3.IntegrityError:
            print(f"Title from folder {folder_path} already exists in the database.")
        finally:
            conn.close()

    def show_preview(self, movie_id, widget):
        details = get_movie_details(movie_id)
        if not details:
            return
        if not widget.winfo_exists():
            return
        if self.preview_window is None or not self.preview_window.winfo_exists():
            self.preview_window = ctk.CTkToplevel(self)
            self.preview_window.overrideredirect(True)
            self.preview_window.attributes("-topmost", True)
            self.preview_window.withdraw()
            self.preview_poster_label = ctk.CTkLabel(self.preview_window, text="No Poster")
            self.preview_poster_label.pack(padx=10, pady=5)
            self.preview_title_label = ctk.CTkLabel(self.preview_window, text="", font=ctk.CTkFont(size=14, weight="bold"))
            self.preview_title_label.pack(padx=10, pady=(0, 5))
            self.preview_tags_label = ctk.CTkLabel(self.preview_window, text="", font=ctk.CTkFont(size=12))
            self.preview_tags_label.pack(padx=10, pady=(0, 10))
        poster_path = details.get("poster_path")
        if poster_path and os.path.exists(poster_path):
            try:
                pil_image = Image.open(poster_path)
                poster_image = ctk.CTkImage(pil_image, size=(120, 180))
                self.preview_poster_label.configure(image=poster_image, text="")
                self.preview_poster_label.image = poster_image
            except Exception:
                self.preview_poster_label.configure(image=None, text="No Poster")
        else:
            self.preview_poster_label.configure(image=None, text="No Poster")
        self.preview_title_label.configure(text=details["title"])
        tags = details["tags"]
        self.preview_tags_label.configure(text=f"Tags: {', '.join(tags) if tags else 'None'}")
        x = widget.winfo_rootx() + widget.winfo_width() + 10
        y = widget.winfo_rooty()
        self.preview_window.geometry(f"250x260+{x}+{y}")
        self.preview_window.deiconify()
        self.preview_window.lift()

    def hide_preview(self):
        if self.preview_window and self.preview_window.winfo_exists():
            self.preview_window.withdraw()

    def toggle_view_mode(self):
        if self.view_mode == "list":
            self.view_mode = "grid"
            self.toggle_view_button.configure(text="List View")
        else:
            self.view_mode = "list"
            self.toggle_view_button.configure(text="Grid View")
        self.refresh_movie_list()

    def open_current_movie_folder(self, event):
        if self.current_folder_path and os.path.exists(self.current_folder_path):
            self.open_folder_in_explorer(self.current_folder_path)

    def _handle_title_right_click(self, event, widget):
        self.context_menu.show(event, widget)
        return "break"  # Останавливаем распространение события

    def _copy_to_clipboard(self, widget):
        try:
            text = widget.get()
            self.clipboard_clear()
            self.clipboard_append(text)
            print(f"Copied to clipboard: {text}")
        except Exception as e:
            print(f"Could not copy text: {e}")

    def _handle_global_copy(self, event):
        """Handle global Ctrl+C event by copying selected text if any"""
        try:
            selected_widget = self.focus_get()
            if isinstance(selected_widget, ctk.CTkEntry):
                # CTkEntry doesn't have selection_present method, so we'll use the underlying tkinter widget
                try:
                    # Try to get selected text directly from the tkinter widget
                    selected_text = selected_widget.selection_get()
                    self.clipboard_clear()
                    self.clipboard_append(selected_text)
                    print(f"Copied selected text: {selected_text}")
                except:
                    # If no selection, copy the entire text
                    text = selected_widget.get()
                    self.clipboard_clear()
                    self.clipboard_append(text)
                    print(f"Copied entire text: {text}")
        except Exception as e:
            print(f"Error handling copy: {e}")


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    import database

    database.init_db()
    app = App()
    app.mainloop()