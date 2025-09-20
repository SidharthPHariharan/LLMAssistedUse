#!/usr/bin/env python3
"""
FastMCP PyAutoGUI Desktop Automation Server

This server provides desktop automation capabilities using PyAutoGUI through the MCP protocol.
It allows AI assistants to control mouse, keyboard, and screen operations.
"""

import pyautogui
import time
import io
import base64
from typing import Optional, Tuple, List
from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("PyAutoGUI Desktop Controller")

# Configure PyAutoGUI safety settings
pyautogui.PAUSE = 0.1  # Small pause between actions for safety
pyautogui.FAILSAFE = False #True  # Move mouse to corner to abort
@mcp.tool()
def take_screenshot(region: Optional[Tuple[int, int, int, int]] = None) -> str:
    """
    Take a screenshot of the desktop or a specific region.
    
    Args:
        region: Optional tuple (left, top, width, height) for partial screenshot
    
    Returns:
        Base64 encoded PNG image of the screenshot
    """
    try:
        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()
        
        # Convert to base64
        buffer = io.BytesIO()
        screenshot.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"Screenshot captured successfully. Base64 data: data:image/png;base64,{img_str[:100]}..."
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"

@mcp.tool()
def click_at(x: int, y: int, button: str = "left", clicks: int = 1) -> str:
    """
    Click at specific coordinates on the screen.
    
    Args:
        x: X coordinate
        y: Y coordinate
        button: Mouse button ('left', 'right', 'middle')
        clicks: Number of clicks (1 for single, 2 for double)
    
    Returns:
        Success message or error
    """
    try:
        pyautogui.click(x, y, clicks=clicks, button=button)
        return f"Clicked at ({x}, {y}) with {button} button, {clicks} times"
    except Exception as e:
        return f"Error clicking: {str(e)}"

@mcp.tool()
def move_mouse(x: int, y: int, duration: float = 0.25) -> str:
    """
    Move mouse to specific coordinates.
    
    Args:
        x: X coordinate
        y: Y coordinate
        duration: Time in seconds to complete the movement
    
    Returns:
        Success message or error
    """
    try:
        pyautogui.moveTo(x, y, duration=duration)
        return f"Mouse moved to ({x}, {y})"
    except Exception as e:
        return f"Error moving mouse: {str(e)}"

@mcp.tool()
def drag_mouse(start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.25) -> str:
    """
    Drag mouse from start coordinates to end coordinates.
    
    Args:
        start_x: Starting X coordinate
        start_y: Starting Y coordinate
        end_x: Ending X coordinate
        end_y: Ending Y coordinate
        duration: Time in seconds to complete the drag
    
    Returns:
        Success message or error
    """
    try:
        pyautogui.dragTo(end_x, end_y, duration=duration, button='left')
        return f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})"
    except Exception as e:
        return f"Error dragging: {str(e)}"

@mcp.tool()
def type_text(text: str) -> str:
    """
    Type text at the current cursor position.
    
    Args:
        text: Text to type
    
    Returns:
        Success message or error
    """
    try:
        pyautogui.typewrite(text, interval=0.01)
        return f"Typed text: '{text}'"
    except Exception as e:
        return f"Error typing: {str(e)}"

@mcp.tool()
def press_key(key: str, presses: int = 1) -> str:
    """
    Press a specific key or key combination.
    
    Args:
        key: Key to press (e.g., 'enter', 'ctrl+c', 'alt+tab')
        presses: Number of times to press the key
    
    Returns:
        Success message or error
    """
    try:
        if '+' in key:
            # Handle key combinations
            keys = key.split('+')
            pyautogui.hotkey(*keys)
            return f"Pressed key combination: {key}"
        else:
            # Handle single key
            for _ in range(presses):
                pyautogui.press(key)
            return f"Pressed '{key}' {presses} times"
    except Exception as e:
        return f"Error pressing key: {str(e)}"

@mcp.tool()
def scroll(clicks: int, direction: str = "down") -> str:
    """
    Scroll the mouse wheel.
    
    Args:
        clicks: Number of scroll clicks
        direction: Direction to scroll ('up' or 'down')
    
    Returns:
        Success message or error
    """
    try:
        scroll_amount = clicks if direction == "up" else -clicks
        pyautogui.scroll(scroll_amount)
        return f"Scrolled {direction} {clicks} clicks"
    except Exception as e:
        return f"Error scrolling: {str(e)}"

@mcp.tool()
def get_screen_size() -> str:
    """
    Get the current screen resolution.
    
    Returns:
        Screen size as string
    """
    try:
        size = pyautogui.size()
        return f"Screen size: {size.width}x{size.height}"
    except Exception as e:
        return f"Error getting screen size: {str(e)}"

@mcp.tool()
def find_on_screen(image_path: str, confidence: float = 0.8) -> str:
    """
    Find an image on the screen and return its location.
    
    Args:
        image_path: Path to the image file to search for
        confidence: Confidence level for image matching (0.0 to 1.0)
    
    Returns:
        Location of the image or error message
    """
    try:
        location = pyautogui.locateOnScreen(image_path, confidence=confidence)
        if location:
            center = pyautogui.center(location)
            return f"Image found at: ({center.x}, {center.y})"
        else:
            return "Image not found on screen"
    except Exception as e:
        return f"Error finding image: {str(e)}"

@mcp.tool()
def get_mouse_position() -> str:
    """
    Get the current mouse position.
    
    Returns:
        Current mouse coordinates
    """
    try:
        pos = pyautogui.position()
        return f"Mouse position: ({pos.x}, {pos.y})"
    except Exception as e:
        return f"Error getting mouse position: {str(e)}"

@mcp.tool()
def wait(seconds: float) -> str:
    """
    Wait for a specified number of seconds.
    
    Args:
        seconds: Number of seconds to wait
    
    Returns:
        Success message
    """
    try:
        time.sleep(seconds)
        return f"Waited {seconds} seconds"
    except Exception as e:
        return f"Error waiting: {str(e)}"

if __name__ == "__main__":
    # Run the MCP server
    # mcp.run()
    # mcp.run(transport="http", port=8000)
    mcp.run(transport="stdio")

# def __init__(self):
#     mcp.run(transport='stdio')