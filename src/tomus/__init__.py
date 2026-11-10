import os
import warnings

# Silenciar poluição de terminal do PyTorch e Docling ao carregar pesos de OCR.
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Silenciar avisos de tomusas externas antes de qualquer outro import do pacote.
warnings.filterwarnings("ignore", category=FutureWarning, module=r"google\..*")
warnings.filterwarnings("ignore", category=FutureWarning, module=r"fitz.*")
warnings.filterwarnings(
    "ignore", message=r".*urllib3 v2 only supports OpenSSL.*"
)
warnings.filterwarnings(
    "ignore", category=DeprecationWarning, message=r".*SwigPy.*|.*swigvarlink.*"
)
warnings.filterwarnings("ignore", message=r".*Redirects are currently not supported.*")
warnings.filterwarnings("ignore", category=UserWarning, module=r"torch\..*")

__version__ = "1.0.0"
