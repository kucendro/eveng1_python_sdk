"""
PowerPoint teleprompter example for G1 glasses
Displays speaker notes from active PowerPoint presentation
"""
import asyncio
import sys
from connector import G1Connector
from utils.logger import setup_logger

# Configuration
SEQUENCE_CHUNK_TIME = 3.0  # Time in seconds to display each chunk of text
MAX_CHARS_PER_CHUNK = 200  # Reduced from 150 to avoid display re-splitting

def split_into_chunks(text, max_chars):
    """Split text into chunks of maximum length while preserving words"""
    if not text:
        return []
    
    # Split into words
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        # Check if adding this word would exceed the limit
        word_length = len(word) + 1  # +1 for the space
        if current_length + word_length > max_chars and current_chunk:
            # Save current chunk and start a new one
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            # Add word to current chunk
            current_chunk.append(word)
            current_length += word_length
    
    # Add the last chunk if there is one
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

print("Script starting...")

async def main():
    """Run PowerPoint teleprompter"""
    logger = setup_logger()
    print("Logger setup complete")
    
    # Initialize G1 connection
    glasses = G1Connector()
    logger.info("Connecting to glasses...")
    await glasses.connect()
    logger.info("Connected to glasses!")
    
    try:
        print("Attempting win32com import...")
        import win32com.client
        print("win32com imported successfully")
        
        # Initialize PowerPoint
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        
        # Track current state
        current_slide = None
        current_notes = None
        
        while True:
            try:
                # Get current slide info
                if powerpoint.SlideShowWindows.Count > 0:
                    # Slideshow mode
                    slideshow = powerpoint.SlideShowWindows(1)
                    slide_number = slideshow.View.CurrentShowPosition
                    current_slide_obj = powerpoint.ActivePresentation.Slides(slide_number)
                else:
                    # Normal mode
                    slide = powerpoint.ActiveWindow.View.Slide
                    slide_number = slide.SlideNumber
                    current_slide_obj = slide
                
                # Only process if slide changed
                if slide_number != current_slide:
                    current_slide = slide_number
                    
                    # Get notes using the working method
                    notes_text = ""
                    if current_slide_obj.HasNotesPage:
                        notes_page = current_slide_obj.NotesPage
                        # Get text from all shapes in notes page
                        for shape in notes_page.Shapes:
                            if shape.HasTextFrame:
                                text = shape.TextFrame.TextRange.Text.strip()
                                # Filter out standalone slide numbers
                                if text and text != str(slide_number):
                                    notes_text += text + "\n"
                    
                    notes_text = notes_text.strip()
                    if notes_text and notes_text != current_notes:
                        current_notes = notes_text
                        print(f"\n=== Notes for Slide {slide_number} ===")
                        print(notes_text)
                        
                        # Split into sequence if needed
                        chunks = split_into_chunks(notes_text, MAX_CHARS_PER_CHUNK)
                        if len(chunks) > 1:
                            print(f"\nSplit into {len(chunks)} parts:")
                            for i, chunk in enumerate(chunks, 1):
                                print(f"\nPart {i}/{len(chunks)} ({SEQUENCE_CHUNK_TIME}s):")
                                print(chunk)
                                await glasses.display.display_text(chunk)
                                await asyncio.sleep(SEQUENCE_CHUNK_TIME)
                        else:
                            await glasses.display.display_text(notes_text)
                            
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                
            await asyncio.sleep(0.5)  # Check every 500ms
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Stopping monitor...")
        await glasses.display.show_exit_message()
        await glasses.disconnect()
        print("Monitor stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExited by user")
    except Exception as e:
        print(f"\nError: {e}") 