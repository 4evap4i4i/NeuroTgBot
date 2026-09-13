from .router_delete_chat import router_delete_chat
from .router_document import router_document
from .router_files import router_files
from .router_message import router_message
from .router_start import router_start

routers = [router_start, router_document, router_files, router_message, router_delete_chat]
