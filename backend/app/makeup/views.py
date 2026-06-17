import os
import tempfile

from django.conf import settings
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status


@api_view(['POST'])
@parser_classes([MultiPartParser])
def simulate_makeup(request):
    face_image = request.FILES.get('face_image')
    if not face_image:
        return Response({'error': 'face_image 필드가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

    suffix = os.path.splitext(face_image.name)[1] or '.png'
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        for chunk in face_image.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        from .services import run_makeup
        output_dir = os.path.join(settings.MEDIA_ROOT, 'simulations')
        gan_results = run_makeup(tmp_path, output_dir)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    results = []
    for i, item in enumerate(gan_results):
        rel = os.path.relpath(item['image_path'], settings.MEDIA_ROOT).replace('\\', '/')
        url = request.build_absolute_uri(settings.MEDIA_URL + rel)
        results.append({'id': f'm{i + 1}', 'image': url, 'name': item['name']})

    return Response({'results': results})
