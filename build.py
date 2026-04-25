import os
import re
import subprocess
from PIL import Image, ImageDraw, ImageFont

VERSION_FILE = os.path.join('src', 'version.py')

def get_next_version():
    current_version = "2.0.0"
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r') as f:
            content = f.read()
            match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
            if match:
                current_version = match.group(1)
    
    # Increment patch version
    parts = current_version.split('.')
    if len(parts) == 3:
        parts[2] = str(int(parts[2]) + 1)
        new_version = ".".join(parts)
    else:
        new_version = current_version + ".1"
        
    with open(VERSION_FILE, 'w') as f:
        f.write(f'__version__ = "{new_version}"\n')
        
    return new_version

def create_splash(version):
    bg_color = (15, 23, 42) # #0f172a
    img = Image.new('RGB', (600, 400), bg_color)
    draw = ImageDraw.Draw(img)

    # Try to paste logo
    try:
        logo = Image.open(os.path.join('assets', 'icons', 'logo.png')).convert('RGBA')
        logo = logo.resize((150, 150))
        x = (600 - 150) // 2
        y = (400 - 150) // 2 - 40
        img.paste(logo, (x, y), logo)
    except Exception as e:
        print('Could not load logo:', e)

    # Add text "AutoBillr"
    text = 'AutoBillr'
    try:
        font = ImageFont.truetype('arial.ttf', 42)
    except:
        font = ImageFont.load_default()

    bbox = font.getbbox(text) if hasattr(font, 'getbbox') else None
    text_width = bbox[2] - bbox[0] if bbox else len(text) * 20

    x = (600 - text_width) // 2
    y = 260
    draw.text((x, y), text, fill=(248, 250, 252), font=font)

    # Add version text
    version_text = f'Version {version}'
    try:
        small_font = ImageFont.truetype('arial.ttf', 16)
    except:
        small_font = ImageFont.load_default()

    bbox = small_font.getbbox(version_text) if hasattr(small_font, 'getbbox') else None
    vw = bbox[2] - bbox[0] if bbox else len(version_text) * 8
    x = (600 - vw) // 2
    y = 320
    draw.text((x, y), version_text, fill=(148, 163, 184), font=small_font)

    # Add creator text
    creator_text = 'Created by R.Thigan'
    bbox = small_font.getbbox(creator_text) if hasattr(small_font, 'getbbox') else None
    cw = bbox[2] - bbox[0] if bbox else len(creator_text) * 8
    x = (600 - cw) // 2
    y = 350
    draw.text((x, y), creator_text, fill=(99, 102, 241), font=small_font)

    splash_path = os.path.join('assets', 'icons', 'splash.png')
    img.save(splash_path)
    print(f'Splash generated for version {version} at {splash_path}')

if __name__ == '__main__':
    version = get_next_version()
    create_splash(version)
    print("Building application with PyInstaller...")
    subprocess.run(['pyinstaller', '--noconfirm', 'AutoBillr.spec'])
    print(f"\n==========================================")
    print(f"Build complete for AutoBillr Version {version}!")
    print(f"==========================================")
