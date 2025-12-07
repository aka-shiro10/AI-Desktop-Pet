"""
Silence all annoying warnings from PyTorch, EasyOCR, etc.
Import this FIRST before anything else
"""

import os
import sys
import warnings as _warnings

# Suppress Python warnings
_warnings.filterwarnings("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

# Suppress PyTorch warnings
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'

# Suppress TensorFlow warnings (if used)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Suppress EasyOCR verbosity
os.environ['EASYOCR_MODULE'] = 'false'

# Nuclear option: Redirect stderr to devnull during imports
class SuppressStream:
    def __init__(self, stream=sys.stderr):
        self.stream = stream
        self.original_stderr = None
        
    def __enter__(self):
        self.original_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        return self
        
    def __exit__(self, *args):
        sys.stderr.close()
        sys.stderr = self.original_stderr

def silence_all():
    """Call this to silence everything"""
    import warnings
    warnings.filterwarnings("ignore")
    
    # Suppress specific PyTorch DataLoader warnings
    warnings.filterwarnings("ignore", message=".*pin_memory.*")
    warnings.filterwarnings("ignore", category=UserWarning, module="torch")
    
    try:
        import logging
        logging.getLogger('torch').setLevel(logging.ERROR)
        logging.getLogger('torch.utils.data').setLevel(logging.ERROR)
        logging.getLogger('py.warnings').setLevel(logging.ERROR)
    except:
        pass