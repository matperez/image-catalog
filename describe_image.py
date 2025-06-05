import requests
import base64
import sys
from PIL import Image
import io

def encode_image_to_base64(image_path: str) -> str:
    """
    Кодирует изображение в base64.
    
    Args:
        image_path (str): Путь к файлу изображения
        
    Returns:
        str: base64-encoded строка изображения
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_image_description(image_path: str) -> str:
    """
    Получает описание изображения через Ollama API.
    
    Args:
        image_path (str): Путь к файлу изображения
        
    Returns:
        str: Описание изображения
    """
    # Проверяем, что файл существует и является изображением
    try:
        Image.open(image_path)
    except Exception as e:
        return f"Ошибка при открытии изображения: {str(e)}"

    # Кодируем изображение в base64
    base64_image = encode_image_to_base64(image_path)
    
    # Формируем запрос к Ollama API
    url = "http://localhost:11434/api/generate"
    
    prompt = """Опиши подробно все что ты видишь на это изображении: 
    локация, предметы, объекты, персонажи и их действия, формат, тематику, 
    цвета - все что может помочь найти это изображение позже по описанию. 
    Не задавай дополнительных вопросов, просто опиши изображение."""
    
    payload = {
        "model": "gemma3",
        "prompt": prompt,
        "images": [base64_image],
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Проверяем на ошибки HTTP
        return response.json()["response"]
    except requests.exceptions.RequestException as e:
        return f"Ошибка при запросе к Ollama API: {str(e)}"
    except KeyError:
        return "Ошибка: неожиданный формат ответа от Ollama API"

def main():
    if len(sys.argv) != 2:
        print("Использование: python describe_image.py <путь_к_изображению>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    description = get_image_description(image_path)
    print(description)

if __name__ == "__main__":
    main() 