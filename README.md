## Media Library
A personalized media library manager for local collections, designed for convenient cataloging and navigation of video and graphic novel content. The application is built with Python using the CustomTkinter graphical library.

(A placeholder screenshot of the application's UI)

## About The Project
This project was created as an alternative to existing media servers, with a focus on local use, high performance, and a flexible manual management system. The core idea is to provide the user with complete control over their collection, from posters to a unique tagging system, without depending on external online services.

## Key Features

## 📚 Library Management
- **Add Content**: Simply point the application to a parent folder, and it will automatically scan all subdirectories, treating each one as a unique title.
- **Local Database**: All information about your collection is stored locally in a `data/library.db` file (SQLite), ensuring privacy and fast access.
- **Automatic Content-Type Detection**: The application automatically analyzes a folder's contents and assigns it a type:
- `video`: For standard folders containing video files.
- `gallery`: For folders with a large number of images (e.g., manga or comics), which prevents loading a list of thousands of files to maintain performance.
- **Manual Type Override**: You can always manually change the content type for any title through the UI.
  
## 🖼️ Visual Presentation
- **Dual View Modes**: Switch between a classic vertical list view and a visually-oriented grid view with posters.
- **Custom Posters**: Easily add or change the poster for any title. The application copies your selected image to the local `data/posters` folder and links it to the title.
- **Details Panel**: Selecting a title displays an information panel on the right, showing the large poster, full title, content type, a list of tags, and a list of files (for video types).
  
## 🏷️ Advanced Tagging System
- **Global Tag Management**: A dedicated "Manage Tags" window allows you to create, rename (case-sensitively), and delete tags from the entire system.
- **Title-Specific Tag Editor**: A user-friendly editor lets you quickly assign and unassign tags for a specific title by selecting from the global list.
- **Filter by Tags**: A powerful filtering system in the sidebar allows you to display only the titles that contain all of the tags you have selected.
  
## ✨ User Experience (UX)
- **Copyable Titles**: Title text in both the main list and the details card can be easily selected and copied (Ctrl+C), simplifying manual searches for information online.
- **Persistent Selection Highlight**: The currently selected title remains highlighted with a distinct color, so you never lose track of it.
- **Hover Preview (Tooltip)**: Hover your mouse over any title in the list for a moment, and a small pop-up card will appear with its poster and tags for a quick preview.
- **Quick File Access**:
- **Middle-clicking** on a title opens its folder in the system's file explorer.
- **Left-clicking** on a file in the details card plays it in your default media player.
  
## Installation and Setup
The project is written in Python and requires a few libraries to be installed.

**1. Prerequisites:**
- Python 3.10+

**2. Creating a Virtual Environment (Recommended):**

```bash
# Create a folder for the environment
python -m venv .venv

# Activate it
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

## 3. Installing Dependencies:
Install the required libraries using pip.

```bash
pip install customtkinter
pip install Pillow
```

## 4. Running the Application:
After installation, simply run the main file.

```bash
python main.py
```
On the first launch, the application will automatically create a `data` directory containing the `library.db` database file and a `posters` folder.

## Project Structure
```bash
/
├── main.py             # Main application file (GUI, logic)
├── database.py         # All functions for SQLite database interaction
└── data/
    ├── library.db      # The database file
    └── posters/        # Folder for storing poster images
```
