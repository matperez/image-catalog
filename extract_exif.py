from exif import Image
import json
from datetime import datetime
from typing import Dict, Any
import sys

def extract_exif_data(image_path: str) -> Dict[str, Any]:
    """
    Извлекает EXIF данные из изображения.
    
    Args:
        image_path (str): Путь к файлу изображения
        
    Returns:
        Dict[str, Any]: Словарь с EXIF данными
    """
    try:
        with open(image_path, 'rb') as image_file:
            image = Image(image_file)
            
        if not image.has_exif:
            return {"error": "Изображение не содержит EXIF данных"}
            
        exif_data = {}
        
        # Получаем все доступные EXIF теги
        for tag in dir(image):
            if not tag.startswith('_'):  # Пропускаем служебные атрибуты
                try:
                    value = getattr(image, tag)
                    # Пропускаем методы и другие несериализуемые объекты
                    if callable(value):
                        continue
                    # Преобразуем datetime в строку для сериализации
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    # Преобразуем bytes в строку
                    elif isinstance(value, bytes):
                        value = value.decode('utf-8', errors='replace')
                    # Преобразуем любые другие несериализуемые объекты в строку
                    try:
                        json.dumps(value)
                    except TypeError:
                        value = str(value)
                    exif_data[tag] = value
                except Exception as e:
                    exif_data[tag] = f"Ошибка чтения: {str(e)}"
                    
        return exif_data
        
    except Exception as e:
        return {"error": f"Ошибка при обработке файла: {str(e)}"}

def main():
    if len(sys.argv) != 2:
        print("Использование: python extract_exif.py <путь_к_изображению>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    exif_data = extract_exif_data(image_path)
    
    # Выводим данные в формате JSON с отступами
    print(json.dumps(exif_data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main() 