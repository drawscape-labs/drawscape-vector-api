# Worker package initialization 

# Import all worker modules to ensure they're available
from . import svg_tasks

# Explicit module exports for RQ to find
__all__ = ['svg_tasks'] 