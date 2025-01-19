import io

import easyocr
from PIL import Image
from django.db.models import F
from django.shortcuts import render

from MedsRecognition.trade_mark_fetcher import TradeMarkFetcher
from MedsRecognition.decorators import supabase_login_required
from MedsRecognition.forms import ImageUploadForm
from MedsRecognition.active_ingredients_fetcher import ActiveIngredientsFetcher
from MedsRecognition.models import Medication


def extract_text_with_easyocr(image):
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    image_bytes = io.BytesIO()
    image.save(image_bytes, format="JPEG")
    image_bytes.seek(0)

    reader = easyocr.Reader(["en"], gpu=True)
    results = reader.readtext(image_bytes.read(), detail=0)
    return " ".join(results)


@supabase_login_required
def upload_image(request):
    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES["image"]
            image = Image.open(io.BytesIO(uploaded_file.read()))
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            extracted_text = extract_text_with_easyocr(image)
            active_ingredients = recognise(extracted_text)
            trade_mark = TradeMarkFetcher().get_trade_mark(extracted_text, active_ingredients)

            Medication.objects.create(
                profile=request.auth_user,
                active_ingredients=", ".join(active_ingredients),
                scanned_text=extracted_text,
                medication_name=trade_mark,
            )

            return render(
                request,
                "recognition/result.html",
                {
                    "text": extracted_text,
                    "active_ingredients": active_ingredients,
                    "trade_marks": trade_mark,
                },
            )
    else:
        form = ImageUploadForm()
    return render(request, "recognition/upload.html", {"form": form})


@supabase_login_required
def user_dashboard(request):
    medications = Medication.objects.filter(profile=request.auth_user).order_by(
        F("scan_date").desc()
    )
    return render(request, "recognition/dashboard.html", {"medications": medications})


def recognise(extracted_text):
    active_ingredients = ActiveIngredientsFetcher().find_active_ingredients(extracted_text)
    return list(dict.fromkeys(active_ingredients))


def index(request):
    return render(request, "recognition/index.html")
