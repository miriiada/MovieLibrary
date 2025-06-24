# database.py
import sqlite3
import os

def init_db():
    conn = sqlite3.connect('data/library.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    try:
        cursor.execute("ALTER TABLE movies ADD COLUMN content_type TEXT NOT NULL DEFAULT 'video'")
    except sqlite3.OperationalError: pass
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, folder_path TEXT NOT NULL UNIQUE,
            poster_path TEXT, content_type TEXT NOT NULL DEFAULT 'video'
        )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS tags (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movie_tags (
            movie_id INTEGER, tag_id INTEGER,
            FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE,
            PRIMARY KEY (movie_id, tag_id))''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT, movie_id INTEGER, file_path TEXT NOT NULL,
            FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE)''')
    conn.commit()
    conn.close()

def get_filtered_movies(selected_tags=None):
    conn = sqlite3.connect('data/library.db')
    cursor = conn.cursor()
    if not selected_tags:
        cursor.execute("SELECT id, title, folder_path FROM movies ORDER BY title ASC")
    else:
        tags_tuple = tuple(selected_tags)
        num_tags = len(tags_tuple)
        query = f"""
            SELECT m.id, m.title, m.folder_path FROM movies m
            JOIN movie_tags mt ON m.id = mt.movie_id
            JOIN tags t ON mt.tag_id = t.id
            WHERE t.name IN ({','.join(['?']*num_tags)})
            GROUP BY m.id HAVING COUNT(DISTINCT t.id) = ?
            ORDER BY m.title ASC
        """
        params = tags_tuple + (num_tags,)
        cursor.execute(query, params)
    movies = cursor.fetchall()
    conn.close()
    return movies

def get_tags_for_movie(movie_id):
    conn = sqlite3.connect('data/library.db')
    cursor = conn.cursor()
    query = "SELECT t.name FROM tags t JOIN movie_tags mt ON t.id = mt.tag_id WHERE mt.movie_id = ? ORDER BY t.name"
    cursor.execute(query, (movie_id,))
    tags = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tags

def get_all_tags():
    conn = sqlite3.connect('data/library.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM tags ORDER BY name")
    all_tags = [row[0] for row in cursor.fetchall()]
    conn.close()
    return all_tags

def add_new_tag(tag_name):
    conn = sqlite3.connect('data/library.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name.strip(),))
    conn.commit()
    conn.close()

def assign_tag_to_movie(movie_id, tag_name):
    conn = sqlite3.connect('data/library.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO movie_tags (movie_id, tag_id) SELECT ?, id FROM tags WHERE name = ?", (movie_id, tag_name))
    conn.commit()
    conn.close()

def remove_tag_from_movie(movie_id, tag_name):
    conn = sqlite3.connect('data/library.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM movie_tags WHERE movie_id = ? AND tag_id = (SELECT id FROM tags WHERE name = ?)", (movie_id, tag_name))
    conn.commit()
    conn.close()

def get_movie_details(movie_id):
    conn = sqlite3.connect('data/library.db')
    cursor = conn.cursor()
    cursor.execute("SELECT title, folder_path, poster_path, content_type FROM movies WHERE id = ?", (movie_id,))
    movie_data = cursor.fetchone()
    if not movie_data:
        conn.close()
        return None
    details = {"title": movie_data[0], "folder_path": movie_data[1], "poster_path": movie_data[2], "content_type": movie_data[3], "files": [], "tags": get_tags_for_movie(movie_id)}
    if details["content_type"] == 'video':
        cursor.execute("SELECT file_path FROM files WHERE movie_id = ? ORDER BY file_path ASC", (movie_id,))
        details["files"] = [file[0] for file in cursor.fetchall()]
    conn.close()
    return details

def update_movie_poster(movie_id, poster_path):
    conn = sqlite3.connect('data/library.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE movies SET poster_path = ? WHERE id = ?", (poster_path, movie_id))
    conn.commit()
    conn.close()

def update_movie_content_type(movie_id, new_type):
    conn = sqlite3.connect('data/library.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE movies SET content_type = ? WHERE id = ?", (new_type, movie_id))
    conn.commit()
    conn.close()

def rename_tag(old_name, new_name):
    conn = sqlite3.connect('data/library.db')
    cursor = conn.cursor()
    new_name = new_name.strip()
    if not new_name:
        conn.close()
        return
    try:
        cursor.execute("UPDATE tags SET name = ? WHERE name = ?", (new_name, old_name))
        conn.commit()
        print(f"Tag '{old_name}' renamed to '{new_name}'.")
    except sqlite3.IntegrityError:
        print(f"Error: A tag with the name '{new_name}' already exists.")
    finally:
        conn.close()

def delete_tag(tag_name):
    conn = sqlite3.connect('data/library.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tags WHERE name = ?", (tag_name,))
    conn.commit()
    conn.close()
    print(f"Tag '{tag_name}' and all its associations have been deleted.")

if __name__ == '__main__':
    if not os.path.exists('data'): os.makedirs('data')
    if not os.path.exists('data/posters'): os.makedirs('data/posters')
    init_db()