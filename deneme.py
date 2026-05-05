from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("helvetica", size=12)

# Test metnimiz: İçinde kalın (**) ve italik (_) kelimeler var.
test_text = "**Kalin** ve _Italik_ metin."

# Fonksiyonu dry_run=True ve markdown=True ile çağırıyoruz.
# Çıktı olarak satırları (LINES) istiyoruz.
result = pdf.multi_cell(w=0, h=10, text=test_text, markdown=True, dry_run=True, output="LINES")

print("\n--- TEST SONUCU ---")
print(f"Gelen Çıktı: {result}")

if "**Kalin**" in result[0] and "_Italik_" in result[0]:
    print("\nBAŞARILI: Markdown etiketleri korundu! 🚀")
else:
    print("\nHATA: Etiketler hala kayıp. ❌")
print("-------------------\n")