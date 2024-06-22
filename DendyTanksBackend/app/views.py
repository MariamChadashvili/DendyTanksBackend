import uuid
from django.shortcuts import render, redirect
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Player, Room
from .serializers import RegisterSerializer, MyTokenObtainPairSerializer, PlayerSerializer, RoomSerializer, RoomCreateSerializer
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView


class RegisterView(generics.CreateAPIView):
    queryset = Player.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            player = serializer.save()
            return Response({
                "user": RegisterSerializer(player, context=self.get_serializer_context()).data,
                "message": "User created successfully!"
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return RoomCreateSerializer
        return RoomSerializer

    def create(self, request, *args, **kwargs):
        player = request.user
        if not player.is_authenticated:
            return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        room_capacity = request.data.get('capacity', None)
        if room_capacity not in [2, 3, 4]:
            room_capacity = 2

        room_data = {
            'player_id': player.id,
            'player_name': player.name,
            'name': request.data.get('name'),
            'capacity': room_capacity,
        }

        room_serializer = self.get_serializer(data=room_data)
        room_serializer.is_valid(raise_exception=True)
        room = room_serializer.save(created_by=player)
        room.add_player(player)

        return Response(RoomSerializer(room).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        room = self.get_object()
        if room.created_by != request.user:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        room_data = {}
        room_capacity = request.data.get('capacity', None)
        if room_capacity:
            if room_capacity in [2, 3, 4]:
                room_data['capacity'] = room_capacity

        room_name = request.data.get('name', None)
        if room_name:
            room_data['name'] = room_name

        room_serializer = self.get_serializer(room, data=room_data, partial=True)
        room_serializer.is_valid(raise_exception=True)
        room = room_serializer.save()

        return Response(RoomSerializer(room).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        room = self.get_object()
        if room.created_by != request.user:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        room.delete()
        return Response({'detail': 'Deleted successfully'}, status=status.HTTP_200_OK)

    # def update(self, request, *args, **kwargs):
    #     room_data = {}
    #     room_capacity = request.data.get('capacity', None)
    #     if room_capacity:
    #         if room_capacity in [2, 3, 4]:
    #             room_data['capacity'] = room_capacity
    #
    #     room_name = request.data.get('name', None)
    #     if room_name:
    #         room_data['name'] = room_name
    #
    #     room = self.get_object()
    #     room_serializer = self.get_serializer(room, data=room_data, partial=True)
    #     room_serializer.is_valid(raise_exception=True)
    #     room = room_serializer.save()
    #
    #     return Response(RoomSerializer(room).data, status=status.HTTP_200_OK)



    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        room = self.get_object()
        if room.status != 'waiting':
            return Response({'detail': 'Room is full. Cannot join.'}, status=status.HTTP_400_BAD_REQUEST)

        player_id = request.data.get('player_id', None)
        player_name = request.data.get('player_name', f'Player-{uuid.uuid4()}')
        player, created = Player.objects.get_or_create(id=player_id, defaults={'name': player_name})
        print("joined-------------", player.id, "-----", player_name)

        try:
            room.add_player(player)
            # return Response(PlayerSerializer(player).data, status=status.HTTP_200_OK)
            print("room_id----------", room.id)
            # return redirect(f'/room/{room.id}/')
            return Response({'redirect_url': f'/room/{room.id}/'}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        room = self.get_object()
        player_id = request.data.get('player_id', None)

        if not player_id:
            return Response({'detail': 'Player ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            player = Player.objects.get(id=player_id)
            room.remove_player(player)  # Assuming you have a method to remove a player from a room
            return Response({'detail': 'Player removed from room.'}, status=status.HTTP_200_OK)
        except Player.DoesNotExist:
            return Response({'detail': 'Player not found.'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def start_game(self, request, pk=None):
        room = self.get_object()
        if room.status == 'full':
            room.status = 'game started'
            room.save()
            # Notify players via WebSockets or any other mechanism
            return Response({'detail': 'Game started!'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Room is not full yet.'}, status=status.HTTP_400_BAD_REQUEST)


def index(request):
    return render(request, 'app/index.html')

# def game_view(request, room_id):
#     room = get_object_or_404(Room, id=room_id)
#     players = room.players.all()
#     return render(request, 'app/index.html', {'room_id': room_id, 'players':players})


def home(request):
    rooms = Room.objects.all()
    serializer = RoomSerializer(rooms, many=True)
    # return JsonResponse(serializer.data, safe=False)
    return render(request, 'app/home.html')


def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    return render(request, 'app/room_detail.html', {'room': room})
