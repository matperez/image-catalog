import sqlite3
import argparse
import os
from datetime import datetime

def list_images(db_path='images.db', limit=None, offset=0, search=None):
    """
    Выводит список изображений и их описаний из базы данных.
    
    Args:
        db_path (str): Путь к файлу базы данных
        limit (int): Максимальное количество записей для вывода
        offset (int): Смещение для пагинации
        search (str): Поисковый запрос для фильтрации описаний
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Формируем базовый запрос
        query = '''
            SELECT i.file_path, i.description, i.created_at
            FROM images i
        '''
        
        # Добавляем поиск по описанию, если указан
        if search:
            query += '''
                JOIN images_fts fts ON i.id = fts.rowid
                WHERE images_fts MATCH ?
            '''
        
        # Добавляем сортировку и лимиты
        query += '''
            ORDER BY i.created_at DESC
            LIMIT ? OFFSET ?
        '''
        
        # Выполняем запрос
        params = [search] if search else []
        params.extend([limit if limit else -1, offset])
        c.execute(query, params)
        
        # Получаем результаты
        rows = c.fetchall()
        
        if not rows:
            print("Изображения не найдены.")
            return
        
        # Выводим результаты
        print(f"\nНайдено изображений: {len(rows)}")
        print("-" * 80)
        
        for row in rows:
            file_path = row['file_path']
            description = row['description']
            created_at = datetime.fromisoformat(row['created_at'])
            
            # Проверяем существование файла
            file_exists = os.path.exists(file_path)
            status = "✓" if file_exists else "✗"
            
            print(f"\n{status} {file_path}")
            print(f"Дата индексации: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 40)
            print(description)
            print("-" * 80)
        
    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {str(e)}")
    except Exception as e:
        print(f"Неожиданная ошибка: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    parser = argparse.ArgumentParser(description='Вывод списка изображений из базы данных.')
    parser.add_argument('--db', default='images.db', help='Путь к файлу базы данных (по умолчанию: images.db)')
    parser.add_argument('--limit', type=int, help='Максимальное количество записей для вывода')
    parser.add_argument('--offset', type=int, default=0, help='Смещение для пагинации (по умолчанию: 0)')
    parser.add_argument('--search', help='Поисковый запрос для фильтрации описаний')
    args = parser.parse_args()
    
    list_images(args.db, args.limit, args.offset, args.search)

if __name__ == "__main__":
    main() 