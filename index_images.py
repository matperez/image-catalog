import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime
from extract_exif import extract_exif_data
from describe_image import get_image_description

DB_PATH = 'images.db'
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.heic', '.gif'}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Основная таблица
    c.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL UNIQUE,
            exif_json TEXT,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # FTS таблица
    c.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS image_descriptions USING fts5(description, content='images', content_rowid='id');
    ''')
    # Триггер на вставку
    c.execute('''
        CREATE TRIGGER IF NOT EXISTS images_ai AFTER INSERT ON images BEGIN
            INSERT INTO image_descriptions(rowid, description) VALUES (new.id, new.description);
        END;
    ''')
    # Триггер на обновление
    c.execute('''
        CREATE TRIGGER IF NOT EXISTS images_au AFTER UPDATE ON images BEGIN
            UPDATE image_descriptions SET description = new.description WHERE rowid = new.id;
        END;
    ''')
    conn.commit()
    conn.close()

def is_image_file(filename):
    return os.path.splitext(filename)[1].lower() in IMAGE_EXTENSIONS

def index_images_in_directory(directory, recursive=False):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for root, _, files in os.walk(directory):
        for file in files:
            if not is_image_file(file):
                continue
            file_path = os.path.abspath(os.path.join(root, file))
            print(f'Индексирую: {file_path}')
            # Проверяем, есть ли уже такая запись
            c.execute('SELECT id FROM images WHERE file_path = ?', (file_path,))
            if c.fetchone():
                print('  Уже в базе, пропускаю.')
                continue
            # Получаем exif
            exif = extract_exif_data(file_path)
            exif_json = json.dumps(exif, ensure_ascii=False)
            # Получаем описание
            description = get_image_description(file_path)
            # Сохраняем в базу
            c.execute('''
                INSERT INTO images (file_path, exif_json, description) VALUES (?, ?, ?)
            ''', (file_path, exif_json, description))
            conn.commit()
            print('  Готово!')
        if not recursive:
            break
    conn.close()

def main():
    parser = argparse.ArgumentParser(description='Индексация изображений в каталоге.')
    parser.add_argument('directory', help='Путь к каталогу с изображениями')
    parser.add_argument('-r', '--recursive', action='store_true', help='Рекурсивный обход каталога')
    args = parser.parse_args()
    if not os.path.isdir(args.directory):
        print('Указанный путь не является каталогом!')
        sys.exit(1)
    init_db()
    index_images_in_directory(args.directory, args.recursive)
    print('Индексация завершена.')

if __name__ == '__main__':
    main() 