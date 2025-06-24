# # ui_windows.py
# import customtkinter as ctk
# from database import (get_all_tags, get_tags_for_movie, add_new_tag, assign_tag_to_movie,
#                       remove_tag_from_movie, rename_tag, delete_tag)
#
# class EditTagDialog(ctk.CTkInputDialog):
#     def __init__(self, *args, initial_value="", **kwargs):
#         super().__init__(*args, **kwargs)
#         self._entry.insert(0, initial_value)
#
# class TagEditorWindow(ctk.CTkToplevel):
#     def __init__(self, master, movie_id):
#         super().__init__(master)
#         self.master_app = master
#         self.movie_id = movie_id
#         self.title("Edit Tags")
#         self.geometry("600x400")
#         self.grid_columnconfigure((0, 1), weight=1)
#         self.grid_rowconfigure(2, weight=1)
#         self.grab_set()
#         self.transient(master)
#
#         self.new_tag_entry = ctk.CTkEntry(self, placeholder_text="Enter new tag name")
#         self.new_tag_entry.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="ew")
#         self.add_new_tag_button = ctk.CTkButton(self, text="Add New Global Tag", command=lambda: self._create_new_tag())
#         self.add_new_tag_button.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
#
#         self.available_tags_frame = ctk.CTkScrollableFrame(self, label_text="Available Tags (Click to add)")
#         self.available_tags_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
#         self.assigned_tags_frame = ctk.CTkScrollableFrame(self, label_text="Assigned Tags (Click to remove)")
#         self.assigned_tags_frame.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
#
#         self.protocol("WM_DELETE_WINDOW", self._on_close)
#         self.refresh_tag_lists()
#
#     def refresh_tag_lists(self):
#         for widget in self.available_tags_frame.winfo_children(): widget.destroy()
#         for widget in self.assigned_tags_frame.winfo_children(): widget.destroy()
#         all_tags = get_all_tags()
#         assigned_tags = get_tags_for_movie(self.movie_id)
#         for tag in all_tags:
#             if tag not in assigned_tags:
#                 btn = ctk.CTkButton(self.available_tags_frame, text=tag, fg_color="gray", command=lambda t=tag: self._add_tag(t))
#                 btn.pack(pady=2, padx=5, fill="x")
#         for tag in assigned_tags:
#             btn = ctk.CTkButton(self.assigned_tags_frame, text=tag, fg_color="#C0392B", hover_color="#E74C3C", command=lambda t=tag: self._remove_tag(t))
#             btn.pack(pady=2, padx=5, fill="x")
#
#     def _add_tag(self, tag_name):
#         assign_tag_to_movie(self.movie_id, tag_name)
#         self.refresh_tag_lists()
#     def _remove_tag(self, tag_name):
#         remove_tag_from_movie(self.movie_id, tag_name)
#         self.refresh_tag_lists()
#     def _create_new_tag(self):
#         new_tag = self.new_tag_entry.get().strip()
#         if new_tag:
#             add_new_tag(new_tag)
#             self.new_tag_entry.delete(0, "end")
#             self.refresh_tag_lists()
#     def _on_close(self):
#         self.master_app.populate_sidebar_tags()
#         if self.master_app.current_selected_movie_id:
#             self.master_app.show_movie_details(self.master_app.current_selected_movie_id)
#         self.destroy()
#
# class GlobalTagManagerWindow(ctk.CTkToplevel):
#     def __init__(self, master):
#         super().__init__(master)
#         self.master_app = master
#         self.title("Global Tag Manager")
#         self.geometry("500x600")
#         self.grid_columnconfigure(0, weight=1)
#         self.grid_rowconfigure(0, weight=1)
#         self.grab_set()
#         self.transient(master)
#         self.scrollable_frame = ctk.CTkScrollableFrame(self, label_text="All Tags")
#         self.scrollable_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
#         self.scrollable_frame.grid_columnconfigure(0, weight=1)
#         self.protocol("WM_DELETE_WINDOW", self._on_close)
#         self.refresh_list()
#
#     def refresh_list(self):
#         for widget in self.scrollable_frame.winfo_children(): widget.destroy()
#         for tag_name in get_all_tags():
#             row_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
#             row_frame.pack(fill="x", pady=2, padx=5)
#             row_frame.grid_columnconfigure(0, weight=1)
#             label = ctk.CTkLabel(row_frame, text=tag_name)
#             label.grid(row=0, column=0, padx=5, sticky="w")
#             delete_button = ctk.CTkButton(row_frame, text="Delete", width=60, fg_color="#D35400", hover_color="#E67E22", command=lambda name=tag_name: self._delete_tag(name))
#             delete_button.grid(row=0, column=2, padx=5)
#             edit_button = ctk.CTkButton(row_frame, text="Edit", width=60, command=lambda name=tag_name: self._edit_tag(name))
#             edit_button.grid(row=0, column=1, padx=5)
#
#     def _edit_tag(self, old_name):
#         dialog = EditTagDialog(text=f"Enter new name for tag '{old_name}':", title="Rename Tag", initial_value=old_name)
#         new_name = dialog.get_input()
#         if new_name and new_name.strip():
#             rename_tag(old_name, new_name.strip())
#             self.refresh_list()
#     def _delete_tag(self, tag_name):
#         delete_tag(tag_name)
#         self.refresh_list()
#     def _on_close(self):
#         self.master_app.populate_sidebar_tags()
#         if self.master_app.current_selected_movie_id:
#             self.master_app.show_movie_details(self.master_app.current_selected_movie_id)
#         self.destroy()