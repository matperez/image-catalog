import requests
import base64
import sys
import argparse
from PIL import Image
import io
import json
from datetime import datetime
import logging
import os

# Создаем каталог для логов, если его нет
LOGS_DIR = 'logs'
os.makedirs(LOGS_DIR, exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'image_descriptions.log')),
        logging.StreamHandler()
    ]
)

def resize_image(image_path: str, max_size: int = 1600) -> Image.Image:
    """
    Изменяет размер изображения, сохраняя пропорции.
    Большая сторона будет не более max_size пикселей.
    
    Args:
        image_path (str): Путь к файлу изображения
        max_size (int): Максимальный размер большей стороны в пикселях
        
    Returns:
        Image.Image: Изображение с измененным размером
    """
    try:
        with Image.open(image_path) as img:
            # Получаем текущие размеры
            width, height = img.size
            
            # Определяем, какая сторона больше
            if width > height:
                new_width = min(width, max_size)
                new_height = int(height * (new_width / width))
            else:
                new_height = min(height, max_size)
                new_width = int(width * (new_height / height))
            
            # Изменяем размер
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logging.info(f"Изображение изменено с {width}x{height} на {new_width}x{new_height}")
            return resized_img
            
    except Exception as e:
        logging.error(f"Ошибка при изменении размера изображения {image_path}: {str(e)}")
        raise

def encode_image_to_base64(image_path: str, max_size: int = 1600) -> str:
    """
    Кодирует изображение в base64.
    
    Args:
        image_path (str): Путь к файлу изображения
        max_size (int): Максимальный размер большей стороны в пикселях
        
    Returns:
        str: base64-encoded строка изображения
    """
    try:
        # Изменяем размер изображения перед кодированием
        resized_img = resize_image(image_path, max_size)
        
        # Сохраняем в буфер
        buffer = io.BytesIO()
        resized_img.save(buffer, format=resized_img.format or 'JPEG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.read()).decode('utf-8')
    except Exception as e:
        logging.error(f"Ошибка при кодировании изображения {image_path}: {str(e)}")
        raise

def describe_image(image_path: str, max_size: int = 1600) -> dict:
    """
    Получает описание изображения через Ollama API.
    
    Args:
        image_path (str): Путь к файлу изображения
        max_size (int): Максимальный размер большей стороны в пикселях
        
    Returns:
        dict: Словарь с описанием изображения и метаданными
    """
    # Проверяем, что файл существует и является изображением
    try:
        image = Image.open(image_path)
        image_info = {
            "format": image.format,
            "size": image.size,
            "mode": image.mode
        }
    except Exception as e:
        logging.error(f"Ошибка при открытии изображения {image_path}: {str(e)}")
        raise

    # Кодируем изображение в base64
    base64_image = encode_image_to_base64(image_path, max_size)
    
    # Формируем запрос к Ollama API
    url = "http://localhost:11434/api/generate"
    
    prompt = """Опиши подробно изображение, структурируя описание по следующим аспектам:
    1. Основные объекты и их расположение
    2. Цветовая гамма и освещение
    3. Композиция и перспектива
    4. Общее настроение и атмосфера
    5. Технические особенности (если заметны)
    
    Будь конкретным и информативным, это описание будет использоваться для поиска изображения."""
    
    payload = {
        "model": "llava",
        "prompt": prompt,
        "images": [base64_image],
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        description = response.json()["response"]
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "image_path": image_path,
            "image_info": image_info,
            "description": description,
            "model": "llava",
            "max_size": max_size
        }
        
        # Сохраняем результат в JSON файл в каталоге logs
        image_name = os.path.basename(image_path)
        output_file = os.path.join(LOGS_DIR, f"{os.path.splitext(image_name)[0]}_description.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Описание успешно сохранено в {output_file}")
        return result
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при запросе к Ollama API: {str(e)}")
        raise
    except KeyError:
        logging.error("Ошибка: неожиданный формат ответа от Ollama API")
        raise
    except Exception as e:
        logging.error(f"Неожиданная ошибка: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Генерация описания изображения с помощью Ollama.')
    parser.add_argument('image_path', help='Путь к изображению')
    parser.add_argument('--max-size', type=int, default=1600,
                      help='Максимальный размер большей стороны изображения в пикселях (по умолчанию: 1600)')
    args = parser.parse_args()

    try:
        result = describe_image(args.image_path, args.max_size)
        print("\nОписание изображения:")
        print("-" * 80)
        print(result["description"])
        print("-" * 80)
        print(f"\nМетаданные:")
        print(f"Формат: {result['image_info']['format']}")
        print(f"Размер: {result['image_info']['size']}")
        print(f"Цветовой режим: {result['image_info']['mode']}")
        print(f"Модель: {result['model']}")
        print(f"Максимальный размер: {result['max_size']}px")
        print(f"Время создания: {result['timestamp']}")
        
    except Exception as e:
        logging.error(f"Ошибка при обработке изображения: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 