from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, MyTokenObtainPairView, RoomViewSet, PlayerViewSet, index, home, room_detail
from rest_framework_simplejwt.views import TokenRefreshView

main_router = DefaultRouter()
main_router.register(r'player', PlayerViewSet, r'player')
main_router.register(r'room', RoomViewSet, r'room')

urlpatterns = [
    path('api/', include(main_router.urls)),
    path('x/', index, name='index'),
    path('', home, name='home'),
    path('room/<str:room_id>/', room_detail, name='room_detail'),
    # path('game/<int:room_id>/', game_view, name='game_view'),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]


# creating room:
# http://127.0.0.1:8000/api/room/
# {
#     "player_id": "some-uuid-for-player",  # Optional
#     "player_name": "PlayerName",          # Optional
#     "name": "RoomName",
#     "capacity": 3
# }
#
# OR
#
# {
#     "name": "RoomName",
#     "capacity": 3
# }

# update room: : http://localhost:8000/api/room/{room_id}/
# method patch:
# {"name": "updated name", "capacity": "3"}

# delete room:
# method delete




#
# start_game:
# http://127.0.0.1:8000/api/room/57f454d7-7b5b-4943-b268-668809c78602/start_game/
#
# join:
# http://127.0.0.1:8000/api/room/57f454d7-7b5b-4943-b268-668809c78602/join/
# {
#     "player_id": "some-uuid-for-player",  # Optional
#     "player_name": "PlayerName",          # Optional
# }
