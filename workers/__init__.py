# Worker package initialization 

# Import all worker modules to ensure they're available
from . import svg_tasks
from . import main

# Explicit module exports for RQ to find
__all__ = ['svg_tasks', 'main'] 