import warnings

# Silenciar avisos de bibliotecas externas antes de qualquer outro import do pacote.
warnings.filterwarnings("ignore", category=FutureWarning, module=r"google\..*")
warnings.filterwarnings("ignore", category=FutureWarning, module=r"fitz.*")
warnings.filterwarnings(
    "ignore", message=r".*urllib3 v2 only supports OpenSSL.*"
)
warnings.filterwarnings(
    "ignore", category=DeprecationWarning, message=r".*SwigPy.*|.*swigvarlink.*"
)

__version__ = "0.0.2"
