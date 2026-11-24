"""Formlardaki seçim listeleri. Değiştirmek için bu dosyayı düzenleyin."""

ILLER = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Aksaray", "Amasya", "Ankara", "Antalya", "Ardahan",
    "Artvin", "Aydın", "Balıkesir", "Bartın", "Batman", "Bayburt", "Bilecik", "Bingöl", "Bitlis", "Bolu",
    "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır", "Düzce", "Edirne",
    "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane", "Hakkari", "Hatay",
    "Iğdır", "Isparta", "İstanbul", "İzmir", "Kahramanmaraş", "Karabük", "Karaman", "Kars", "Kastamonu",
    "Kayseri", "Kilis", "Kırıkkale", "Kırklareli", "Kırşehir", "Kocaeli", "Konya", "Kütahya", "Malatya",
    "Manisa", "Mardin", "Mersin", "Muğla", "Muş", "Nevşehir", "Niğde", "Ordu", "Osmaniye", "Rize",
    "Sakarya", "Samsun", "Şanlıurfa", "Siirt", "Sinop", "Şırnak", "Sivas", "Tekirdağ", "Tokat", "Trabzon",
    "Tunceli", "Uşak", "Van", "Yalova", "Yozgat", "Zonguldak",
]

# İlçe "seçimlik/yazı": bu illerde liste önerilir, diğerlerinde elle yazılır.
ILCELER = {
    "İstanbul": [
        "Adalar", "Arnavutköy", "Ataşehir", "Avcılar", "Bağcılar", "Bahçelievler", "Bakırköy", "Başakşehir",
        "Bayrampaşa", "Beşiktaş", "Beykoz", "Beylikdüzü", "Beyoğlu", "Büyükçekmece", "Çatalca", "Çekmeköy",
        "Esenler", "Esenyurt", "Eyüpsultan", "Fatih", "Gaziosmanpaşa", "Güngören", "Kadıköy", "Kağıthane",
        "Kartal", "Küçükçekmece", "Maltepe", "Pendik", "Sancaktepe", "Sarıyer", "Silivri", "Sultanbeyli",
        "Sultangazi", "Şile", "Şişli", "Tuzla", "Ümraniye", "Üsküdar", "Zeytinburnu",
    ],
    "Kocaeli": [
        "Başiskele", "Çayırova", "Darıca", "Derince", "Dilovası", "Gebze", "Gölcük", "İzmit", "Kandıra",
        "Karamürsel", "Kartepe", "Körfez",
    ],
    "Ankara": ["Altındağ", "Çankaya", "Etimesgut", "Keçiören", "Mamak", "Pursaklar", "Sincan", "Temelli", "Yenimahalle"],
    "Bursa": ["Gemlik", "Gürsu", "İnegöl", "Kestel", "Mudanya", "Nilüfer", "Osmangazi", "Yıldırım"],
    "İzmir": ["Bayraklı", "Bornova", "Buca", "Çiğli", "Gaziemir", "Karabağlar", "Karşıyaka", "Kemalpaşa", "Konak", "Torbalı"],
}

SEKTORLER = [
    "Otomotiv ve Yan Sanayi", "Beyaz Eşya", "Gıda ve İçecek", "Ambalaj", "Tekstil",
    "Makine İmalatı", "Enerji", "İlaç ve Kimya", "Elektrik - Elektronik", "Metal ve Döküm",
    "Plastik ve Kauçuk", "Lojistik ve Depolama", "Otomasyon Entegratörü / Mühendislik",
    "Savunma Sanayi", "Bina ve Tesis Otomasyonu", "Diğer",
]

MEZUNIYET_ALANLARI = [
    "Endüstriyel Otomasyon Teknolojileri (Lise)",
    "Elektrik - Elektronik Teknolojisi (Lise)",
    "Makine ve Tasarım Teknolojisi (Lise)",
    "Mekatronik (Önlisans)",
    "Kontrol ve Otomasyon Teknolojisi (Önlisans)",
    "Elektrik (Önlisans)",
    "Elektronik Teknolojisi (Önlisans)",
    "Mekatronik Mühendisliği",
    "Elektrik - Elektronik Mühendisliği",
    "Kontrol ve Otomasyon Mühendisliği",
    "Makine Mühendisliği",
    "Bilgisayar Mühendisliği",
    "Endüstri Mühendisliği",
    "Diğer",
]

UZMANLIK_ALANLARI = [
    "PLC Programlama", "HMI Programlama", "SCADA Programlama", "Mekanik Tasarım",
    "Robot Programlama", "Gömülü Sistem PCB Tasarım", "Pano Tasarımı", "Proje Mühendisliği",
    "Satış Mühendisliği", "Bakım Mühendisliği", "Pano Montajı",
]

ROBOT_MARKALARI = ["Kuka", "Fanuc", "ABB", "Yaskawa"]

CALISMA_TURLERI = ["Tam zamanlı", "Yarı zamanlı", "Staj", "Proje bazlı"]

# İşletmenin istediği en az deneyim (yıl)
DENEYIM_SECENEKLERI = [(0, "Deneyimsiz olabilir"), (1, "En az 1 yıl"), (2, "En az 2 yıl"),
                       (3, "En az 3 yıl"), (5, "En az 5 yıl")]

MAKS_DENEYIM = 3  # İş arayanın girebileceği deneyim sayısı
