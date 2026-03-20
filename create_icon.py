from PIL import Image, ImageDraw

def create_lightning_icon():
    # Create a 256x256 image with transparent background
    img = Image.new('RGBA', (256, 256), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Points for a classic lightning bolt
    polygon = [
        (140, 20),
        (60, 140),
        (120, 140),
        (90, 240),
        (200, 100),
        (140, 100)
    ]
    
    # Draw polygon (Golden Yellow)
    draw.polygon(polygon, fill='#FFD700')
    
    # Add a slight outline for better visibility on light backgrounds
    draw.line(polygon + [polygon[0]], fill='#DAA520', width=6, joint='curve')
    
    # Save as ICO with multiple sizes for Windows
    img.save('icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])

if __name__ == '__main__':
    create_lightning_icon()
    print("icon.ico created.")
