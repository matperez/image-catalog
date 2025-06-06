import os
import sys
import json
import sqlite3
import argparse
from extract_exif import extract_exif_data
from describe_image import describe_image
from PIL import Image
from PIL.ExifTags import TAGS

DB_PATH = 'images.db'
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png'}

def init_db():
    """Инициализация базы данных и создание необходимых таблиц."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Создаем основную таблицу для изображений
    c.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE,
            exif_json TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Создаем таблицу для полнотекстового поиска
    c.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS images_fts USING fts5(
            file_path,
            description,
            content='images',
            content_rowid='id'
        )
    ''')
    
    # Создаем триггеры для поддержания FTS таблицы в актуальном состоянии
    c.execute('''
        CREATE TRIGGER IF NOT EXISTS images_ai AFTER INSERT ON images BEGIN
            INSERT INTO images_fts(rowid, file_path, description)
            VALUES (new.id, new.file_path, new.description);
        END
    ''')
    
    c.execute('''
        CREATE TRIGGER IF NOT EXISTS images_ad AFTER DELETE ON images BEGIN
            INSERT INTO images_fts(images_fts, rowid, file_path, description)
            VALUES('delete', old.id, old.file_path, old.description);
        END
    ''')
    
    c.execute('''
        CREATE TRIGGER IF NOT EXISTS images_au AFTER UPDATE ON images BEGIN
            INSERT INTO images_fts(images_fts, rowid, file_path, description)
            VALUES('delete', old.id, old.file_path, old.description);
            INSERT INTO images_fts(rowid, file_path, description)
            VALUES (new.id, new.file_path, new.description);
        END
    ''')
    
    conn.commit()
    return conn

def is_image_file(filename):
    """Проверяет, является ли файл изображением."""
    return os.path.splitext(filename)[1].lower() in IMAGE_EXTENSIONS

def extract_exif(image_path):
    """Извлечение EXIF данных из изображения."""
    try:
        image = Image.open(image_path)
        exif_data = {}
        
        if hasattr(image, '_getexif') and image._getexif() is not None:
            for tag_id in image._getexif():
                tag = TAGS.get(tag_id, tag_id)
                data = image._getexif().get(tag_id)
                if isinstance(data, bytes):
                    data = data.decode(errors='replace')
                exif_data[tag] = str(data)
        
        return exif_data
    except Exception as e:
        print(f"  Ошибка при извлечении EXIF: {str(e)}")
        return {}

def index_images_in_directory(directory, recursive=False):
    """Индексация всех изображений в указанной директории."""
    conn = init_db()
    c = conn.cursor()
    
    # Получаем список уже проиндексированных файлов
    c.execute('SELECT file_path FROM images')
    indexed_files = {row[0] for row in c.fetchall()}
    
    # Поддерживаемые форматы изображений
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.raw', '.cr2', '.nef', '.arw', '.pef'}
    
    # Функция для обработки одного файла
    def process_file(file_path):
        if file_path in indexed_files:
            print(f"  Файл уже проиндексирован: {file_path}")
            return
        
        print(f"Обработка {file_path}...")
        
        # Извлекаем EXIF
        print("  Извлечение EXIF...")
        exif_data = extract_exif(file_path)
        
        # Получаем описание
        print("  Генерация описания...")
        try:
            description_data = describe_image(file_path)
            description = description_data["description"]  # Берем только текстовое описание
        except Exception as e:
            print(f"  Ошибка при генерации описания: {str(e)}")
            description = ""
        
        # Сохраняем в базу данных
        try:
            c.execute('''
                INSERT INTO images (file_path, exif_json, description)
                VALUES (?, ?, ?)
            ''', (file_path, json.dumps(exif_data), description))
            conn.commit()
            print(f"  Файл успешно проиндексирован")
        except sqlite3.IntegrityError:
            print(f"  Ошибка: файл уже существует в базе данных")
        except Exception as e:
            print(f"  Ошибка при сохранении в базу данных: {str(e)}")
    
    # Обрабатываем файлы
    if recursive:
        for root, _, files in os.walk(directory):
            for file in files:
                if os.path.splitext(file.lower())[1] in image_extensions:
                    process_file(os.path.join(root, file))
    else:
        for file in os.listdir(directory):
            if os.path.splitext(file.lower())[1] in image_extensions:
                process_file(os.path.join(directory, file))
    
    conn.close()

def main():
    parser = argparse.ArgumentParser(description='Индексация изображений в указанной директории.')
    parser.add_argument('directory', help='Путь к директории с изображениями')
    parser.add_argument('-r', '--recursive', action='store_true', help='Рекурсивный обход поддиректорий')
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print('Указанный путь не является каталогом!')
        sys.exit(1)
    
    index_images_in_directory(args.directory, args.recursive)
    print('Индексация завершена.')

if __name__ == "__main__":
    main() 