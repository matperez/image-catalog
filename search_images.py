import sqlite3
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import sys
import os

# Константы
DB_PATH = 'images.db'
INDEX_PATH = 'image_index.faiss'
MODEL_NAME = 'all-MiniLM-L6-v2'

def load_index():
    """Загружает FAISS индекс."""
    if not os.path.exists(INDEX_PATH):
        raise FileNotFoundError(f"Индекс не найден: {INDEX_PATH}")
    return faiss.read_index(INDEX_PATH)

def load_model():
    """Загружает модель для создания эмбеддингов."""
    return SentenceTransformer(MODEL_NAME)

def search_similar(query, index, model, k=5):
    """Ищет похожие изображения по текстовому запросу."""
    # Создаем эмбеддинг для запроса
    query_embedding = model.encode([query])
    
    # Ищем ближайших соседей
    distances, indices = index.search(query_embedding.astype(np.float32), k)
    
    return distances[0], indices[0]

def get_image_info(image_ids):
    """Получает информацию об изображениях из базы данных."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    placeholders = ','.join('?' * len(image_ids))
    query = f'SELECT id, file_path, description FROM images WHERE id IN ({placeholders})'
    
    c.execute(query, image_ids)
    results = c.fetchall()
    conn.close()
    
    return results

def main():
    if len(sys.argv) < 2:
        print("Использование: python search_images.py <текстовый_запрос>")
        sys.exit(1)
    
    query = ' '.join(sys.argv[1:])
    
    try:
        print("Загрузка индекса...")
        index = load_index()
        
        print("Загрузка модели...")
        model = load_model()
        
        print(f"Поиск похожих изображений для запроса: '{query}'")
        distances, indices = search_similar(query, index, model)
        
        print("\nРезультаты поиска:")
        print("-" * 80)
        
        image_info = get_image_info(indices.tolist())
        
        for (distance, (image_id, file_path, description)) in zip(distances, image_info):
            print(f"\nРасстояние: {distance:.4f}")
            print(f"ID: {image_id}")
            print(f"Путь: {file_path}")
            print(f"Описание: {description}")  # Выводим полное описание
            print("-" * 80)
            
    except Exception as e:
        print(f"Ошибка: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 