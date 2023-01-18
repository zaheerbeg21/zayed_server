from django.contrib import admin
from django.urls import path, include
# from zayed_university_app import views
from zayed_university_app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("authentication.urls")),
    path("", include("report_app.urls")),
    path("chatbot/", include("zayed_university_app.urls")),
]
## file upload
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
