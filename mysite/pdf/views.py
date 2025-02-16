from django.shortcuts import render
from django.http import HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from io import BytesIO

def main(request):
    if request.method == 'POST':
        firstname = request.POST.get('firstname')
        secondaryname = request.POST.get('secondaryname')  # opcjonalne
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        degree = request.POST.getlist('degree')
        school = request.POST.getlist('school')
        university = request.POST.getlist('university')
        previous_work = request.POST.getlist('previous_work')
        
        # Nowe pole: Additional information
        info = request.POST.get('info', '')  # Może być puste

        # Obsługa uploadu obrazu
        image_file = request.FILES.get('image')
        image_path = None
        if image_file:
            image_path = default_storage.save(
                f"temp/{image_file.name}", 
                ContentFile(image_file.read())
            )

        # Tworzenie PDF (A4)
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Marginesy
        left_margin = 50
        top_margin = 50

        # Ustawiamy czcionkę bazową
        p.setFont("Helvetica", 12)

        # Rozmiary i pozycja zdjęcia (lewy górny róg)
        image_width = 120
        image_height = 120
        image_left = left_margin
        image_top = height - top_margin

        # Próba wstawienia obrazu
        if image_path:
            try:
                img = ImageReader(default_storage.open(image_path))
                p.drawImage(
                    img, 
                    image_left, 
                    image_top - image_height, 
                    width=image_width, 
                    height=image_height, 
                    preserveAspectRatio=True, 
                    mask='auto'
                )
            except:
                pass

        # Tekst obok zdjęcia
        text_x = image_left + image_width + 20
        text_y = image_top - 20

        # --- Imię, drugie imię, nazwisko ---
        p.setFont("Helvetica-Bold", 12)
        p.drawString(text_x, text_y, "Name:")
        p.setFont("Helvetica", 11)
        text_y -= 18
        p.drawString(text_x, text_y, f"First Name: {firstname}")
        text_y -= 15

        if secondaryname:
            p.drawString(text_x, text_y, f"Secondary Name: {secondaryname}")
            text_y -= 15

        p.drawString(text_x, text_y, f"Last Name: {lastname}")
        text_y -= 15

        # Pozioma linia poniżej zdjęcia
        line_y = image_top - image_height - 10
        p.setLineWidth(1)
        p.setStrokeColor(colors.grey)
        p.line(left_margin, line_y, width - left_margin, line_y)

        # Dalej umieszczamy resztę informacji poniżej tej linii
        y = line_y - 30

        # Funkcja do rysowania list wypunktowanych
        def draw_bulleted_list(canvas_obj, items, start_x, start_y):
            for item in items:
                item = item.strip()
                if item:
                    canvas_obj.drawString(start_x, start_y, u"\u2022 " + item)
                    start_y -= 15
            return start_y

        # Pomocnicza funkcja do rysowania nagłówka sekcji i poziomej linii
        def draw_section_header(canvas_obj, header_text, x, y):
            canvas_obj.setFont("Helvetica-Bold", 12)
            canvas_obj.drawString(x, y, header_text)
            canvas_obj.setFont("Helvetica", 11)
            return y - 20

        # 1) Email i telefon
        y = draw_section_header(p, "Contact Info:", left_margin, y)
        p.drawString(left_margin, y, f"Email: {email}")
        y -= 15
        p.drawString(left_margin, y, f"Phone: {phone}")
        y -= 25
        p.line(left_margin, y, width - left_margin, y)
        y -= 30

        # 2) Degrees
        if any(d.strip() for d in degree):
            y = draw_section_header(p, "Degrees:", left_margin, y)
            y = draw_bulleted_list(p, degree, left_margin + 15, y)
            y -= 10
            p.line(left_margin, y, width - left_margin, y)
            y -= 30

        # 3) Schools (wymagane)
        y = draw_section_header(p, "Schools:", left_margin, y)
        y = draw_bulleted_list(p, school, left_margin + 15, y)
        y -= 10
        p.line(left_margin, y, width - left_margin, y)
        y -= 30

        # 4) Universities
        if any(u.strip() for u in university):
            y = draw_section_header(p, "Universities:", left_margin, y)
            y = draw_bulleted_list(p, university, left_margin + 15, y)
            y -= 10
            p.line(left_margin, y, width - left_margin, y)
            y -= 30

        # 5) Previous Work
        if any(pw.strip() for pw in previous_work):
            y = draw_section_header(p, "Previous Work:", left_margin, y)
            y = draw_bulleted_list(p, previous_work, left_margin + 15, y)
            y -= 10
            p.line(left_margin, y, width - left_margin, y)
            y -= 30

        # 6) Additional Information (nowa sekcja na samym końcu)
        info = info.strip()
        if info:
            y = draw_section_header(p, "Additional Information:", left_margin, y)
            # Rozbijamy na linie i każdą rysujemy osobno
            for line in info.splitlines():
                line = line.strip()
                if line:
                    p.drawString(left_margin + 15, y, line)
                    y -= 15
            y -= 10
            p.line(left_margin, y, width - left_margin, y)
            y -= 30

        # Zakończenie strony
        p.showPage()
        p.save()
        buffer.seek(0)

        # Usuwamy tymczasowy plik obrazu po zakończeniu
        if image_path:
            default_storage.delete(image_path)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="CV.pdf"'
        return response

    return render(request, 'pdf/main.html')
