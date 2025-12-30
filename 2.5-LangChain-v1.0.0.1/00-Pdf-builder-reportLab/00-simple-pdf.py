from reportlab.pdfgen import canvas

c = canvas.Canvas("testfile.pdf")

c.drawCentredString(100, 800, "Assalamualikum")

c.save()