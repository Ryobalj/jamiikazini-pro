# businesses/management/commands/seed_product_categories.py

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from businesses.models.product_category import ProductCategory
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# =====================================================
# CATEGORIES DATA - kama rafu halisi za duka
# =====================================================

CATEGORIES = [
    {
        "slug": "vyakula",
        "name_en": "Food & Groceries",
        "name_sw": "Vyakula",
        "name_fr": "Alimentation",
        "name_ar": "الأغذية والبقالة",
        "name_af": "Kos en Kruideniersware",
        "name_ha": "Abinci da Kayan Masarufi",
        "name_hi": "भोजन और किराना",
        "name_ja": "食品・食料品",
        "name_ko": "식품 및 식료품",
        "name_lg": "Emmere n'Ebyeisulo",
        "name_pt": "Alimentos e Mercearia",
        "name_ru": "Продукты и бакалея",
        "name_rw": "Ibiribwa n'Ibicuruzwa by'Amaduka",
        "name_zh": "食品与杂货",
        "name_es": "Alimentos y Abarrotes",
        "description_en": "Food staples, groceries and cooking essentials",
        "description_sw": "Vyakula vya kila siku, chakula cha dukani na vya kupikia",
        "description_ar": "المواد الغذائية الأساسية ولوازم الطبخ",
        "description_af": "Voedselstapels, kruideniersware en kooknoodsaaklikhede",
        "description_ha": "Kayan abinci na yau da kullum, kayan masarufi da kayan dafa abinci",
        "description_hi": "मुख्य खाद्य पदार्थ, किराना और खाना पकाने की आवश्यक वस्तुएं",
        "description_ja": "主食、食料品、料理の必需品",
        "description_ko": "주식, 식료품 및 요리 필수품",
        "description_lg": "Emmere enkulu, ebyeisulo n'ebikozesebwa mu kufumba",
        "description_pt": "Alimentos básicos, mercearia e itens essenciais para cozinhar",
        "description_ru": "Основные продукты питания, бакалея и кулинарные принадлежности",
        "description_rw": "Ibiribwa fatizo, ibicuruzwa by'amaduka n'ibikoresho byo guteka",
        "description_zh": "主食、杂货及烹饪必需品",
        "description_es": "Alimentos básicos, abarrotes y esenciales para cocinar",
        "children": [
            {"slug": "nafaka-unga", "name_en": "Grains & Flour", "name_sw": "Nafaka na Unga", "name_fr": "Céréales et farine", "name_ar": "الحبوب والدقيق", "name_af": "Grane en Meel", "name_ha": "Hatsi da Gari", "name_hi": "अनाज और आटा", "name_ja": "穀物・小麦粉", "name_ko": "곡물 및 밀가루", "name_lg": "Empeke n'Obuwunga", "name_pt": "Grãos e Farinha", "name_ru": "Крупы и мука", "name_rw": "Ibinyampeke n'Ifu", "name_zh": "谷物与面粉", "name_es": "Granos y Harina"},
            {"slug": "mafuta-kupikia", "name_en": "Cooking Oil", "name_sw": "Mafuta ya Kupikia", "name_fr": "Huile de cuisson", "name_ar": "زيت الطبخ", "name_af": "Kookolie", "name_ha": "Man Girki", "name_hi": "खाना पकाने का तेल", "name_ja": "食用油", "name_ko": "식용유", "name_lg": "Amafuta ag'Okufumbisa", "name_pt": "Óleo de Cozinha", "name_ru": "Растительное масло", "name_rw": "Amavuta yo Guteka", "name_zh": "食用油", "name_es": "Aceite de Cocina"},
            {"slug": "vyakula-makopo", "name_en": "Canned & Packaged Foods", "name_sw": "Vyakula vya Makopo", "name_fr": "Aliments en conserve", "name_ar": "الأغذية المعلبة والمعبأة", "name_af": "Blik- en Verpakte Kos", "name_ha": "Abincin Gwangwani da Marufi", "name_hi": "डिब्बाबंद और पैक किया गया भोजन", "name_ja": "缶詰・加工食品", "name_ko": "통조림 및 포장 식품", "name_lg": "Emmere y'omu Bikopo n'Ebipakiddwa", "name_pt": "Alimentos Enlatados e Embalados", "name_ru": "Консервированные и упакованные продукты", "name_rw": "Ibiribwa byo mu Mabati n'Ibipfunyitse", "name_zh": "罐装及包装食品", "name_es": "Alimentos Enlatados y Envasados"},
            {"slug": "viungo", "name_en": "Spices & Condiments", "name_sw": "Viungo", "name_fr": "Épices", "name_ar": "التوابل", "name_af": "Speserye en Geursels", "name_ha": "Kayan Yaji", "name_hi": "मसाले और मसाला", "name_ja": "香辛料・調味料", "name_ko": "향신료 및 조미료", "name_lg": "Ebiwoomya", "name_pt": "Temperos e Condimentos", "name_ru": "Специи и приправы", "name_rw": "Ibirungo", "name_zh": "香料与调味品", "name_es": "Especias y Condimentos"},
        ],
    },
    {
        "slug": "vinywaji",
        "name_en": "Beverages",
        "name_sw": "Vinywaji",
        "name_fr": "Boissons",
        "name_ar": "المشروبات",
        "name_af": "Drankies",
        "name_ha": "Abubuwan Sha",
        "name_hi": "पेय पदार्थ",
        "name_ja": "飲料",
        "name_ko": "음료",
        "name_lg": "Ebyokunywa",
        "name_pt": "Bebidas",
        "name_ru": "Напитки",
        "name_rw": "Ibinyobwa",
        "name_zh": "饮料",
        "name_es": "Bebidas",
        "description_en": "Drinks - soft drinks, water, tea and coffee",
        "description_sw": "Soda, maji, chai na kahawa",
        "description_ar": "المشروبات الغازية والماء والشاي والقهوة",
        "description_af": "Drankies - koeldrank, water, tee en koffie",
        "description_ha": "Abubuwan sha - ruwan zaki, ruwa, shayi da kofi",
        "description_hi": "पेय - शीतल पेय, पानी, चाय और कॉफी",
        "description_ja": "飲み物 - 清涼飲料水、水、紅茶、コーヒー",
        "description_ko": "음료 - 청량음료, 물, 차 및 커피",
        "description_lg": "Ebyokunywa - soda, amazzi, caayi ne kaawa",
        "description_pt": "Bebidas - refrigerantes, água, chá e café",
        "description_ru": "Напитки - газировка, вода, чай и кофе",
        "description_rw": "Ibinyobwa - amazi asukiranye, amazi, icyayi na kawa",
        "description_zh": "饮品——汽水、水、茶与咖啡",
        "description_es": "Bebidas: refrescos, agua, té y café",
        "children": [
            {"slug": "soda-juisi", "name_en": "Soft Drinks & Juice", "name_sw": "Soda na Juisi", "name_fr": "Sodas et jus", "name_ar": "المشروبات الغازية والعصائر", "name_af": "Koeldrank en Sap", "name_ha": "Ruwan Zaki da Ruwan 'Ya'yan Itace", "name_hi": "शीतल पेय और जूस", "name_ja": "清涼飲料水・ジュース", "name_ko": "청량음료 및 주스", "name_lg": "Soda na Envinnyo", "name_pt": "Refrigerantes e Sucos", "name_ru": "Газировка и соки", "name_rw": "Amazi Asukiranye n'Umutobe", "name_zh": "汽水与果汁", "name_es": "Refrescos y Jugos"},
            {"slug": "maji", "name_en": "Water", "name_sw": "Maji", "name_fr": "Eau", "name_ar": "الماء", "name_af": "Water", "name_ha": "Ruwa", "name_hi": "पानी", "name_ja": "水", "name_ko": "물", "name_lg": "Amazzi", "name_pt": "Água", "name_ru": "Вода", "name_rw": "Amazi", "name_zh": "水", "name_es": "Agua"},
            {"slug": "chai-kahawa", "name_en": "Tea & Coffee", "name_sw": "Chai na Kahawa", "name_fr": "Thé et café", "name_ar": "الشاي والقهوة", "name_af": "Tee en Koffie", "name_ha": "Shayi da Kofi", "name_hi": "चाय और कॉफी", "name_ja": "紅茶・コーヒー", "name_ko": "차 및 커피", "name_lg": "Caayi ne Kaawa", "name_pt": "Chá e Café", "name_ru": "Чай и кофе", "name_rw": "Icyayi na Kawa", "name_zh": "茶与咖啡", "name_es": "Té y Café"},
        ],
    },
    {
        "slug": "nguo-mavazi",
        "name_en": "Clothing & Apparel",
        "name_sw": "Nguo na Mavazi",
        "name_fr": "Vêtements",
        "name_ar": "الملابس والأزياء",
        "name_af": "Klere en Drag",
        "name_ha": "Tufafi da Kaya",
        "name_hi": "कपड़े और परिधान",
        "name_ja": "衣料品・アパレル",
        "name_ko": "의류 및 의상",
        "name_lg": "Engoye",
        "name_pt": "Roupas e Vestuário",
        "name_ru": "Одежда",
        "name_rw": "Imyenda",
        "name_zh": "服装与服饰",
        "name_es": "Ropa y Vestimenta",
        "description_en": "Clothes, shoes and fashion accessories",
        "description_sw": "Nguo, viatu na vifaa vya mavazi",
        "description_ar": "الملابس والأحذية وإكسسوارات الأزياء",
        "description_af": "Klere, skoene en modeaanhangsels",
        "description_ha": "Tufafi, takalma da kayan kwalliya",
        "description_hi": "कपड़े, जूते और फैशन एक्सेसरीज़",
        "description_ja": "衣類、靴、ファッション小物",
        "description_ko": "의류, 신발 및 패션 액세서리",
        "description_lg": "Engoye, engatto n'ebyokwewunda",
        "description_pt": "Roupas, sapatos e acessórios de moda",
        "description_ru": "Одежда, обувь и модные аксессуары",
        "description_rw": "Imyenda, inkweto n'ibikoresho by'imyambarire",
        "description_zh": "服装、鞋类与时尚配饰",
        "description_es": "Ropa, calzado y accesorios de moda",
        "children": [
            {"slug": "nguo-wanaume", "name_en": "Men's Clothing", "name_sw": "Nguo za Wanaume", "name_fr": "Vêtements pour hommes", "name_ar": "ملابس رجالية", "name_af": "Mansklere", "name_ha": "Tufafin Maza", "name_hi": "पुरुषों के कपड़े", "name_ja": "メンズ衣料", "name_ko": "남성 의류", "name_lg": "Engoye z'Abasajja", "name_pt": "Roupas Masculinas", "name_ru": "Мужская одежда", "name_rw": "Imyenda y'Abagabo", "name_zh": "男装", "name_es": "Ropa de Hombre"},
            {"slug": "nguo-wanawake", "name_en": "Women's Clothing", "name_sw": "Nguo za Wanawake", "name_fr": "Vêtements pour femmes", "name_ar": "ملابس نسائية", "name_af": "Damesklere", "name_ha": "Tufafin Mata", "name_hi": "महिलाओं के कपड़े", "name_ja": "レディース衣料", "name_ko": "여성 의류", "name_lg": "Engoye z'Abakazi", "name_pt": "Roupas Femininas", "name_ru": "Женская одежда", "name_rw": "Imyenda y'Abagore", "name_zh": "女装", "name_es": "Ropa de Mujer"},
            {"slug": "nguo-watoto", "name_en": "Children's Clothing", "name_sw": "Nguo za Watoto", "name_fr": "Vêtements pour enfants", "name_ar": "ملابس أطفال", "name_af": "Kinderklere", "name_ha": "Tufafin Yara", "name_hi": "बच्चों के कपड़े", "name_ja": "子供服", "name_ko": "아동복", "name_lg": "Engoye z'Abaana", "name_pt": "Roupas Infantis", "name_ru": "Детская одежда", "name_rw": "Imyenda y'Abana", "name_zh": "童装", "name_es": "Ropa de Niños"},
            {"slug": "viatu", "name_en": "Shoes", "name_sw": "Viatu", "name_fr": "Chaussures", "name_ar": "الأحذية", "name_af": "Skoene", "name_ha": "Takalma", "name_hi": "जूते", "name_ja": "靴", "name_ko": "신발", "name_lg": "Engatto", "name_pt": "Sapatos", "name_ru": "Обувь", "name_rw": "Inkweto", "name_zh": "鞋类", "name_es": "Zapatos"},
        ],
    },
    {
        "slug": "vifaa-nyumbani",
        "name_en": "Household Items",
        "name_sw": "Vifaa vya Nyumbani",
        "name_fr": "Articles ménagers",
        "name_ar": "مستلزمات منزلية",
        "name_af": "Huishoudelike Items",
        "name_ha": "Kayan Gida",
        "name_hi": "घरेलू सामान",
        "name_ja": "家庭用品",
        "name_ko": "가정용품",
        "name_lg": "Ebintu by'Awaka",
        "name_pt": "Itens para o Lar",
        "name_ru": "Товары для дома",
        "name_rw": "Ibikoresho by'Urugo",
        "name_zh": "家居用品",
        "name_es": "Artículos para el Hogar",
        "description_en": "Furniture, kitchenware and cleaning supplies",
        "description_sw": "Samani, vyombo vya jikoni na vifaa vya kusafisha",
        "description_ar": "الأثاث وأدوات المطبخ ومستلزمات التنظيف",
        "description_af": "Meubels, kombuisware en skoonmaakbenodigdhede",
        "description_ha": "Kayan daki, kayan girki da kayan tsaftacewa",
        "description_hi": "फर्नीचर, रसोई के बर्तन और सफाई की आपूर्ति",
        "description_ja": "家具、キッチン用品、清掃用品",
        "description_ko": "가구, 주방용품 및 청소용품",
        "description_lg": "Ebintu by'omu nnyumba, ebyokufumbira n'ebyokwerongoosa",
        "description_pt": "Móveis, utensílios de cozinha e produtos de limpeza",
        "description_ru": "Мебель, кухонная утварь и чистящие средства",
        "description_rw": "Ibikoresho byo mu nzu, ibikoresho byo guteka n'ibyo gusukura",
        "description_zh": "家具、厨具与清洁用品",
        "description_es": "Muebles, utensilios de cocina y artículos de limpieza",
        "children": [
            {"slug": "samani", "name_en": "Furniture", "name_sw": "Samani", "name_fr": "Meubles", "name_ar": "الأثاث", "name_af": "Meubels", "name_ha": "Kayan Daki", "name_hi": "फर्नीचर", "name_ja": "家具", "name_ko": "가구", "name_lg": "Ebintu by'omu Nnyumba", "name_pt": "Móveis", "name_ru": "Мебель", "name_rw": "Ibikoresho byo mu Nzu", "name_zh": "家具", "name_es": "Muebles"},
            {"slug": "vyombo-jikoni", "name_en": "Kitchenware", "name_sw": "Vyombo vya Jikoni", "name_fr": "Ustensiles de cuisine", "name_ar": "أدوات المطبخ", "name_af": "Kombuisware", "name_ha": "Kayan Girki", "name_hi": "रसोई के बर्तन", "name_ja": "台所用品", "name_ko": "주방용품", "name_lg": "Ebyokufumbira", "name_pt": "Utensílios de Cozinha", "name_ru": "Кухонная утварь", "name_rw": "Ibikoresho byo Guteka", "name_zh": "厨具", "name_es": "Utensilios de Cocina"},
            {"slug": "vifaa-kusafisha", "name_en": "Cleaning Supplies", "name_sw": "Vifaa vya Kusafisha", "name_fr": "Produits de nettoyage", "name_ar": "مستلزمات التنظيف", "name_af": "Skoonmaakbenodigdhede", "name_ha": "Kayan Tsaftacewa", "name_hi": "सफाई की आपूर्ति", "name_ja": "掃除用品", "name_ko": "청소용품", "name_lg": "Ebyokwerongoosa", "name_pt": "Produtos de Limpeza", "name_ru": "Чистящие средства", "name_rw": "Ibikoresho byo Gusukura", "name_zh": "清洁用品", "name_es": "Productos de Limpieza"},
        ],
    },
    {
        "slug": "elektroniki",
        "name_en": "Electronics",
        "name_sw": "Elektroniki",
        "name_fr": "Électronique",
        "name_ar": "الإلكترونيات",
        "name_af": "Elektronika",
        "name_ha": "Na'urorin Lantarki",
        "name_hi": "इलेक्ट्रॉनिक्स",
        "name_ja": "電子機器",
        "name_ko": "전자제품",
        "name_lg": "Ebya Elekitoroniki",
        "name_pt": "Eletrônicos",
        "name_ru": "Электроника",
        "name_rw": "Ibikoresho bya Elegitoroniki",
        "name_zh": "电子产品",
        "name_es": "Electrónica",
        "description_en": "Phones, computers and electrical equipment",
        "description_sw": "Simu, kompyuta na vifaa vya umeme",
        "description_ar": "الهواتف والحواسيب والأجهزة الكهربائية",
        "description_af": "Fone, rekenaars en elektriese toerusting",
        "description_ha": "Wayoyi, kwamfutoci da na'urorin lantarki",
        "description_hi": "फोन, कंप्यूटर और विद्युत उपकरण",
        "description_ja": "電話、コンピューター、電気機器",
        "description_ko": "휴대폰, 컴퓨터 및 전자 장비",
        "description_lg": "Essimu, kompyuta n'ebyuma bya masannyalaze",
        "description_pt": "Telefones, computadores e equipamentos elétricos",
        "description_ru": "Телефоны, компьютеры и электрооборудование",
        "description_rw": "Telefone, mudasobwa n'ibikoresho bya elegitoroniki",
        "description_zh": "手机、电脑与电气设备",
        "description_es": "Teléfonos, computadoras y equipos eléctricos",
        "children": [
            {"slug": "simu-vifaa", "name_en": "Phones & Accessories", "name_sw": "Simu na Vifaa", "name_fr": "Téléphones et accessoires", "name_ar": "الهواتف والملحقات", "name_af": "Fone en Bybehore", "name_ha": "Wayoyi da Kayan Aiki", "name_hi": "फोन और सामान", "name_ja": "電話・アクセサリー", "name_ko": "휴대폰 및 액세서리", "name_lg": "Essimu n'Ebigenderako", "name_pt": "Telefones e Acessórios", "name_ru": "Телефоны и аксессуары", "name_rw": "Telefone n'Ibikoresho", "name_zh": "手机与配件", "name_es": "Teléfonos y Accesorios"},
            {"slug": "kompyuta", "name_en": "Computers", "name_sw": "Kompyuta", "name_fr": "Ordinateurs", "name_ar": "الحواسيب", "name_af": "Rekenaars", "name_ha": "Kwamfutoci", "name_hi": "कंप्यूटर", "name_ja": "コンピューター", "name_ko": "컴퓨터", "name_lg": "Kompyuta", "name_pt": "Computadores", "name_ru": "Компьютеры", "name_rw": "Mudasobwa", "name_zh": "电脑", "name_es": "Computadoras"},
            {"slug": "vifaa-umeme", "name_en": "Electrical Appliances", "name_sw": "Vifaa vya Umeme", "name_fr": "Appareils électriques", "name_ar": "الأجهزة الكهربائية", "name_af": "Elektriese Toestelle", "name_ha": "Na'urorin Lantarki", "name_hi": "विद्युत उपकरण", "name_ja": "電化製品", "name_ko": "전자기기", "name_lg": "Ebyuma bya Masannyalaze", "name_pt": "Eletrodomésticos", "name_ru": "Электроприборы", "name_rw": "Ibikoresho bya Amashanyarazi", "name_zh": "电器", "name_es": "Electrodomésticos"},
        ],
    },
    {
        "slug": "vipodozi-urembo",
        "name_en": "Cosmetics & Beauty",
        "name_sw": "Vipodozi na Urembo",
        "name_fr": "Cosmétiques et beauté",
        "name_ar": "مستحضرات التجميل والجمال",
        "name_af": "Skoonheidsmiddels",
        "name_ha": "Kayan Kwalliya da Kyau",
        "name_hi": "सौंदर्य प्रसाधन",
        "name_ja": "化粧品・美容",
        "name_ko": "화장품 및 뷰티",
        "name_lg": "Eby'Okwewunda",
        "name_pt": "Cosméticos e Beleza",
        "name_ru": "Косметика и красота",
        "name_rw": "Ibiribagirisha n'Ubwiza",
        "name_zh": "化妆品与美容",
        "name_es": "Cosméticos y Belleza",
        "description_en": "Cosmetics, perfumes and hair products",
        "description_sw": "Vipodozi, manukato na bidhaa za nywele",
        "description_ar": "مستحضرات التجميل والعطور ومنتجات الشعر",
        "description_af": "Skoonheidsmiddels, parfuum en haarprodukte",
        "description_ha": "Kayan kwalliya, turare da kayayyakin gashi",
        "description_hi": "सौंदर्य प्रसाधन, इत्र और बाल उत्पाद",
        "description_ja": "化粧品、香水、ヘアケア製品",
        "description_ko": "화장품, 향수 및 헤어 제품",
        "description_lg": "Eby'okwewunda, akawoowo n'ebiweese by'enviiri",
        "description_pt": "Cosméticos, perfumes e produtos capilares",
        "description_ru": "Косметика, парфюмерия и средства для волос",
        "description_rw": "Ibiribagirisha, imibavu n'ibikoresho by'umusatsi",
        "description_zh": "化妆品、香水与美发产品",
        "description_es": "Cosméticos, perfumes y productos capilares",
        "children": [
            {"slug": "vipodozi", "name_en": "Cosmetics", "name_sw": "Vipodozi", "name_fr": "Cosmétiques", "name_ar": "مستحضرات التجميل", "name_af": "Skoonheidsmiddels", "name_ha": "Kayan Kwalliya", "name_hi": "सौंदर्य प्रसाधन", "name_ja": "化粧品", "name_ko": "화장품", "name_lg": "Eby'Okwewunda", "name_pt": "Cosméticos", "name_ru": "Косметика", "name_rw": "Ibiribagirisha", "name_zh": "化妆品", "name_es": "Cosméticos"},
            {"slug": "manukato", "name_en": "Perfumes", "name_sw": "Manukato", "name_fr": "Parfums", "name_ar": "العطور", "name_af": "Parfuum", "name_ha": "Turare", "name_hi": "इत्र", "name_ja": "香水", "name_ko": "향수", "name_lg": "Akawoowo", "name_pt": "Perfumes", "name_ru": "Парфюмерия", "name_rw": "Imibavu", "name_zh": "香水", "name_es": "Perfumes"},
            {"slug": "bidhaa-nywele", "name_en": "Hair Products", "name_sw": "Bidhaa za Nywele", "name_fr": "Produits capillaires", "name_ar": "منتجات الشعر", "name_af": "Haarprodukte", "name_ha": "Kayayyakin Gashi", "name_hi": "बाल उत्पाद", "name_ja": "ヘアケア製品", "name_ko": "헤어 제품", "name_lg": "Ebiweese by'Enviiri", "name_pt": "Produtos Capilares", "name_ru": "Средства для волос", "name_rw": "Ibikoresho by'Umusatsi", "name_zh": "美发产品", "name_es": "Productos Capilares"},
        ],
    },
    {
        "slug": "afya-dawa",
        "name_en": "Health & Medicine",
        "name_sw": "Afya na Dawa",
        "name_fr": "Santé et médicaments",
        "name_ar": "الصحة والدواء",
        "name_af": "Gesondheid en Medisyne",
        "name_ha": "Lafiya da Magani",
        "name_hi": "स्वास्थ्य और दवा",
        "name_ja": "健康・医薬品",
        "name_ko": "건강 및 의약품",
        "name_lg": "Obulamu n'Eddagala",
        "name_pt": "Saúde e Medicamentos",
        "name_ru": "Здоровье и медицина",
        "name_rw": "Ubuzima n'Imiti",
        "name_zh": "健康与药品",
        "name_es": "Salud y Medicina",
        "description_en": "Medicines and health products",
        "description_sw": "Dawa na bidhaa za afya",
        "description_ar": "الأدوية والمنتجات الصحية",
        "description_af": "Medisyne en gesondheidsprodukte",
        "description_ha": "Magunguna da kayayyakin lafiya",
        "description_hi": "दवाएं और स्वास्थ्य उत्पाद",
        "description_ja": "医薬品と健康製品",
        "description_ko": "의약품 및 건강 제품",
        "description_lg": "Eddagala n'ebiweese by'obulamu",
        "description_pt": "Medicamentos e produtos de saúde",
        "description_ru": "Лекарства и товары для здоровья",
        "description_rw": "Imiti n'ibicuruzwa by'ubuzima",
        "description_zh": "药品与健康产品",
        "description_es": "Medicamentos y productos de salud",
        "children": [
            {"slug": "dawa", "name_en": "Medicines", "name_sw": "Dawa", "name_fr": "Médicaments", "name_ar": "الأدوية", "name_af": "Medisyne", "name_ha": "Magunguna", "name_hi": "दवाएं", "name_ja": "医薬品", "name_ko": "의약품", "name_lg": "Eddagala", "name_pt": "Medicamentos", "name_ru": "Лекарства", "name_rw": "Imiti", "name_zh": "药品", "name_es": "Medicamentos"},
            {"slug": "bidhaa-afya", "name_en": "Health Products", "name_sw": "Bidhaa za Afya", "name_fr": "Produits de santé", "name_ar": "منتجات صحية", "name_af": "Gesondheidsprodukte", "name_ha": "Kayayyakin Lafiya", "name_hi": "स्वास्थ्य उत्पाद", "name_ja": "健康製品", "name_ko": "건강 제품", "name_lg": "Ebiweese by'Obulamu", "name_pt": "Produtos de Saúde", "name_ru": "Товары для здоровья", "name_rw": "Ibicuruzwa by'Ubuzima", "name_zh": "健康产品", "name_es": "Productos de Salud"},
        ],
    },
    {
        "slug": "kilimo-mifugo",
        "name_en": "Agriculture & Livestock",
        "name_sw": "Kilimo na Mifugo",
        "name_fr": "Agriculture et élevage",
        "name_ar": "الزراعة والثروة الحيوانية",
        "name_af": "Landbou en Vee",
        "name_ha": "Noma da Kiwo",
        "name_hi": "कृषि और पशुधन",
        "name_ja": "農業・畜産",
        "name_ko": "농업 및 축산",
        "name_lg": "Awalimi n'Ensolo",
        "name_pt": "Agricultura e Pecuária",
        "name_ru": "Сельское хозяйство и животноводство",
        "name_rw": "Ubuhinzi n'Ubworozi",
        "name_zh": "农业与畜牧",
        "name_es": "Agricultura y Ganadería",
        "description_en": "Seeds, fertilizer and farming/livestock supplies",
        "description_sw": "Mbegu, mbolea na vifaa vya kilimo na ufugaji",
        "description_ar": "البذور والأسمدة ولوازم الزراعة والثروة الحيوانية",
        "description_af": "Saad, kunsmis en boerdery-/veebenodigdhede",
        "description_ha": "Iri, taki da kayan noma/kiwo",
        "description_hi": "बीज, उर्वरक और कृषि/पशुधन सामग्री",
        "description_ja": "種子、肥料、農業・畜産用品",
        "description_ko": "종자, 비료 및 농업/축산 용품",
        "description_lg": "Ensigo, ebigimusa n'ebikozesebwa mu bulimi/obulunzi",
        "description_pt": "Sementes, fertilizantes e suprimentos agrícolas/pecuários",
        "description_ru": "Семена, удобрения и сельскохозяйственные/животноводческие принадлежности",
        "description_rw": "Imbuto, ifumbire n'ibikoresho by'ubuhinzi/ubworozi",
        "description_zh": "种子、肥料及农牧用品",
        "description_es": "Semillas, fertilizantes y suministros agrícolas/ganaderos",
        "children": [
            {"slug": "mbegu-mbolea", "name_en": "Seeds & Fertilizer", "name_sw": "Mbegu na Mbolea", "name_fr": "Semences et engrais", "name_ar": "البذور والأسمدة", "name_af": "Saad en Kunsmis", "name_ha": "Iri da Taki", "name_hi": "बीज और उर्वरक", "name_ja": "種子・肥料", "name_ko": "종자 및 비료", "name_lg": "Ensigo n'Ebigimusa", "name_pt": "Sementes e Fertilizantes", "name_ru": "Семена и удобрения", "name_rw": "Imbuto n'Ifumbire", "name_zh": "种子与肥料", "name_es": "Semillas y Fertilizantes"},
            {"slug": "dawa-kilimo", "name_en": "Agro-chemicals", "name_sw": "Dawa za Kilimo", "name_fr": "Produits agrochimiques", "name_ar": "المواد الكيميائية الزراعية", "name_af": "Landbouchemikalieë", "name_ha": "Sinadaran Noma", "name_hi": "कृषि रसायन", "name_ja": "農薬", "name_ko": "농약", "name_lg": "Eddagala y'Awalimi", "name_pt": "Produtos Agroquímicos", "name_ru": "Агрохимикаты", "name_rw": "Imiti y'Ubuhinzi", "name_zh": "农用化学品", "name_es": "Agroquímicos"},
            {"slug": "vifaa-kilimo", "name_en": "Farm Equipment", "name_sw": "Vifaa vya Kilimo", "name_fr": "Équipement agricole", "name_ar": "معدات المزرعة", "name_af": "Plaastoerusting", "name_ha": "Kayan Aikin Gona", "name_hi": "कृषि उपकरण", "name_ja": "農業機器", "name_ko": "농기구", "name_lg": "Ebyuma by'Awalimi", "name_pt": "Equipamentos Agrícolas", "name_ru": "Сельхозтехника", "name_rw": "Ibikoresho by'Ubuhinzi", "name_zh": "农业设备", "name_es": "Equipos Agrícolas"},
        ],
    },
    {
        "slug": "zana-vifaa-kazi",
        "name_en": "Tools & Equipment",
        "name_sw": "Zana na Vifaa vya Kazi",
        "name_fr": "Outils et équipement",
        "name_ar": "الأدوات والمعدات",
        "name_af": "Gereedskap en Toerusting",
        "name_ha": "Kayan Aiki",
        "name_hi": "उपकरण और सामग्री",
        "name_ja": "工具・機材",
        "name_ko": "도구 및 장비",
        "name_lg": "Ebikozesebwa n'Ebyuma",
        "name_pt": "Ferramentas e Equipamentos",
        "name_ru": "Инструменты и оборудование",
        "name_rw": "Ibikoresho n'Ibyuma",
        "name_zh": "工具与设备",
        "name_es": "Herramientas y Equipos",
        "description_en": "Construction and artisan tools",
        "description_sw": "Zana za ujenzi na za mafundi",
        "description_ar": "أدوات البناء وأدوات الحرفيين",
        "description_af": "Konstruksie- en ambagsgereedskap",
        "description_ha": "Kayan aikin gini da na sana'a",
        "description_hi": "निर्माण और शिल्प उपकरण",
        "description_ja": "建設・職人用工具",
        "description_ko": "건설 및 공예 도구",
        "description_lg": "Ebikozesebwa mu kuzimba n'eby'emikono",
        "description_pt": "Ferramentas de construção e artesanato",
        "description_ru": "Строительные и ремесленные инструменты",
        "description_rw": "Ibikoresho by'ubwubatsi n'ubukorikori",
        "description_zh": "建筑与工匠工具",
        "description_es": "Herramientas de construcción y artesanía",
        "children": [
            {"slug": "zana-ujenzi", "name_en": "Construction Tools", "name_sw": "Zana za Ujenzi", "name_fr": "Outils de construction", "name_ar": "أدوات البناء", "name_af": "Konstruksiegereedskap", "name_ha": "Kayan Aikin Gini", "name_hi": "निर्माण उपकरण", "name_ja": "建設工具", "name_ko": "건설 도구", "name_lg": "Ebikozesebwa mu Kuzimba", "name_pt": "Ferramentas de Construção", "name_ru": "Строительные инструменты", "name_rw": "Ibikoresho by'Ubwubatsi", "name_zh": "建筑工具", "name_es": "Herramientas de Construcción"},
            {"slug": "zana-mafundi", "name_en": "Artisan Tools", "name_sw": "Zana za Mafundi", "name_fr": "Outils d'artisan", "name_ar": "أدوات الحرفيين", "name_af": "Ambagsgereedskap", "name_ha": "Kayan Aikin Sana'a", "name_hi": "शिल्प उपकरण", "name_ja": "職人用工具", "name_ko": "공예 도구", "name_lg": "Ebikozesebwa eby'Emikono", "name_pt": "Ferramentas de Artesão", "name_ru": "Ремесленные инструменты", "name_rw": "Ibikoresho by'Ubukorikori", "name_zh": "工匠工具", "name_es": "Herramientas de Artesano"},
        ],
    },
    {
        "slug": "huduma",
        "name_en": "Services",
        "name_sw": "Huduma",
        "name_fr": "Services",
        "name_ar": "الخدمات",
        "name_af": "Dienste",
        "name_ha": "Ayyuka",
        "name_hi": "सेवाएं",
        "name_ja": "サービス",
        "name_ko": "서비스",
        "name_lg": "Obuweereza",
        "name_pt": "Serviços",
        "name_ru": "Услуги",
        "name_rw": "Serivisi",
        "name_zh": "服务",
        "name_es": "Servicios",
        "description_en": "Repair, cleaning and skilled trade services",
        "description_sw": "Huduma za ukarabati, usafi na ufundi",
        "description_ar": "خدمات الإصلاح والتنظيف والحرف المهنية",
        "description_af": "Herstel-, skoonmaak- en vakkundige dienste",
        "description_ha": "Ayyukan gyara, tsaftacewa da sana'ar hannu",
        "description_hi": "मरम्मत, सफाई और कुशल व्यापार सेवाएं",
        "description_ja": "修理、清掃、専門技能サービス",
        "description_ko": "수리, 청소 및 숙련 기술 서비스",
        "description_lg": "Obuweereza bw'okuddaabiriza, okwerongoosa n'obukugu",
        "description_pt": "Serviços de reparo, limpeza e ofícios especializados",
        "description_ru": "Услуги по ремонту, уборке и квалифицированные ремесленные услуги",
        "description_rw": "Serivisi zo gusana, gusukura n'imyuga",
        "description_zh": "维修、清洁与技术服务",
        "description_es": "Servicios de reparación, limpieza y oficios especializados",
        "children": [
            {"slug": "huduma-ukarabati", "name_en": "Repair Services", "name_sw": "Huduma za Ukarabati", "name_fr": "Services de réparation", "name_ar": "خدمات الإصلاح", "name_af": "Herstelldienste", "name_ha": "Ayyukan Gyara", "name_hi": "मरम्मत सेवाएं", "name_ja": "修理サービス", "name_ko": "수리 서비스", "name_lg": "Obuweereza bw'Okuddaabiriza", "name_pt": "Serviços de Reparo", "name_ru": "Услуги по ремонту", "name_rw": "Serivisi zo Gusana", "name_zh": "维修服务", "name_es": "Servicios de Reparación"},
            {"slug": "huduma-usafi", "name_en": "Cleaning Services", "name_sw": "Huduma za Usafi", "name_fr": "Services de nettoyage", "name_ar": "خدمات التنظيف", "name_af": "Skoonmaakdienste", "name_ha": "Ayyukan Tsaftacewa", "name_hi": "सफाई सेवाएं", "name_ja": "清掃サービス", "name_ko": "청소 서비스", "name_lg": "Obuweereza bw'Okwerongoosa", "name_pt": "Serviços de Limpeza", "name_ru": "Клининговые услуги", "name_rw": "Serivisi zo Gusukura", "name_zh": "清洁服务", "name_es": "Servicios de Limpieza"},
            {"slug": "huduma-ufundi", "name_en": "Skilled Trade Services", "name_sw": "Huduma za Ufundi", "name_fr": "Services d'artisanat", "name_ar": "خدمات الحرف المهنية", "name_af": "Vakkundige Dienste", "name_ha": "Ayyukan Sana'a", "name_hi": "कुशल व्यापार सेवाएं", "name_ja": "専門技能サービス", "name_ko": "숙련 기술 서비스", "name_lg": "Obuweereza bw'Obukugu", "name_pt": "Serviços de Ofícios Especializados", "name_ru": "Услуги квалифицированных мастеров", "name_rw": "Serivisi z'Imyuga", "name_zh": "技术服务", "name_es": "Servicios de Oficios Especializados"},
        ],
    },
    {
        "slug": "vitabu-elimu",
        "name_en": "Books & Stationery",
        "name_sw": "Vitabu na Vifaa vya Elimu",
        "name_fr": "Livres et papeterie",
        "name_ar": "الكتب والقرطاسية",
        "name_af": "Boeke en Skryfbehoeftes",
        "name_ha": "Littattafai da Kayan Rubutu",
        "name_hi": "पुस्तकें और स्टेशनरी",
        "name_ja": "書籍・文房具",
        "name_ko": "도서 및 문구",
        "name_lg": "Ebitabo n'Ebyokuwandiikira",
        "name_pt": "Livros e Papelaria",
        "name_ru": "Книги и канцтовары",
        "name_rw": "Ibitabo n'Ibikoresho by'Ishuri",
        "name_zh": "图书与文具",
        "name_es": "Libros y Papelería",
        "description_en": "Books, stationery and school supplies",
        "description_sw": "Vitabu, vifaa vya ofisi na shule",
        "description_ar": "الكتب والقرطاسية ومستلزمات المدرسة",
        "description_af": "Boeke, skryfbehoeftes en skoolbenodigdhede",
        "description_ha": "Littattafai, kayan rubutu da kayan makaranta",
        "description_hi": "पुस्तकें, स्टेशनरी और स्कूल की आपूर्ति",
        "description_ja": "書籍、文房具、学用品",
        "description_ko": "도서, 문구 및 학용품",
        "description_lg": "Ebitabo, ebyokuwandiikira n'ebikozesebwa ku ssomero",
        "description_pt": "Livros, papelaria e material escolar",
        "description_ru": "Книги, канцтовары и школьные принадлежности",
        "description_rw": "Ibitabo, ibikoresho byo kwandika n'ibikoresho by'ishuri",
        "description_zh": "图书、文具与学习用品",
        "description_es": "Libros, papelería y útiles escolares",
        "children": [],
    },
    {
        "slug": "michezo-burudani",
        "name_en": "Sports & Entertainment",
        "name_sw": "Michezo na Burudani",
        "name_fr": "Sport et loisirs",
        "name_ar": "الرياضة والترفيه",
        "name_af": "Sport en Vermaak",
        "name_ha": "Wasanni da Nishadi",
        "name_hi": "खेल और मनोरंजन",
        "name_ja": "スポーツ・娯楽",
        "name_ko": "스포츠 및 엔터테인먼트",
        "name_lg": "Emizannyo n'Eby'Okusanyusa",
        "name_pt": "Esportes e Entretenimento",
        "name_ru": "Спорт и развлечения",
        "name_rw": "Imikino n'Imyidagaduro",
        "name_zh": "体育与娱乐",
        "name_es": "Deportes y Entretenimiento",
        "description_en": "Sporting goods and entertainment items",
        "description_sw": "Bidhaa za michezo na burudani",
        "description_ar": "أدوات رياضية ومستلزمات ترفيهية",
        "description_af": "Sportartikels en vermaakitems",
        "description_ha": "Kayan wasanni da nishadi",
        "description_hi": "खेल का सामान और मनोरंजन की वस्तुएं",
        "description_ja": "スポーツ用品と娯楽品",
        "description_ko": "스포츠 용품 및 엔터테인먼트 상품",
        "description_lg": "Ebikozesebwa mu mizannyo n'eby'okusanyusa",
        "description_pt": "Artigos esportivos e itens de entretenimento",
        "description_ru": "Спортивные товары и предметы для развлечений",
        "description_rw": "Ibikoresho by'imikino n'ibintu byo kwidagadura",
        "description_zh": "体育用品与娱乐产品",
        "description_es": "Artículos deportivos y de entretenimiento",
        "children": [],
    },
]


class Command(BaseCommand):
    help = "Seed Product Categories with translations and hierarchy"

    LANGUAGES = ['sw', 'fr', 'ar', 'af', 'ha', 'hi', 'ja', 'ko', 'lg', 'pt', 'ru', 'rw', 'zh', 'es']
    TRANSLATABLE_FIELDS = ['name', 'description']

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Dry run: show what would be created without actually creating')
        parser.add_argument('--verbose', action='store_true', help='Show detailed output')
        parser.add_argument('--categories', nargs='+', type=str, help='Specific category slugs to seed')
        parser.add_argument('--clear', action='store_true', help='Clear existing categories before seeding (use with caution)')
        parser.add_argument('--skip-existing', action='store_true', help='Skip existing categories instead of updating them')

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.verbose = options['verbose']
        self.skip_existing = options['skip_existing']

        if self.dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN MODE - No changes will be made"))
            self.stdout.write("=" * 60)

        if options['clear'] and not self.dry_run:
            self.clear_categories()

        categories_to_seed = self.filter_categories(options.get('categories'))

        start_time = timezone.now()
        stats = self.seed_categories(categories_to_seed)
        end_time = timezone.now()

        self.print_summary(stats, end_time - start_time, self.dry_run)

    def filter_categories(self, slug_list: Optional[List[str]]) -> List[Dict]:
        if not slug_list:
            return CATEGORIES

        filtered = []
        for cat in CATEGORIES:
            if cat['slug'] in slug_list:
                filtered.append(cat)
            else:
                children = cat.get('children', [])
                filtered_children = [c for c in children if c['slug'] in slug_list]
                if filtered_children:
                    cat_copy = cat.copy()
                    cat_copy['children'] = filtered_children
                    filtered.append(cat_copy)

        if not filtered:
            self.stdout.write(self.style.WARNING(f"No categories found for slugs: {', '.join(slug_list)}"))

        return filtered

    def clear_categories(self):
        self.stdout.write(self.style.WARNING("Clearing all existing product categories..."))
        count = ProductCategory.objects.count()
        ProductCategory.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"✅ Deleted {count} categories"))

    @transaction.atomic
    def seed_categories(self, categories: List[Dict], parent: Optional[ProductCategory] = None,
                         depth: int = 0, stats: Optional[Dict] = None) -> Dict:
        if stats is None:
            stats = {'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0}

        indent = "  " * depth

        for data in categories:
            try:
                self.validate_category_data(data)

                exists = ProductCategory.objects.filter(slug=data["slug"]).exists()

                if exists and self.skip_existing and not self.dry_run:
                    stats['skipped'] += 1
                    if self.verbose:
                        self.stdout.write(f"{indent}⏭️  Skipped: {data['slug']}")
                    continue

                if self.dry_run:
                    action = "Would create" if not exists else "Would update"
                    self.stdout.write(f"{indent}{action}: {data['slug']}")
                    stats['created' if not exists else 'updated'] += 1
                else:
                    category, created = self.create_or_update_category(data, parent)
                    if created:
                        stats['created'] += 1
                        self.stdout.write(self.style.SUCCESS(f"{indent}✅ Created: {data['slug']}"))
                    else:
                        stats['updated'] += 1
                        if self.verbose:
                            self.stdout.write(self.style.SUCCESS(f"{indent}🔄 Updated: {data['slug']}"))

                children = data.get("children", [])
                if children:
                    self.seed_categories(
                        children,
                        parent=None if self.dry_run else category,
                        depth=depth + 1,
                        stats=stats,
                    )

            except Exception as e:
                stats['errors'] += 1
                error_msg = f"Error seeding {data.get('slug', 'unknown')}: {str(e)}"
                self.stderr.write(self.style.ERROR(f"{indent}❌ {error_msg}"))
                logger.error(error_msg, exc_info=True)

                if not self.dry_run:
                    raise CommandError(f"Seeding failed: {error_msg}")

        return stats

    def validate_category_data(self, data: Dict):
        required_fields = ['slug', 'name_en']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: '{field}'")

        slug = data['slug']
        if not slug.replace('-', '').replace('_', '').isalnum():
            raise ValueError(f"Invalid slug format: '{slug}'. Use only letters, numbers, hyphens and underscores.")

        if 'children' in data:
            child_slugs = [c['slug'] for c in data['children']]
            if len(child_slugs) != len(set(child_slugs)):
                raise ValueError(f"Duplicate child slugs found in {slug}")

        return True

    def create_or_update_category(self, data: Dict, parent: Optional[ProductCategory] = None) -> tuple:
        defaults = {
            "parent": parent,
            "name": data.get("name_en"),
            "description": data.get("description_en", ""),
        }

        category, created = ProductCategory.objects.update_or_create(
            slug=data["slug"],
            defaults=defaults,
        )

        for field in self.TRANSLATABLE_FIELDS:
            for lang in self.LANGUAGES:
                key = f"{field}_{lang}"
                if key in data:
                    setattr(category, key, data[key])

        category.save()

        return category, created

    def print_summary(self, stats: Dict, duration, dry_run: bool):
        self.stdout.write("=" * 60)

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN SUMMARY"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ SEEDING COMPLETED"))

        self.stdout.write("Categories:")
        self.stdout.write(f"  ✅ Created:  {stats.get('created', 0)}")
        self.stdout.write(f"  🔄 Updated:  {stats.get('updated', 0)}")
        self.stdout.write(f"  ⏭️ Skipped:  {stats.get('skipped', 0)}")

        if stats.get('errors', 0) > 0:
            self.stdout.write(self.style.ERROR(f"  ❌ Errors:   {stats.get('errors', 0)}"))
        else:
            self.stdout.write("  ✅ Errors:   0")

        self.stdout.write(f"⏱️ Time: {duration.total_seconds():.2f} seconds")

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN - No changes were made"))
        else:
            total = ProductCategory.objects.count()
            self.stdout.write(self.style.SUCCESS(f"📊 Total categories in DB: {total}"))
