"""
Example of sending text to G1 glasses
note: send multiple texts with short waits between them, the full text should display on the glasses for a period then switch to the next text.
avoid too long text and scrolling.


from the documentation:
urrently, the demo supports sending text directly to the glasses and displaying it. The core steps are as follows:

Divide the input text into lines according to the actual display width of the glasses (the value in the demo is 488, which can be fine-tuned) and the font size you want (the value in the demo is 21, which can be customized);
Combine the number of lines per screen (the value in the demo is 5) and the size limit of each ble packet to divide the text divided in step 1 into packets (5 lines are displayed per screen in the demo, the first three lines form one packet, and the last two lines form one packet);
Use the Text Sending protocol in the protocol section below to send the multi-packet data in step 2 to the glasses by screen (a timer is used in the demo to send each screen of text in sequence).

Text Sending
Command Information
Command: 0x4E
seq (Sequence Number): 0~255
total_package_num (Total Package Count): 1~255
current_package_num (Current Package Number): 0~255
newscreen (Screen Status)
Field Descriptions
seq (Sequence Number):

Range: 0~255
Description: Indicates the sequence of the current package.
total_package_num (Total Package Count):

Range: 1~255
Description: The total number of packages being sent in this transmission.
current_package_num (Current Package Number):

Range: 0~255
Description: The current package number within the total, starting from 0.
newscreen (Screen Status):

Composed of lower 4 bits and upper 4 bits to represent screen status and Even AI mode.
Lower 4 Bits (Screen Action):
0x01: Display new content
Upper 4 Bits (Status):
0x70: Text Show
Example:
New content + Text Show state is represented as 0x71.
new_char_pos0 and new_char_pos1:

new_char_pos0: Higher 8 bits of the new character position.
new_char_pos1: Lower 8 bits of the new character position.
current_page_num (Current Page Number):

Range: 0~255
Description: Represents the current page number.
max_page_num (Maximum Page Number):

Range: 1~255
Description: The total number of pages.
data (Data):

Description: The actual data being transmitted in this package.
"""

import asyncio
from g1sdk.connector import G1Connector
from g1sdk.services import DisplayService

async def main():
    """
    Demonstrates sending text to G1 glasses
    
    Protocol details:
    - Text is divided into lines based on display width (488 pixels)
    - Font size is configurable (default 21)
    - 5 lines displayed per screen
    - First 3 lines form one packet, last 2 lines form another packet
    - Uses command 0x4E for text transmission
    """
    glasses = G1Connector()
    await glasses.connect()
    
    display = DisplayService(glasses)
    text = "Hello from G1 SDK!\nThis is a multi-line\ntext demonstration."
    await display.send_text(text)

if __name__ == "__main__":
    asyncio.run(main())
