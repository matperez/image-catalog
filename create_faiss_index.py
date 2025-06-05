import sqlite3
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import os

# Константы
DB_PATH = 'images.db'
INDEX_PATH = 'image_index.faiss'
MODEL_NAME = 'all-MiniLM-L6-v2'  # Легкая модель для эмбеддингов

def load_descriptions():
    """Загружает описания изображений из базы данных."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, description FROM images')
    results = c.fetchall()
    conn.close()
    return results

def create_embeddings(descriptions):
    """Создает эмбеддинги для описаний изображений."""
    model = SentenceTransformer(MODEL_NAME)
    texts = [desc for _, desc in descriptions]
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings

def create_faiss_index(embeddings, dimension):
    """Создает FAISS индекс."""
    index = faiss.IndexFlatL2(dimension)  # L2 расстояние
    index.add(embeddings.astype(np.float32))
    return index

def save_index(index, index_path):
    """Сохраняет индекс в файл."""
    faiss.write_index(index, index_path)

def main():
    print("Загрузка описаний из базы данных...")
    descriptions = load_descriptions()
    if not descriptions:
        print("В базе данных нет изображений!")
        return

    print(f"Найдено {len(descriptions)} изображений")
    print("Создание эмбеддингов...")
    embeddings = create_embeddings(descriptions)
    
    print("Создание FAISS индекса...")
    dimension = embeddings.shape[1]
    index = create_faiss_index(embeddings, dimension)
    
    print("Сохранение индекса...")
    save_index(index, INDEX_PATH)
    
    print(f"Индекс успешно создан и сохранен в {INDEX_PATH}")
    print(f"Размерность эмбеддингов: {dimension}")
    print(f"Количество векторов в индексе: {index.ntotal}")

if __name__ == "__main__":
    main() 