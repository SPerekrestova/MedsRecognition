import easyocr
import io
from PIL import Image
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from MedsRecognition.forms import ImageUploadForm
from MedsRecognition.meds_recognition import MedsRecognition

reader = easyocr.Reader(['en'], gpu=True)
meds_recognition = MedsRecognition()


def extract_text_with_easyocr(image):
    if image.mode in ('RGBA', 'P'):
        image = image.convert('RGB')

    image_bytes = io.BytesIO()
    image.save(image_bytes, format='JPEG')
    image_bytes.seek(0)

    results = reader.readtext(image_bytes.read(), detail=0)
    return " ".join(results)


@csrf_exempt # DEVELOPMENT ONLY 403 ERROR DISABLE
def upload_image(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['image']
            image = Image.open(io.BytesIO(uploaded_file.read()))
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            extracted_text = extract_text_with_easyocr(image)
            active_ingredients = recognise(extracted_text)

            return JsonResponse({
                'success': True,
                'text': extracted_text,
                'active_ingredients': active_ingredients
            })
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


def recognise(extracted_text):
    active_ingredients = meds_recognition.find_active_ingredients(extracted_text)
    return list(dict.fromkeys(active_ingredients))
