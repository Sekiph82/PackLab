"""Small dict-based English/Turkish UI translation (PL-0464).

English source text is the key. Technical audit identifiers (status codes such as
DEFERRED_OWNER_VALIDATION, units such as mm_unverified) stay verbatim inside the Turkish
strings, followed by a plain-language explanation. Language is chosen once at startup.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractButton,
    QComboBox,
    QDockWidget,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMenu,
    QWidget,
)

LANGUAGES = {"en": "English", "tr": "Türkçe"}
SETTINGS_KEY = "ui/language"
_current = "en"


def set_language(code: object) -> str:
    global _current
    _current = str(code) if str(code) in LANGUAGES else "en"
    return _current


def language() -> str:
    return _current


def tr(text: str) -> str:
    """Translate an English UI string; unknown strings stay as they are."""
    if _current == "tr":
        return TURKISH.get(text, text)
    return text


def translate_widget_tree(root: QWidget) -> None:
    """Translate static texts of an already-built widget tree in place (Turkish only)."""
    if _current == "en":
        return
    for button in root.findChildren(QAbstractButton):
        button.setText(tr(button.text()))
    for label in root.findChildren(QLabel):
        label.setText(tr(label.text()))
    for group in root.findChildren(QGroupBox):
        group.setTitle(tr(group.title()))
    for line in root.findChildren(QLineEdit):
        line.setPlaceholderText(tr(line.placeholderText()))
    for combo in root.findChildren(QComboBox):
        for index in range(combo.count()):  # item data (the logic key) is unchanged
            combo.setItemText(index, tr(combo.itemText(index)))
    for dock in root.findChildren(QDockWidget):
        dock.setWindowTitle(tr(dock.windowTitle()))
    for menu in root.findChildren(QMenu):
        menu.setTitle(tr(menu.title()))
        for action in menu.actions():
            action.setText(tr(action.text()))


_SCALE_NOTE = "mm_unverified = milimetre, henüz fiziksel olarak doğrulanmadı"
_DEFERRED = "DEFERRED_OWNER_VALIDATION = sahip doğrulaması bekleniyor"

TURKISH: dict[str, str] = {
    # Navigation and page headers
    "Packaging Library": "Ambalaj Kütüphanesi",
    "Browse, search and manage your saved packaging designs (SKUs).": (
        "Kayıtlı ambalaj tasarımlarınıza (SKU = stok kodu) göz atın, arayın ve yönetin."
    ),
    "Capture Inbox": "Tarama Gelen Kutusu",
    "Receive scans from the iPhone or import a .packscan file.": (
        "iPhone'dan gelen taramaları alın veya bir .packscan dosyası içe aktarın."
    ),
    "Build 3D Model": "3B Model Oluştur",
    "Turn the photos of an imported scan into a 3D model (COLMAP / OpenMVS).": (
        "İçe aktarılan taramanın fotoğraflarından 3B model oluşturun (COLMAP / OpenMVS)."
    ),
    "Scan Master": "Scan Master (ölçülmüş tarama)",
    "Promote a cleaned scan to Scan Master, the measured reference copy of the real object.": (
        "Temizlenmiş taramayı Scan Master'a yükseltin: gerçek nesnenin ölçülmüş referans kopyası."
    ),
    "Mask Correction": "Maske Düzeltme",
    "Fix the object outline in a photo by painting or erasing pixels.": (
        "Fotoğraftaki nesne sınırını pikselleri boyayarak veya silerek düzeltin."
    ),
    "Exports": "Dışa Aktarım",
    "Save the Scan Master or Design Model as engineering files.": (
        "Scan Master'ı veya Tasarım Modelini (Design Model) mühendislik dosyası olarak kaydedin."
    ),
    "Settings": "Ayarlar",
    "Language, automatic model building, reconstruction engines and version details.": (
        "Dil, otomatik model oluşturma, 3B yeniden yapılandırma motorları ve sürüm bilgisi."
    ),
    "Model Viewer": "Model Görüntüleyici",
    "Look at a built 3D model: drag to rotate, right-drag to pan, wheel to zoom.": (
        "Oluşturulan 3B modeli inceleyin: döndürmek için sürükleyin, kaydırmak için sağ "
        "tuşla sürükleyin, yakınlaştırmak için tekerleği kullanın."
    ),
    "Measure & Design": "Ölç ve Tasarla",
    "Isolate the object, set real-world scale, measure it and create a Design Model.": (
        "Nesneyi ayırın, gerçek ölçeği ayarlayın, ölçün ve Tasarım Modeli (Design Model) oluşturun."
    ),
    "Labels": "Etiketler",
    "Place label zones and artwork on the Design Model and render mockups.": (
        "Tasarım Modeli üzerine etiket alanları ve baskı görselleri yerleştirin, "
        "önizleme oluşturun."
    ),
    "Package Families": "Ambalaj Aileleri",
    "Create size and closure variants from parametric package family templates.": (
        "Parametrik ambalaj ailesi şablonlarından boyut ve kapak varyantları oluşturun."
    ),
    # Menus, docks, window
    "&File": "&Dosya",
    "&Edit": "Dü&zen",
    "&View": "&Görünüm",
    "&Help": "&Yardım",
    "&New Project…": "&Yeni Proje…",
    "&Open Project…": "Proje &Aç…",
    "Open &Recent": "&Son Açılanlar",
    "&Close Project": "Projeyi &Kapat",
    "&Portability report…": "&Taşınabilirlik raporu…",
    "E&xit": "Çı&kış",
    "&Undo selection": "Seçimi &geri al",
    "&Redo selection": "Seçimi &yinele",
    "Create &diagnostic bundle": "&Tanılama paketi oluştur",
    "&Language": "&Dil",
    "Scene / Objects": "Sahne / Nesneler",
    "Properties / Inspector": "Özellikler / Denetçi",
    "Jobs / Activity": "İşler / Etkinlik",
    "Jobs (idle)": "İşler (boşta)",
    "Jobs ({count} running)": "İşler ({count} çalışıyor)",
    "Logs": "Günlükler",
    "Language": "Dil",
    "Language changes apply after restarting PackLab Studio.": (
        "Dil değişikliği PackLab Studio yeniden başlatıldığında uygulanır."
    ),
    # Capture Inbox
    "Receive scans": "Tarama al",
    "Receiving…": "Alınıyor…",
    "Receiving on {address} — scan the QR code in the iPhone app.": (
        "{address} üzerinden alınıyor — iPhone uygulamasında QR kodunu okutun."
    ),
    "If Windows asks, allow PackLab on private networks.": (
        "Windows sorarsa PackLab'e özel ağlarda izin verin."
    ),
    "Not receiving.": "Alım kapalı.",
    "Receiver stopped.": "Alıcı durduruldu.",
    "Pairing code: {code}": "Eşleştirme kodu: {code}",
    "Address: {address}": "Adres: {address}",
    "The code refreshes automatically.": "Kod otomatik olarak yenilenir.",
    "paired {when}": "eşleşme {when}",
    "last seen {when}": "son görülme {when}",
    "never": "hiç",
    "Scan from {model}": "{model} taraması",
    "Scan": "Tarama",
    "Photos: {count}": "Fotoğraf: {count}",
    "iPhone Wi-Fi": "iPhone Wi-Fi",
    "File": "Dosya",
    "Start receiving and select a paired phone to control its capture.": (
        "Telefonun çekimini yönetmek için alımı başlatın ve eşleşmiş bir telefon seçin."
    ),
    "Phone not connected. On the iPhone start a scan and turn on Allow PackLab to trigger "
    "captures.": (
        "Telefon bağlı değil. iPhone'da bir tarama başlatın ve \"Allow PackLab to trigger "
        'captures" seçeneğini açın.'
    ),
    "Phone connected, no active scan.": "Telefon bağlı, etkin tarama yok.",
    # Shell status messages
    "Created project {path}": "Proje oluşturuldu: {path}",
    "New project failed: {error}": "Yeni proje oluşturulamadı: {error}",
    "Opened project {path}": "Proje açıldı: {path}",
    "Open project failed: {error}": "Proje açılamadı: {error}",
    "Project closed": "Proje kapatıldı",
    "Close project failed: {error}": "Proje kapatılamadı: {error}",
    "Diagnostic bundle written: {path}": "Tanılama paketi yazıldı: {path}",
    "Diagnostic bundle failed: {error}": "Tanılama paketi oluşturulamadı: {error}",
    "All changes saved": "Tüm değişiklikler kaydedildi",
    "Design Model: unsaved edits (autosave pending)": (
        "Tasarım Modeli: kaydedilmemiş değişiklikler (otomatik kayıt bekliyor)"
    ),
    # Buttons
    "1. Isolate object": "1. Nesneyi ayır",
    "2. Scale from mat markers": "2. Mat işaretlerinden ölçekle",
    "3. Measure (mm)": "3. Ölç (mm)",
    "4. Fit Design Model": "4. Tasarım Modelini oturt",
    "Add label zone": "Etiket alanı ekle",
    "Add to library (Design Model / Scan Master)": "Kütüphaneye ekle (Design Model / Scan Master)",
    "Add to library": "Kütüphaneye ekle",
    "Apply dimensions": "Ölçüleri uygula",
    "Apply dimensions (new revision)": "Ölçüleri uygula (yeni revizyon)",
    "Back up library…": "Kütüphaneyi yedekle…",
    "Build model": "Model oluştur",
    "Build model automatically after import": "İçe aktarmadan sonra modeli otomatik oluştur",
    "Cancel": "İptal",
    "Cancel render": "Görüntülemeyi iptal et",
    "Capture now": "Şimdi çek",
    "Clear filters": "Filtreleri temizle",
    "Create Design Model": "Tasarım Modeli oluştur",
    "Create SKU from selected geometry": "Seçili geometriden SKU (stok kodu) oluştur",
    "Export": "Dışa aktar",
    "Export contact sheet…": "Özet sayfası dışa aktar…",
    "Export dieline SVG (mm)…": "Kesim çizgisi SVG dışa aktar (mm)…",
    "Export dimension report…": "Ölçü raporu dışa aktar…",
    "Export selected part…": "Seçili parçayı dışa aktar…",
    "Export selected source": "Seçili kaynağı dışa aktar",
    "Finish scan": "Taramayı bitir",
    "Fit": "Oturt",
    "Import .packscan file…": ".packscan dosyası içe aktar…",
    "Import artwork (SVG/PNG)…": "Baskı görseli içe aktar (SVG/PNG)…",
    "New code": "Yeni kod",
    "Object-only, scale and measure": "Yalnız nesne, ölçekle ve ölç",
    "Open Design Model…": "Tasarım Modeli aç…",
    "Open built model…": "Oluşturulan modeli aç…",
    "Open model in viewer": "Modeli görüntüleyicide aç",
    "Open model…": "Model aç…",
    "Open the project's current Design Model": "Projenin güncel Tasarım Modelini aç",
    "Owner review: accept partial scan / straight jar": (
        "Sahip incelemesi: kısmi taramayı / düz kavanozu kabul et"
    ),
    "Place artwork on the front…": "Baskı görselini ön yüze yerleştir…",
    "Promote Scan Master": "Scan Master'a yükselt",
    "Promote to Scan Master": "Scan Master'a yükselt",
    "Re-check engines": "Motorları yeniden denetle",
    "Checking engines…": "Motorlar denetleniyor…",
    "Receive from iPhone": "iPhone'dan al",
    "Redo closure replacement": "Kapak değişimini yinele",
    "Refresh": "Yenile",
    "Render mockup (Blender)…": "Önizleme oluştur (Blender)…",
    "Replace closure with the dimensions above": "Kapağı yukarıdaki ölçülerle değiştir",
    "Restore backup into folder…": "Yedeği klasöre geri yükle…",
    "Revoke": "İptal et (yetkiyi kaldır)",
    "Save Design Model revision": "Tasarım Modeli revizyonunu kaydet",
    "Save revision to project": "Revizyonu projeye kaydet",
    "Show closure / head": "Kapağı / başlığı göster",
    "Stop receiving": "Almayı durdur",
    "Submit correction": "Düzeltmeyi gönder",
    "Suggest zone": "Alan öner",
    "Undo": "Geri al",
    "Undo closure replacement": "Kapak değişimini geri al",
    "Use latest project build": "Projedeki son modeli kullan",
    "Use manual reference": "Elle referansı kullan",
    "Use project Design Model": "Projenin Tasarım Modelini kullan",
    # Combo items (display only; item data stays the logic key)
    "Any closure": "Tüm kapaklar",
    "Any material": "Tüm malzemeler",
    "Any status": "Tüm durumlar",
    "Any volume": "Tüm hacimler",
    "Back": "Arka",
    "Front": "Ön",
    "Wrap": "Sarmal",
    "Grid": "Izgara",
    "List": "Liste",
    "Contain": "Sığdır",
    "Cover": "Kapla",
    "Stretch": "Uzat",
    "Unknown": "Bilinmiyor",
    "Unknown volume": "Bilinmeyen hacim",
    "Paint foreground": "Ön planı boya",
    "Erase to background": "Arka plana sil",
    "Editable Design Model / CAD": "Düzenlenebilir Tasarım Modeli / CAD",
    "Scan Mesh / Scan Master": "Tarama ağı / Scan Master",
    "Selected Scan Master / Design Model (captured)": "Seçili Scan Master / Tasarım Modeli",
    "Clear PET visual reference": "Şeffaf PET görsel referansı",
    "Colored PET visual reference": "Renkli PET görsel referansı",
    "Natural HDPE visual reference": "Doğal HDPE görsel referansı",
    "White HDPE visual reference": "Beyaz HDPE görsel referansı",
    "PP cap visual reference": "PP kapak görsel referansı",
    # Group boxes and form labels
    "Closure workflow": "Kapak iş akışı",
    "Design Model": "Tasarım Modeli (Design Model)",
    "Design Model (editable)": "Tasarım Modeli (düzenlenebilir)",
    "Key dimensions (mm_unverified)": f"Temel ölçüler (mm_unverified; {_SCALE_NOTE})",
    "Label zone (curvature-checked on the exact CAD surface)": (
        "Etiket alanı (CAD yüzeyinde eğrilik denetimli)"
    ),
    "Labels and artwork": "Etiketler ve baskı görselleri",
    "Material and mockup (visual reference only)": (
        "Malzeme ve önizleme (yalnızca görsel referans)"
    ),
    "Package family": "Ambalaj ailesi",
    "Save and export": "Kaydet ve dışa aktar",
    "Scale and upright": "Ölçek ve dikey hizalama",
    "Actor": "Kişi",
    "Reason": "Gerekçe",
    "Promotion reason": "Yükseltme gerekçesi",
    "Available formats": "Kullanılabilir biçimler",
    "Format": "Biçim",
    "Source type": "Kaynak türü",
    "Selected authority": "Seçili yetkili kaynak",
    "Family": "Aile",
    "Start from": "Başlangıç",
    "Preset": "Hazır ayar",
    "Part": "Parça",
    "Kind": "Tür",
    "Variant": "Varyant",
    "Material": "Malzeme",
    "Height": "Yükseklik",
    "Diameter": "Çap",
    "Placement (0..1 of the host face)": "Yerleşim (yüzeyin 0..1 oranı)",
    "Known A-B length": "Bilinen A-B uzunluğu",
    "Manual point A (model units x, y, z)": "Elle A noktası (model birimi x, y, z)",
    "Manual point B": "Elle B noktası",
    "Mat print check: 100 mm bar measures": "Mat baskı kontrolü: 100 mm çubuğun ölçüsü",
    "Brush": "Fırça",
    "e.g. jar-500ml-a1b2c3d4": "ör. jar-500ml-a1b2c3d4",
    "e.g. Jar 500 ml": "ör. Kavanoz 500 ml",
    "Asset ID": "Varlık kimliği (ID)",
    "Display name": "Görünen ad",
    "SKU ID": "SKU (stok kodu) ID",
    "Name": "Ad",
    "Status": "Durum",
    "Received scans": "Gelen taramalar",
    "Paired devices": "Eşleşmiş cihazlar",
    "Remote capture": "Uzaktan çekim",
    "Related Packaging Assets": "İlgili ambalaj varlıkları",
    "Reconstruction engines (COLMAP / OpenMVS)": (
        "3B yeniden yapılandırma motorları (COLMAP / OpenMVS)"
    ),
    "Build 3D model": "3B model oluştur",
    "Build revision": "Derleme revizyonu",
    "Local update manifest": "Yerel güncelleme bildirimi",
    "PackScan schema": "PackScan şeması",
    # Static status texts
    "No 3D preview selected.": "3B önizleme seçilmedi.",
    "No Design Model open.": "Açık Tasarım Modeli yok.",
    "No artwork.": "Baskı görseli yok.",
    "No asset selected.": "Varlık seçilmedi.",
    "No export requested.": "Dışa aktarma istenmedi.",
    "No mockup rendered.": "Önizleme oluşturulmadı.",
    "No model loaded. Drag to orbit, right-drag to pan, wheel to zoom.": (
        "Model yüklenmedi. Döndürmek için sürükleyin, kaydırmak için sağ tuşla sürükleyin, "
        "yakınlaştırmak için tekerleği kullanın."
    ),
    "No packaging assets in this library.": "Bu kütüphanede ambalaj varlığı yok.",
    "No promotion requested.": "Yükseltme istenmedi.",
    "No selected persisted Scan Master revision is available.": (
        "Seçili, kaydedilmiş bir Scan Master revizyonu yok."
    ),
    "Open a Design Model to place labels.": "Etiket yerleştirmek için bir Tasarım Modeli açın.",
    "Open a mask correction session to begin.": "Başlamak için bir maske düzeltme oturumu açın.",
    "Open the built model (dense PLY or textured OBJ).": (
        "Oluşturulan modeli açın (yoğun PLY veya dokulu OBJ)."
    ),
    "Project Design Model: no project open.": "Projenin Tasarım Modeli: açık proje yok.",
    "Choose a package family.": "Bir ambalaj ailesi seçin.",
    "Closure: open a project first (File > New/Open project)": (
        "Kapak: önce bir proje açın (Dosya > Yeni/Proje Aç)"
    ),
    "Create SKU uses the selected asset; artwork comes from the Labels tab.": (
        "SKU oluşturma seçili varlığı kullanır; baskı görseli Etiketler sayfasından gelir."
    ),
    "Press Receive from iPhone, then in the iPhone app choose Send to PackLab > Scan QR "
    "offer. The phone and this PC must be on the same Wi-Fi.": (
        '"iPhone\'dan al" düğmesine basın, ardından iPhone uygulamasında Send to PackLab > '
        "Scan QR offer seçin. Telefon ve bu bilgisayar aynı Wi-Fi ağında olmalıdır."
    ),
    "Select a scan in Capture Inbox and press Build model, or import one with automatic "
    "building switched on in Settings.": (
        "Tarama Gelen Kutusu'nda bir tarama seçip \"Model oluştur\"a basın veya Ayarlar'da "
        "otomatik oluşturma açıkken bir tarama içe aktarın."
    ),
    "Search ID, name, supplier, or family": "ID, ad, tedarikçi veya aile ara",
    "variant name, e.g. front, back, wrap-v2": "varyant adı, ör. front, back, wrap-v2",
    # Audit wording: identifiers kept verbatim, plain Turkish explanation added.
    "Before physical validation: DEFERRED_OWNER_VALIDATION; inherited scale state; "
    "mold_use_authorized=false.": (
        "Fiziksel doğrulamadan önce: DEFERRED_OWNER_VALIDATION; inherited scale state; "
        "mold_use_authorized=false. (Açıklama: ölçüler henüz gerçek nesneyle doğrulanmadı, "
        "ölçek önceki adımdan devralındı ve kalıp üretiminde kullanılamaz.)"
    ),
    "Dimensions are mm_unverified design geometry; print fit, colour and physical accuracy "
    "are DEFERRED_OWNER_VALIDATION.": (
        "Ölçüler mm_unverified tasarım geometrisidir; baskı uyumu, renk ve fiziksel "
        f"doğruluk DEFERRED_OWNER_VALIDATION. ({_SCALE_NOTE}; {_DEFERRED}.)"
    ),
    "Exports are derived files. DEFERRED_OWNER_VALIDATION; physical accuracy, mold use, and "
    "manufacturing suitability are not established.": (
        "Dışa aktarılan dosyalar türetilmiş dosyalardır. DEFERRED_OWNER_VALIDATION. "
        "(Açıklama: fiziksel doğruluk, kalıp kullanımı ve üretime uygunluk henüz "
        "kanıtlanmadı.)"
    ),
    "Next: object-only cleanup (Mask Correction), scale and measure, Design Model (Editor), "
    "labels, export (Exports). The model is RECONSTRUCTION_OBSERVATION in relative units "
    "until scale is verified; it is not Scan Master.": (
        "Sonraki adımlar: yalnız nesne temizliği (Maske Düzeltme), ölçekleme ve ölçme, "
        "Tasarım Modeli, etiketler, dışa aktarım. Ölçek doğrulanana kadar model "
        "RECONSTRUCTION_OBSERVATION durumundadır (göreli birimde gözlem; gerçek mm değil); "
        "Scan Master değildir."
    ),
}
