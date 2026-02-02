import cv2
import numpy as np
import os
import textwrap  # NEW LIBRARY: Helps us wrap text
from PIL import Image, ImageDraw, ImageFont

# --- 1. ANALYSIS LOGIC (Kept same as before) ---
def analyze_handwriting_style(image_path):
    try:
        img = cv2.imread(image_path, 0)
        if img is None: return "standard"
        thickness_score = np.mean(255 - img) 
        if thickness_score > 30: return "thick"
        elif thickness_score < 10: return "thin"
        else: return "standard"
    except:
        return "standard"

# --- 2. NEW HELPER: Handles Text Wrapping ---
def draw_text_with_wrapping(draw, text, font, max_width, start_x, start_y, line_spacing=10):
    lines = []
    # Break text into paragraphs first (handling newlines in input)
    paragraphs = text.split('\n')
    
    for paragraph in paragraphs:
        # Wrap each paragraph to fit the width
        # 'width=50' is an estimate; we calculate real pixel width below
        wrapped_lines = textwrap.wrap(paragraph, width=60) 
        lines.extend(wrapped_lines)
    
    y = start_y
    for line in lines:
        # Draw the line
        draw.text((start_x, y), line, font=font, fill="black")
        
        # Move down for the next line
        # parsing the font size properly to calculate height
        bbox = font.getbbox(line)
        line_height = bbox[3] - bbox[1] 
        y += line_height + line_spacing

    return y  # Return the final Y position if we need it

# --- 3. GENERATION LOGIC ---
def generate_handwritten_image(text_content, user_sample_path=None):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base_dir, "static", "fonts")
    output_path = os.path.join(base_dir, "static", "handwritten_output.png")
    
    # 1. Select Font
    selected_font_file = "handwriting.ttf"
    if user_sample_path and os.path.exists(user_sample_path):
        detected_style = analyze_handwriting_style(user_sample_path)
        if detected_style == "thick": selected_font_file = "thick_marker.ttf"
        elif detected_style == "thin": selected_font_file = "thin_cursive.ttf"
            
    font_path = os.path.join(fonts_dir, selected_font_file)
    if not os.path.exists(font_path):
        font_path = os.path.join(fonts_dir, "handwriting.ttf")

    # 2. Setup Image (Increased Height to fit long text)
    # Changed height from 600 to 1200 to accommodate your long lecture text
    image = Image.new("RGB", (800, 1500), "white") 
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype(font_path, size=24)
        
        # 3. Draw with Wrapping
        # x=50, y=50 is the starting margin
        # max_width=700 (800px total width - 100px margins)
        draw_text_with_wrapping(draw, text_content, font, max_width=700, start_x=50, start_y=50)
        
    except Exception as e:
        return f"Error: {e}"

    image.save(output_path)
    return output_path

if __name__ == "__main__":
    # Test with your long text
    long_text = """This is wrong civilization; produce your own food... (paste your full text here to test)"""
    print(generate_handwritten_image(long_text))