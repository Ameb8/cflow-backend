from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'exec/<int:project_id>/$', consumers.ChatConsumer.as_asgi())
]