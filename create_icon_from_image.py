"""
Скрипт для создания иконки приложения из изображения.
Конвертирует PNG/JPG изображение в ICO формат с несколькими размерами.
"""
from PIL import Image
import os
import sys

# Настройка кодировки для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def create_icon_from_image(input_path: str, output_path: str = "app.ico"):
    """
    Создает ICO файл из изображения с несколькими размерами.
    
    Args:
        input_path: Путь к исходному изображению (PNG, JPG, etc.)
        output_path: Путь для сохранения ICO файла (по умолчанию app.ico)
    """
    if not os.path.exists(input_path):
        print(f"[ERROR] File not found: '{input_path}'")
        return False
    
    try:
        # Открываем исходное изображение
        img = Image.open(input_path)
        print(f"[OK] Image loaded: {img.size[0]}x{img.size[1]}, mode: {img.mode}")
        
        # Конвертируем в RGB если нужно (ICO требует RGB или RGBA)
        if img.mode not in ('RGB', 'RGBA'):
            print(f"   Converting from {img.mode} to RGB...")
            if img.mode == 'P':  # Палитра
                img = img.convert('RGBA')
            else:
                img = img.convert('RGB')
        
        # Размеры для иконки (Windows поддерживает множественные размеры в одном ICO)
        sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
        
        # Создаем изображения разных размеров
        icons = []
        for size in sizes:
            resized = img.resize(size, Image.Resampling.LANCZOS)
            # Если исходное изображение RGBA, сохраняем RGBA, иначе RGB
            if resized.mode == 'RGBA':
                icons.append(resized)
            else:
                icons.append(resized)
        
        # Сохраняем как ICO с несколькими размерами
        icons[0].save(
            output_path,
            format='ICO',
            sizes=sizes,
            append_images=icons[1:] if len(icons) > 1 else None
        )
        
        print(f"[OK] Icon successfully created: '{output_path}'")
        print(f"   Sizes: {', '.join([f'{w}x{h}' for w, h in sizes])}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error creating icon: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Главная функция."""
    if len(sys.argv) < 2:
        print("Usage: python create_icon_from_image.py <image_path> [output.ico]")
        print("\nExamples:")
        print("  python create_icon_from_image.py icon.png")
        print("  python create_icon_from_image.py icon.png app.ico")
        print("\nSupported formats: PNG, JPG, JPEG, BMP, and other formats supported by PIL")
        return
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "app.ico"
    
    create_icon_from_image(input_path, output_path)


if __name__ == "__main__":
    main()

