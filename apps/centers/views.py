from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.types import OpenApiTypes
from .models import Center
from .serializers import CenterSerializer, CenterListSerializer


@extend_schema_view(
    get=extend_schema(
        operation_id='center_list',
        summary='List Centers',
        description='Get list of centers (admins: all, users: own center)',
        tags=['Centers'],
        responses={200: CenterListSerializer(many=True)}
    ),
    post=extend_schema(
        operation_id='center_create',
        summary='Create Center',
        description='Create new center (only for System Admin and Food Admin)',
        tags=['Centers'],
        request=CenterSerializer,
        responses={
            201: CenterSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'}
        }
    )
)
class CenterListCreateView(generics.ListCreateAPIView):
    queryset = Center.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CenterListSerializer
        return CenterSerializer

    def get_queryset(self):
        # Only admins can see centers, regular users cannot see any centers
        user = self.request.user
        if user.is_admin:
            return Center.objects.filter(is_active=True)
        return Center.objects.none()

    def perform_create(self, serializer):
        # Only System Admin can create centers
        user = self.request.user
        if user.role != 'sys_admin':
            raise PermissionDenied("Only System Admin can create centers.")
        serializer.save()


@extend_schema_view(
    get=extend_schema(
        operation_id='center_detail',
        summary='Get Center Details',
        description='Get details of a specific center',
        tags=['Centers'],
        responses={
            200: CenterSerializer,
            404: {'description': 'Center not found'}
        }
    ),
    put=extend_schema(
        operation_id='center_update',
        summary='Update Center',
        description='Update center completely (only for System Admin and Food Admin)',
        tags=['Centers'],
        request=CenterSerializer,
        responses={
            200: CenterSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Center not found'}
        }
    ),
    patch=extend_schema(
        operation_id='center_partial_update',
        summary='Partial Update Center',
        description='Partially update center (only for System Admin and Food Admin)',
        tags=['Centers'],
        request=CenterSerializer,
        responses={
            200: CenterSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Center not found'}
        }
    ),
    delete=extend_schema(
        operation_id='center_delete',
        summary='Delete Center',
        description='Delete center (only for System Admin and Food Admin)',
        tags=['Centers'],
        responses={
            204: {'description': 'Center deleted'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Center not found'}
        }
    )
)
class CenterDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Center.objects.filter(is_active=True)
    serializer_class = CenterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only admins can see centers, regular users cannot see any centers
        user = self.request.user
        if user.is_admin:
            return Center.objects.filter(is_active=True)
        return Center.objects.none()

    def perform_update(self, serializer):
        # Only System Admin can update centers
        user = self.request.user
        if user.role != 'sys_admin':
            raise PermissionDenied("Only System Admin can update centers.")
        serializer.save()

    def perform_destroy(self, instance):
        # Only System Admin can delete centers
        user = self.request.user
        if user.role != 'sys_admin':
            raise PermissionDenied("Only System Admin can delete centers.")
        instance.delete()


@extend_schema(
    operation_id='center_employees',
    summary='Get Center Employees',
    description='Get list of employees in a specific center',
    responses={
        200: OpenApiTypes.OBJECT,
        403: OpenApiTypes.OBJECT,
        404: OpenApiTypes.OBJECT
    },
    tags=['Centers']
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def center_employees(request, center_id):
    """Get employees of a specific center"""
    try:
        center = Center.objects.get(id=center_id, is_active=True)
        
        # Check if user has permission to view this center's employees
        user = request.user
        if not user.is_admin and not user.has_center(center):
            return Response({'error': 'Permission denied'}, status=403)
        
        employees = center.users.filter(is_active=True)
        from apps.accounts.serializers import UserSerializer
        serializer = UserSerializer(employees, many=True)
        return Response(serializer.data)
    except Center.DoesNotExist:
        return Response({'error': 'Center not found'}, status=404)


