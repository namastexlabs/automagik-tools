"""
Google Docs Helper Functions

This module provides utility functions for common Google Docs operations
to simplify the implementation of document editing tools.
"""
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

def build_text_style(
    bold: bool = None,
    italic: bool = None,
    underline: bool = None,
    font_size: int = None,
    font_family: str = None
) -> tuple[Dict[str, Any], list[str]]:
    """
    Build text style object for Google Docs API requests.
    
    Args:
        bold: Whether text should be bold
        italic: Whether text should be italic
        underline: Whether text should be underlined
        font_size: Font size in points
        font_family: Font family name
    
    Returns:
        Tuple of (text_style_dict, list_of_field_names)
    """
    text_style = {}
    fields = []
    
    if bold is not None:
        text_style['bold'] = bold
        fields.append('bold')
    
    if italic is not None:
        text_style['italic'] = italic
        fields.append('italic')
    
    if underline is not None:
        text_style['underline'] = underline
        fields.append('underline')
    
    if font_size is not None:
        text_style['fontSize'] = {'magnitude': font_size, 'unit': 'PT'}
        fields.append('fontSize')
    
    if font_family is not None:
        text_style['weightedFontFamily'] = {'fontFamily': font_family}
        fields.append('weightedFontFamily')
    
    return text_style, fields

def create_insert_text_request(index: int, text: str) -> Dict[str, Any]:
    """
    Create an insertText request for Google Docs API.
    
    Args:
        index: Position to insert text
        text: Text to insert
    
    Returns:
        Dictionary representing the insertText request
    """
    return {
        'insertText': {
            'location': {'index': index},
            'text': text
        }
    }

def create_insert_text_segment_request(index: int, text: str, segment_id: str) -> Dict[str, Any]:
    """
    Create an insertText request for Google Docs API with segmentId (for headers/footers).
    
    Args:
        index: Position to insert text
        text: Text to insert
        segment_id: Segment ID (for targeting headers/footers)
    
    Returns:
        Dictionary representing the insertText request with segmentId
    """
    return {
        'insertText': {
            'location': {
                'segmentId': segment_id,
                'index': index
            },
            'text': text
        }
    }

def create_delete_range_request(start_index: int, end_index: int) -> Dict[str, Any]:
    """
    Create a deleteContentRange request for Google Docs API.
    
    Args:
        start_index: Start position of content to delete
        end_index: End position of content to delete
    
    Returns:
        Dictionary representing the deleteContentRange request
    """
    return {
        'deleteContentRange': {
            'range': {
                'startIndex': start_index,
                'endIndex': end_index
            }
        }
    }

def create_format_text_request(
    start_index: int, 
    end_index: int,
    bold: bool = None,
    italic: bool = None,
    underline: bool = None,
    font_size: int = None,
    font_family: str = None
) -> Optional[Dict[str, Any]]:
    """
    Create an updateTextStyle request for Google Docs API.
    
    Args:
        start_index: Start position of text to format
        end_index: End position of text to format
        bold: Whether text should be bold
        italic: Whether text should be italic
        underline: Whether text should be underlined
        font_size: Font size in points
        font_family: Font family name
    
    Returns:
        Dictionary representing the updateTextStyle request, or None if no styles provided
    """
    text_style, fields = build_text_style(bold, italic, underline, font_size, font_family)
    
    if not text_style:
        return None
    
    return {
        'updateTextStyle': {
            'range': {
                'startIndex': start_index,
                'endIndex': end_index
            },
            'textStyle': text_style,
            'fields': ','.join(fields)
        }
    }

def create_find_replace_request(
    find_text: str, 
    replace_text: str, 
    match_case: bool = False
) -> Dict[str, Any]:
    """
    Create a replaceAllText request for Google Docs API.
    
    Args:
        find_text: Text to find
        replace_text: Text to replace with
        match_case: Whether to match case exactly
    
    Returns:
        Dictionary representing the replaceAllText request
    """
    return {
        'replaceAllText': {
            'containsText': {
                'text': find_text,
                'matchCase': match_case
            },
            'replaceText': replace_text
        }
    }

def create_insert_table_request(index: int, rows: int, columns: int) -> Dict[str, Any]:
    """
    Create an insertTable request for Google Docs API.
    
    Args:
        index: Position to insert table
        rows: Number of rows
        columns: Number of columns
    
    Returns:
        Dictionary representing the insertTable request
    """
    return {
        'insertTable': {
            'location': {'index': index},
            'rows': rows,
            'columns': columns
        }
    }

def create_insert_page_break_request(index: int) -> Dict[str, Any]:
    """
    Create an insertPageBreak request for Google Docs API.
    
    Args:
        index: Position to insert page break
    
    Returns:
        Dictionary representing the insertPageBreak request
    """
    return {
        'insertPageBreak': {
            'location': {'index': index}
        }
    }

def create_insert_image_request(
    index: int, 
    image_uri: str,
    width: int = None,
    height: int = None
) -> Dict[str, Any]:
    """
    Create an insertInlineImage request for Google Docs API.
    
    Args:
        index: Position to insert image
        image_uri: URI of the image (Drive URL or public URL)
        width: Image width in points
        height: Image height in points
    
    Returns:
        Dictionary representing the insertInlineImage request
    """
    request = {
        'insertInlineImage': {
            'location': {'index': index},
            'uri': image_uri
        }
    }
    
    # Add size properties if specified
    object_size = {}
    if width is not None:
        object_size['width'] = {'magnitude': width, 'unit': 'PT'}
    if height is not None:
        object_size['height'] = {'magnitude': height, 'unit': 'PT'}
    
    if object_size:
        request['insertInlineImage']['objectSize'] = object_size
    
    return request

def create_bullet_list_request(
    start_index: int, 
    end_index: int,
    list_type: str = "UNORDERED"
) -> Dict[str, Any]:
    """
    Create a createParagraphBullets request for Google Docs API.
    
    Args:
        start_index: Start of text range to convert to list
        end_index: End of text range to convert to list
        list_type: Type of list ("UNORDERED" or "ORDERED")
    
    Returns:
        Dictionary representing the createParagraphBullets request
    """
    bullet_preset = (
        'BULLET_DISC_CIRCLE_SQUARE' 
        if list_type == "UNORDERED" 
        else 'NUMBERED_DECIMAL_ALPHA_ROMAN'
    )
    
    return {
        'createParagraphBullets': {
            'range': {
                'startIndex': start_index,
                'endIndex': end_index
            },
            'bulletPreset': bullet_preset
        }
    }

def validate_operation(operation: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a batch operation dictionary.
    
    Args:
        operation: Operation dictionary to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    op_type = operation.get('type')
    if not op_type:
        return False, "Missing 'type' field"
    
    # Validate required fields for each operation type
    required_fields = {
        'insert_text': ['index', 'text'],
        'delete_text': ['start_index', 'end_index'],
        'replace_text': ['start_index', 'end_index', 'text'],
        'format_text': ['start_index', 'end_index'],
        'insert_table': ['index', 'rows', 'columns'],
        'insert_page_break': ['index'],
        'find_replace': ['find_text', 'replace_text']
    }
    
    if op_type not in required_fields:
        return False, f"Unsupported operation type: {op_type or 'None'}"
    
    for field in required_fields[op_type]:
        if field not in operation:
            return False, f"Missing required field: {field}"
    
    return True, ""

