def get_page_detail(
    former_list: list,
    page: int = None,
    page_size: int = None
) -> list:
    """
    Get certain items of former list
    
    Args:
        former_list (list): all items
        page (int, optional): page number. Defaults to None.
        page_size (int, optional): number of items in one page. Defaults to None.

    Raises:
        KeyError: if page_size is None and page is not None

    Returns:
        list: items selected by page and page_size.
    """
    if not page_size:
        # Format error
        if page:
            raise KeyError
        
        return former_list
    
    if not page:
        page = 0
    
    return former_list[page_size * page : page_size * (page + 1)]
    