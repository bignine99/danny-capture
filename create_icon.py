from PIL import Image, ImageDraw

def create_crop_icon(filename="icon.ico"):
    # Dark modern background with rounded corners
    img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a rounded rectangle background
    bg_color = (30, 30, 35, 255)
    draw.rounded_rectangle([10, 10, 246, 246], radius=40, fill=bg_color)
    
    # Draw a vibrant cyan/neon blue viewfinder
    accent_color = (0, 255, 170, 255) # Neon Mint
    thick = 16
    length = 60
    margin = 50
    
    # Top-left
    draw.rectangle([margin, margin, margin + length, margin + thick], fill=accent_color)
    draw.rectangle([margin, margin, margin + thick, margin + length], fill=accent_color)
    
    # Top-right
    draw.rectangle([256 - margin - length, margin, 256 - margin, margin + thick], fill=accent_color)
    draw.rectangle([256 - margin - thick, margin, 256 - margin, margin + length], fill=accent_color)
    
    # Bottom-left
    draw.rectangle([margin, 256 - margin - thick, margin + length, 256 - margin], fill=accent_color)
    draw.rectangle([margin, 256 - margin - length, margin + thick, 256 - margin], fill=accent_color)
    
    # Bottom-right
    draw.rectangle([256 - margin - length, 256 - margin - thick, 256 - margin, 256 - margin], fill=accent_color)
    draw.rectangle([256 - margin - thick, 256 - margin - length, 256 - margin, 256 - margin], fill=accent_color)
    
    # Center targeting crosshair
    cx, cy = 128, 128
    draw.rectangle([cx - 20, cy - 4, cx + 20, cy + 4], fill=accent_color)
    draw.rectangle([cx - 4, cy - 20, cx + 4, cy + 20], fill=accent_color)
    
    img.save(filename, sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])

create_crop_icon("icon.ico")
