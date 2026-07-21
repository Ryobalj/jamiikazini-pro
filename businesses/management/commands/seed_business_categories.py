# businesses/management/commands/seed_business_categories.py

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from businesses.models.category import BusinessCategory
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

# =====================================================
# CATEGORIES DATA - Bila Icon field
# =====================================================

CATEGORIES = [
    # AGRICULTURE
    {
        "slug": "agriculture",
        "name_en": "Agriculture",
        "name_sw": "Kilimo",
        "name_fr": "Agriculture",
        "name_ar": "الزراعة",
        "name_af": "Landbou",
        "name_ha": "Aikin Gona",
        "name_hi": "कृषि",
        "name_ja": "農業",
        "name_ko": "농업",
        "name_lg": "Awalimi",
        "name_pt": "Agricultura",
        "name_ru": "Сельское хозяйство",
        "name_rw": "Ubuhinzi",
        "name_zh": "农业",
        "name_es": "Agricultura",
        "description_en": "Farming, crop production and livestock keeping",
        "description_sw": "Kilimo, uzalishaji wa mazao na ufugaji",
        "description_fr": "Agriculture, production végétale et élevage",
        "description_ar": "الزراعة وإنتاج المحاصيل وتربية الماشية",
        "description_af": "Boerdery, gewasproduksie en veeboerdery",
        "description_ha": "Noma, samar da amfanin gona da kiwon dabbobi",
        "description_hi": "खेती, फसल उत्पादन और पशुपालन",
        "description_ja": "農業、作物生産、畜産",
        "description_ko": "농업, 작물 생산 및 축산업",
        "description_lg": "Awalimi, okulima ebirime n'okulunda ensolo",
        "description_pt": "Agricultura, produção de culturas e pecuária",
        "description_ru": "Земледелие, растениеводство и животноводство",
        "description_rw": "Ubuhinzi, gutunganya ibihingwa n'ubworozi",
        "description_zh": "农业种植与畜牧养殖",
        "description_es": "Agricultura, producción de cultivos y ganadería",
        "children": [
            {
                "slug": "crop-production",
                "name_en": "Crop Production",
                "name_sw": "Uzalishaji wa Mazao",
                "name_fr": "Production végétale",
                "name_ar": "إنتاج المحاصيل",
                "name_af": "Gewasproduksie",
                "name_ha": "Samar da Amfanin Gona",
                "name_hi": "फसल उत्पादन",
                "name_ja": "作物生産",
                "name_ko": "작물 생산",
                "name_lg": "Okulima Ebirime",
                "name_pt": "Produção de Culturas",
                "name_ru": "Растениеводство",
                "name_rw": "Gutunganya Ibihingwa",
                "name_zh": "农作物生产",
                "name_es": "Producción de Cultivos",
                "description_en": "Growing crops for food and commercial purposes",
                "description_sw": "Kulima mazao ya chakula na biashara",
                "description_ar": "زراعة المحاصيل للأغراض الغذائية والتجارية",
                "description_af": "Verbouing van gewasse vir voedsel en kommersiële doeleindes",
                "description_ha": "Noman amfanin gona don abinci da manufofin kasuwanci",
                "description_hi": "भोजन और व्यावसायिक उद्देश्यों के लिए फसलें उगाना",
                "description_ja": "食用および商業目的での作物栽培",
                "description_ko": "식량 및 상업적 목적을 위한 작물 재배",
                "description_lg": "Okulima ebirime okulya n'okusuubula",
                "description_pt": "Cultivo de plantações para fins alimentares e comerciais",
                "description_ru": "Выращивание сельскохозяйственных культур для продовольственных и коммерческих целей",
                "description_rw": "Guhinga ibihingwa mu buryo bwo kurya no gucuruza",
                "description_zh": "为食品和商业用途种植农作物",
                "description_es": "Cultivo de plantas con fines alimentarios y comerciales",
                "children": [
                    {
                        "slug": "grain-farming",
                        "name_en": "Grain Farming",
                        "name_sw": "Kilimo cha Nafaka",
                        "name_fr": "Culture céréalière",
                        "name_ar": "زراعة الحبوب",
                        "name_af": "Graanboerdery",
                        "name_ha": "Noman Hatsi",
                        "name_hi": "अनाज की खेती",
                        "name_ja": "穀物栽培",
                        "name_ko": "곡물 재배",
                        "name_lg": "Okulima Empeke",
                        "name_pt": "Cultivo de Grãos",
                        "name_ru": "Зерновое хозяйство",
                        "name_rw": "Guhinga Ibinyampeke",
                        "name_zh": "谷物种植",
                        "name_es": "Cultivo de Granos",
                    },
                    {
                        "slug": "horticulture",
                        "name_en": "Horticulture",
                        "name_sw": "Kilimo cha Mboga na Matunda",
                        "name_fr": "Horticulture",
                        "name_ar": "البستنة",
                        "name_af": "Tuinbou",
                        "name_ha": "Noman Lambu",
                        "name_hi": "बागवानी",
                        "name_ja": "園芸",
                        "name_ko": "원예",
                        "name_lg": "Okulima Enva Endiirwa",
                        "name_pt": "Horticultura",
                        "name_ru": "Садоводство",
                        "name_rw": "Ubworozi bw'Imboga n'Imbuto",
                        "name_zh": "园艺种植",
                        "name_es": "Horticultura",
                    },
                    {
                        "slug": "cash-crops",
                        "name_en": "Cash Crops",
                        "name_sw": "Mazao ya Biashara",
                        "name_fr": "Cultures de rente",
                        "name_ar": "المحاصيل النقدية",
                        "name_af": "Kontantgewasse",
                        "name_ha": "Amfanin Gonar Kudi",
                        "name_hi": "नकदी फसलें",
                        "name_ja": "商品作物",
                        "name_ko": "환금 작물",
                        "name_lg": "Ebirime by'Ebyensimbi",
                        "name_pt": "Culturas Comerciais",
                        "name_ru": "Товарные культуры",
                        "name_rw": "Ibihingwa by'Ubucuruzi",
                        "name_zh": "经济作物",
                        "name_es": "Cultivos Comerciales",
                    },
                ]
            },
            {
                "slug": "livestock",
                "name_en": "Livestock Farming",
                "name_sw": "Ufugaji",
                "name_fr": "Élevage",
                "name_ar": "تربية الماشية",
                "name_af": "Veeboerdery",
                "name_ha": "Kiwon Dabbobi",
                "name_hi": "पशुपालन",
                "name_ja": "畜産業",
                "name_ko": "축산업",
                "name_lg": "Okulunda Ensolo",
                "name_pt": "Pecuária",
                "name_ru": "Животноводство",
                "name_rw": "Ubworozi",
                "name_zh": "畜牧养殖",
                "name_es": "Ganadería",
                "description_en": "Raising animals for food, fiber and other products",
                "description_sw": "Ufugaji wa wanyama kwa ajili ya chakula na bidhaa nyingine",
                "description_ar": "تربية الحيوانات لإنتاج الغذاء والألياف ومنتجات أخرى",
                "description_af": "Diereteelt vir voedsel, vesel en ander produkte",
                "description_ha": "Kiwon dabbobi don abinci, zare da sauran kayayyaki",
                "description_hi": "भोजन, फाइबर और अन्य उत्पादों के लिए पशुपालन",
                "description_ja": "食用、繊維、その他の製品のための動物飼育",
                "description_ko": "식품, 섬유 및 기타 제품을 위한 동물 사육",
                "description_lg": "Okulunda ensolo okufuna emmere, ebyuma n'ebintu ebirala",
                "description_pt": "Criação de animais para alimentos, fibras e outros produtos",
                "description_ru": "Разведение животных для получения продовольствия, волокна и других продуктов",
                "description_rw": "Korora amatungo kugira ngo habeho ibiribwa, ibintu byo kudoda n'ibindi bicuruzwa",
                "description_zh": "为获取食品、纤维及其他产品而饲养动物",
                "description_es": "Cría de animales para alimentos, fibra y otros productos",
                "children": [
                    {
                        "slug": "poultry",
                        "name_en": "Poultry Farming",
                        "name_sw": "Ufugaji wa Kuku",
                        "name_fr": "Aviculture",
                        "name_ar": "تربية الدواجن",
                        "name_af": "Pluimveeboerdery",
                        "name_ha": "Kiwon Kaji",
                        "name_hi": "मुर्गी पालन",
                        "name_ja": "養鶏",
                        "name_ko": "양계업",
                        "name_lg": "Okulunda Enkoko",
                        "name_pt": "Avicultura",
                        "name_ru": "Птицеводство",
                        "name_rw": "Ubworozi bw'Inkoko",
                        "name_zh": "家禽养殖",
                        "name_es": "Avicultura",
                    },
                    {
                        "slug": "dairy",
                        "name_en": "Dairy Farming",
                        "name_sw": "Ufugaji wa Maziwa",
                        "name_fr": "Élevage laitier",
                        "name_ar": "تربية الألبان",
                        "name_af": "Suiwelboerdery",
                        "name_ha": "Kiwon Shanun Nono",
                        "name_hi": "डेयरी फार्मिंग",
                        "name_ja": "酪農",
                        "name_ko": "낙농업",
                        "name_lg": "Okulunda Ente ez'Amata",
                        "name_pt": "Pecuária Leiteira",
                        "name_ru": "Молочное животноводство",
                        "name_rw": "Ubworozi bw'Amata",
                        "name_zh": "奶牛养殖",
                        "name_es": "Ganadería Lechera",
                    },
                    {
                        "slug": "goat-farming",
                        "name_en": "Goat Farming",
                        "name_sw": "Ufugaji wa Mbuzi",
                        "name_fr": "Élevage de chèvres",
                        "name_ar": "تربية الماعز",
                        "name_af": "Bokboerdery",
                        "name_ha": "Kiwon Awaki",
                        "name_hi": "बकरी पालन",
                        "name_ja": "ヤギ飼育",
                        "name_ko": "염소 사육",
                        "name_lg": "Okulunda Embuzi",
                        "name_pt": "Criação de Cabras",
                        "name_ru": "Козоводство",
                        "name_rw": "Ubworozi bw'Ihene",
                        "name_zh": "山羊养殖",
                        "name_es": "Cría de Cabras",
                    },
                ]
            }
        ]
    },

    # TRADE & COMMERCE
    {
        "slug": "trade-commerce",
        "name_en": "Trade & Commerce",
        "name_sw": "Biashara na Uchumi",
        "name_fr": "Commerce",
        "name_ar": "التجارة والأعمال",
        "name_af": "Handel en Kommersie",
        "name_ha": "Kasuwanci da Ciniki",
        "name_hi": "व्यापार और वाणिज्य",
        "name_ja": "貿易・商業",
        "name_ko": "무역 및 상업",
        "name_lg": "Obusuubuzi",
        "name_pt": "Comércio",
        "name_ru": "Торговля и коммерция",
        "name_rw": "Ubucuruzi n'Ubukungu",
        "name_zh": "贸易与商业",
        "name_es": "Comercio",
        "description_en": "Buying and selling of goods and services",
        "description_sw": "Kununua na kuuza bidhaa na huduma",
        "description_ar": "بيع وشراء السلع والخدمات",
        "description_af": "Koop en verkoop van goedere en dienste",
        "description_ha": "Sayarwa da sayen kayayyaki da ayyuka",
        "description_hi": "वस्तुओं और सेवाओं की खरीद और बिक्री",
        "description_ja": "商品とサービスの売買",
        "description_ko": "상품 및 서비스의 매매",
        "description_lg": "Okugula n'okutunda ebintu n'obuweereza",
        "description_pt": "Compra e venda de bens e serviços",
        "description_ru": "Купля и продажа товаров и услуг",
        "description_rw": "Kugura no kugurisha ibicuruzwa n'imirimo",
        "description_zh": "商品与服务的买卖",
        "description_es": "Compra y venta de bienes y servicios",
        "children": [
            {
                "slug": "retail",
                "name_en": "Retail Trade",
                "name_sw": "Rejareja",
                "name_fr": "Commerce de détail",
                "name_ar": "تجارة التجزئة",
                "name_af": "Kleinhandel",
                "name_ha": "Kasuwancin Dillanci",
                "name_hi": "खुदरा व्यापार",
                "name_ja": "小売業",
                "name_ko": "소매업",
                "name_lg": "Obusuubuzi bwa Rejareja",
                "name_pt": "Comércio Varejista",
                "name_ru": "Розничная торговля",
                "name_rw": "Ubucuruzi bwo mu Rutonde",
                "name_zh": "零售贸易",
                "name_es": "Comercio Minorista",
            },
            {
                "slug": "wholesale",
                "name_en": "Wholesale Trade",
                "name_sw": "Biashara ya Jumla",
                "name_fr": "Commerce de gros",
                "name_ar": "تجارة الجملة",
                "name_af": "Groothandel",
                "name_ha": "Kasuwancin Jumla",
                "name_hi": "थोक व्यापार",
                "name_ja": "卸売業",
                "name_ko": "도매업",
                "name_lg": "Obusuubuzi bwa Jumla",
                "name_pt": "Comércio Atacadista",
                "name_ru": "Оптовая торговля",
                "name_rw": "Ubucuruzi bwa Njumla",
                "name_zh": "批发贸易",
                "name_es": "Comercio Mayorista",
            },
            {
                "slug": "ecommerce",
                "name_en": "E-Commerce",
                "name_sw": "Biashara Mtandao",
                "name_fr": "Commerce électronique",
                "name_ar": "التجارة الإلكترونية",
                "name_af": "E-handel",
                "name_ha": "Kasuwanci ta Yanar Gizo",
                "name_hi": "ई-कॉमर्स",
                "name_ja": "電子商取引",
                "name_ko": "전자상거래",
                "name_lg": "Obusuubuzi bwa Yintaneeti",
                "name_pt": "Comércio Eletrônico",
                "name_ru": "Электронная коммерция",
                "name_rw": "Ubucuruzi bwa Interineti",
                "name_zh": "电子商务",
                "name_es": "Comercio Electrónico",
            },
        ]
    },

    # TECHNOLOGY
    {
        "slug": "technology",
        "name_en": "Technology",
        "name_sw": "Teknolojia",
        "name_fr": "Technologie",
        "name_ar": "التكنولوجيا",
        "name_af": "Tegnologie",
        "name_ha": "Fasaha",
        "name_hi": "प्रौद्योगिकी",
        "name_ja": "テクノロジー",
        "name_ko": "기술",
        "name_lg": "Tekinologiya",
        "name_pt": "Tecnologia",
        "name_ru": "Технологии",
        "name_rw": "Ikoranabuhanga",
        "name_zh": "技术",
        "name_es": "Tecnología",
        "description_en": "Digital solutions, software and IT services",
        "description_sw": "Suluhisho za kidijitali, programu na huduma za TEHAMA",
        "description_ar": "الحلول الرقمية والبرمجيات وخدمات تقنية المعلومات",
        "description_af": "Digitale oplossings, sagteware en IT-dienste",
        "description_ha": "Hanyoyin dijital, software da ayyukan IT",
        "description_hi": "डिजिटल समाधान, सॉफ्टवेयर और आईटी सेवाएं",
        "description_ja": "デジタルソリューション、ソフトウェア、IT サービス",
        "description_ko": "디지털 솔루션, 소프트웨어 및 IT 서비스",
        "description_lg": "Ebikolwa bya digito, sofuwea n'obuweereza bwa IT",
        "description_pt": "Soluções digitais, software e serviços de TI",
        "description_ru": "Цифровые решения, программное обеспечение и ИТ-услуги",
        "description_rw": "Ibisubizo bya digitale, porogaramu n'imirimo ya IT",
        "description_zh": "数字化解决方案、软件与IT服务",
        "description_es": "Soluciones digitales, software y servicios de TI",
        "children": [
            {
                "slug": "software-development",
                "name_en": "Software Development",
                "name_sw": "Utengenezaji wa Programu",
                "name_fr": "Développement logiciel",
                "name_ar": "تطوير البرمجيات",
                "name_af": "Sagteware-ontwikkeling",
                "name_ha": "Kirkirar Software",
                "name_hi": "सॉफ्टवेयर विकास",
                "name_ja": "ソフトウェア開発",
                "name_ko": "소프트웨어 개발",
                "name_lg": "Okukola Sofuwea",
                "name_pt": "Desenvolvimento de Software",
                "name_ru": "Разработка программного обеспечения",
                "name_rw": "Gukora Porogaramu",
                "name_zh": "软件开发",
                "name_es": "Desarrollo de Software",
            },
            {
                "slug": "it-services",
                "name_en": "IT Services",
                "name_sw": "Huduma za TEHAMA",
                "name_fr": "Services informatiques",
                "name_ar": "خدمات تقنية المعلومات",
                "name_af": "IT-dienste",
                "name_ha": "Ayyukan IT",
                "name_hi": "आईटी सेवाएं",
                "name_ja": "ITサービス",
                "name_ko": "IT 서비스",
                "name_lg": "Obuweereza bwa IT",
                "name_pt": "Serviços de TI",
                "name_ru": "ИТ-услуги",
                "name_rw": "Serivisi za IT",
                "name_zh": "IT服务",
                "name_es": "Servicios de TI",
            },
            {
                "slug": "telecommunications",
                "name_en": "Telecommunications",
                "name_sw": "Mawasiliano",
                "name_fr": "Télécommunications",
                "name_ar": "الاتصالات",
                "name_af": "Telekommunikasie",
                "name_ha": "Sadarwa",
                "name_hi": "दूरसंचार",
                "name_ja": "電気通信",
                "name_ko": "통신",
                "name_lg": "Empuliziganya",
                "name_pt": "Telecomunicações",
                "name_ru": "Телекоммуникации",
                "name_rw": "Itumanaho",
                "name_zh": "电信",
                "name_es": "Telecomunicaciones",
            },
        ]
    },

    # HEALTH
    {
        "slug": "healthcare",
        "name_en": "Healthcare",
        "name_sw": "Afya",
        "name_fr": "Santé",
        "name_ar": "الرعاية الصحية",
        "name_af": "Gesondheidsorg",
        "name_ha": "Kiwon Lafiya",
        "name_hi": "स्वास्थ्य देखभाल",
        "name_ja": "医療",
        "name_ko": "의료",
        "name_lg": "Eby'Obulamu",
        "name_pt": "Saúde",
        "name_ru": "Здравоохранение",
        "name_rw": "Ubuzima",
        "name_zh": "医疗保健",
        "name_es": "Atención Médica",
        "description_en": "Medical services, health facilities and wellness",
        "description_sw": "Huduma za matibabu, vituo vya afya na ustawi",
        "description_ar": "الخدمات الطبية والمرافق الصحية والعافية",
        "description_af": "Mediese dienste, gesondheidsfasiliteite en welstand",
        "description_ha": "Ayyukan likita, cibiyoyin kiwon lafiya da lafiyar jiki",
        "description_hi": "चिकित्सा सेवाएं, स्वास्थ्य सुविधाएं और स्वास्थ्य",
        "description_ja": "医療サービス、医療施設、健康管理",
        "description_ko": "의료 서비스, 의료 시설 및 건강 관리",
        "description_lg": "Obuweereza bw'obujjanjabi, amayumba g'obulamu n'obulungi bw'omubiri",
        "description_pt": "Serviços médicos, instalações de saúde e bem-estar",
        "description_ru": "Медицинские услуги, медицинские учреждения и оздоровление",
        "description_rw": "Serivisi z'ubuvuzi, ibigo by'ubuzima n'ubuzima bwiza",
        "description_zh": "医疗服务、医疗设施与健康保健",
        "description_es": "Servicios médicos, instalaciones de salud y bienestar",
        "children": [
            {
                "slug": "clinics",
                "name_en": "Clinics",
                "name_sw": "Kliniki",
                "name_fr": "Cliniques",
                "name_ar": "العيادات",
                "name_af": "Klinieke",
                "name_ha": "Asibitoci",
                "name_hi": "क्लीनिक",
                "name_ja": "クリニック",
                "name_ko": "클리닉",
                "name_lg": "Ebipimo",
                "name_pt": "Clínicas",
                "name_ru": "Клиники",
                "name_rw": "Amavuriro",
                "name_zh": "诊所",
                "name_es": "Clínicas",
            },
            {
                "slug": "pharmacies",
                "name_en": "Pharmacies",
                "name_sw": "Maduka ya Dawa",
                "name_fr": "Pharmacies",
                "name_ar": "الصيدليات",
                "name_af": "Apteke",
                "name_ha": "Kantunan Magani",
                "name_hi": "फार्मेसी",
                "name_ja": "薬局",
                "name_ko": "약국",
                "name_lg": "Amaduuka g'Eddagala",
                "name_pt": "Farmácias",
                "name_ru": "Аптеки",
                "name_rw": "Farumasi",
                "name_zh": "药店",
                "name_es": "Farmacias",
            },
            {
                "slug": "diagnostic-centers",
                "name_en": "Diagnostic Centers",
                "name_sw": "Vituo vya Vipimo",
                "name_fr": "Centres de diagnostic",
                "name_ar": "مراكز التشخيص",
                "name_af": "Diagnostiese Sentrums",
                "name_ha": "Cibiyoyin Bincike",
                "name_hi": "नैदानिक केंद्र",
                "name_ja": "検査センター",
                "name_ko": "진단 센터",
                "name_lg": "Ebifo by'Okukebera",
                "name_pt": "Centros de Diagnóstico",
                "name_ru": "Диагностические центры",
                "name_rw": "Ibigo by'Isuzuma",
                "name_zh": "诊断中心",
                "name_es": "Centros de Diagnóstico",
            },
        ]
    },

    # EDUCATION
    {
        "slug": "education",
        "name_en": "Education",
        "name_sw": "Elimu",
        "name_fr": "Éducation",
        "name_ar": "التعليم",
        "name_af": "Onderwys",
        "name_ha": "Ilimi",
        "name_hi": "शिक्षा",
        "name_ja": "教育",
        "name_ko": "교육",
        "name_lg": "Eby'Okusoma",
        "name_pt": "Educação",
        "name_ru": "Образование",
        "name_rw": "Uburezi",
        "name_zh": "教育",
        "name_es": "Educación",
        "description_en": "Learning institutions and educational services",
        "description_sw": "Taasisi za elimu na huduma za kujifunza",
        "description_ar": "مؤسسات التعليم وخدمات التعلم",
        "description_af": "Leerinstellings en opvoedkundige dienste",
        "description_ha": "Cibiyoyin koyo da ayyukan ilimi",
        "description_hi": "शिक्षण संस्थान और शैक्षिक सेवाएं",
        "description_ja": "教育機関と教育サービス",
        "description_ko": "교육 기관 및 교육 서비스",
        "description_lg": "Amasomero n'obuweereza bw'ebyenjigiriza",
        "description_pt": "Instituições de ensino e serviços educacionais",
        "description_ru": "Учебные заведения и образовательные услуги",
        "description_rw": "Ibigo by'uburezi n'imirimo y'uburezi",
        "description_zh": "教育机构与教育服务",
        "description_es": "Instituciones educativas y servicios educativos",
        "children": [
            {
                "slug": "schools",
                "name_en": "Schools",
                "name_sw": "Shule",
                "name_fr": "Écoles",
                "name_ar": "المدارس",
                "name_af": "Skole",
                "name_ha": "Makarantu",
                "name_hi": "स्कूल",
                "name_ja": "学校",
                "name_ko": "학교",
                "name_lg": "Amasomero",
                "name_pt": "Escolas",
                "name_ru": "Школы",
                "name_rw": "Amashuri",
                "name_zh": "学校",
                "name_es": "Escuelas",
            },
            {
                "slug": "training-centers",
                "name_en": "Training Centers",
                "name_sw": "Vituo vya Mafunzo",
                "name_fr": "Centres de formation",
                "name_ar": "مراكز التدريب",
                "name_af": "Opleidingsentrums",
                "name_ha": "Cibiyoyin Horarwa",
                "name_hi": "प्रशिक्षण केंद्र",
                "name_ja": "研修センター",
                "name_ko": "훈련 센터",
                "name_lg": "Ebifo by'Okutendekebwa",
                "name_pt": "Centros de Treinamento",
                "name_ru": "Учебные центры",
                "name_rw": "Ibigo by'Amahugurwa",
                "name_zh": "培训中心",
                "name_es": "Centros de Capacitación",
            },
            {
                "slug": "e-learning",
                "name_en": "E-learning",
                "name_sw": "Elimu Mtandao",
                "name_fr": "Apprentissage en ligne",
                "name_ar": "التعلم الإلكتروني",
                "name_af": "E-leer",
                "name_ha": "Koyo ta Yanar Gizo",
                "name_hi": "ई-लर्निंग",
                "name_ja": "eラーニング",
                "name_ko": "이러닝",
                "name_lg": "Okuyiga kwa Yintaneeti",
                "name_pt": "Ensino a Distância",
                "name_ru": "Электронное обучение",
                "name_rw": "Kwiga kuri Interineti",
                "name_zh": "在线学习",
                "name_es": "Educación en Línea",
            },
        ]
    },

    # CONSTRUCTION
    {
        "slug": "construction",
        "name_en": "Construction",
        "name_sw": "Ujenzi",
        "name_fr": "Construction",
        "name_ar": "البناء",
        "name_af": "Konstruksie",
        "name_ha": "Gine-gine",
        "name_hi": "निर्माण",
        "name_ja": "建設",
        "name_ko": "건설",
        "name_lg": "Okuzimba",
        "name_pt": "Construção",
        "name_ru": "Строительство",
        "name_rw": "Ubwubatsi",
        "name_zh": "建筑",
        "name_es": "Construcción",
        "description_en": "Building, infrastructure and property development",
        "description_sw": "Ujenzi wa majengo, miundombinu na nyumba",
        "description_ar": "بناء المباني والبنية التحتية وتطوير العقارات",
        "description_af": "Bou, infrastruktuur en eiendomsontwikkeling",
        "description_ha": "Gine-gine, kayayyakin more rayuwa da bunkasa gidaje",
        "description_hi": "भवन निर्माण, बुनियादी ढांचा और संपत्ति विकास",
        "description_ja": "建築、インフラ、不動産開発",
        "description_ko": "건축, 인프라 및 부동산 개발",
        "description_lg": "Okuzimba, ebizimbe n'okukulaakulanya obutaka",
        "description_pt": "Construção, infraestrutura e desenvolvimento imobiliário",
        "description_ru": "Строительство, инфраструктура и развитие недвижимости",
        "description_rw": "Ubwubatsi, ibikorwa remezo n'iterambere ry'imitungo",
        "description_zh": "建筑、基础设施与房地产开发",
        "description_es": "Construcción, infraestructura y desarrollo inmobiliario",
        "children": [
            {
                "slug": "building",
                "name_en": "Building Construction",
                "name_sw": "Ujenzi wa Majengo",
                "name_fr": "Construction de bâtiments",
                "name_ar": "بناء المباني",
                "name_af": "Gebouekonstruksie",
                "name_ha": "Gine-ginen Gidaje",
                "name_hi": "भवन निर्माण",
                "name_ja": "建物建設",
                "name_ko": "건물 건설",
                "name_lg": "Okuzimba Ebizimbe",
                "name_pt": "Construção de Edifícios",
                "name_ru": "Строительство зданий",
                "name_rw": "Ubwubatsi bw'Inyubako",
                "name_zh": "建筑物施工",
                "name_es": "Construcción de Edificios",
            },
            {
                "slug": "civil-engineering",
                "name_en": "Civil Engineering",
                "name_sw": "Uhandisi wa Miundombinu",
                "name_fr": "Génie civil",
                "name_ar": "الهندسة المدنية",
                "name_af": "Siviele Ingenieurswese",
                "name_ha": "Injiniyan Gini",
                "name_hi": "सिविल इंजीनियरिंग",
                "name_ja": "土木工学",
                "name_ko": "토목 공학",
                "name_lg": "Obuyivu bw'Emiwendo",
                "name_pt": "Engenharia Civil",
                "name_ru": "Гражданское строительство",
                "name_rw": "Ubuhanga mu Bwubatsi",
                "name_zh": "土木工程",
                "name_es": "Ingeniería Civil",
            },
            {
                "slug": "real-estate",
                "name_en": "Real Estate",
                "name_sw": "Biashara ya Majengo",
                "name_fr": "Immobilier",
                "name_ar": "العقارات",
                "name_af": "Vaste Eiendom",
                "name_ha": "Gidaje da Filaye",
                "name_hi": "रियल एस्टेट",
                "name_ja": "不動産",
                "name_ko": "부동산",
                "name_lg": "Eby'Obutaka",
                "name_pt": "Imóveis",
                "name_ru": "Недвижимость",
                "name_rw": "Imitungo Itimukanwa",
                "name_zh": "房地产",
                "name_es": "Bienes Raíces",
            },
        ]
    },

    # TRANSPORT
    {
        "slug": "transport-logistics",
        "name_en": "Transport & Logistics",
        "name_sw": "Usafirishaji na Usafirishaji",
        "name_fr": "Transport et logistique",
        "name_ar": "النقل والخدمات اللوجستية",
        "name_af": "Vervoer en Logistiek",
        "name_ha": "Sufuri da Dabaru",
        "name_hi": "परिवहन और रसद",
        "name_ja": "輸送・物流",
        "name_ko": "운송 및 물류",
        "name_lg": "Entambula n'Obuweereza",
        "name_pt": "Transporte e Logística",
        "name_ru": "Транспорт и логистика",
        "name_rw": "Ubwikorezi n'Ubwikorezi",
        "name_zh": "运输与物流",
        "name_es": "Transporte y Logística",
        "description_en": "Moving goods and people from one place to another",
        "description_sw": "Kusafirisha bidhaa na watu kutoka sehemu moja hadi nyingine",
        "description_ar": "نقل البضائع والأشخاص من مكان إلى آخر",
        "description_af": "Beweging van goedere en mense van een plek na 'n ander",
        "description_ha": "Kai kayayyaki da mutane daga wuri zuwa wani",
        "description_hi": "एक स्थान से दूसरे स्थान तक माल और लोगों की आवाजाही",
        "description_ja": "物や人をある場所から別の場所へ移動させること",
        "description_ko": "물건과 사람을 한 곳에서 다른 곳으로 이동",
        "description_lg": "Okusindika ebintu n'abantu okuva mu kifo ekimu okudda mu kirala",
        "description_pt": "Movimentação de mercadorias e pessoas de um lugar para outro",
        "description_ru": "Перемещение товаров и людей из одного места в другое",
        "description_rw": "Kwimura ibicuruzwa n'abantu kuva ahantu bajya ahandi",
        "description_zh": "将货物和人员从一个地方运送到另一个地方",
        "description_es": "Traslado de mercancías y personas de un lugar a otro",
        "children": [
            {
                "slug": "road-transport",
                "name_en": "Road Transport",
                "name_sw": "Usafiri wa Barabarani",
                "name_fr": "Transport routier",
                "name_ar": "النقل البري",
                "name_af": "Padvervoer",
                "name_ha": "Sufurin Kasa",
                "name_hi": "सड़क परिवहन",
                "name_ja": "陸上輸送",
                "name_ko": "도로 운송",
                "name_lg": "Entambula y'Oku Luguudo",
                "name_pt": "Transporte Rodoviário",
                "name_ru": "Автомобильный транспорт",
                "name_rw": "Ubwikorezi bw'Umuhanda",
                "name_zh": "公路运输",
                "name_es": "Transporte por Carretera",
            },
            {
                "slug": "air-transport",
                "name_en": "Air Transport",
                "name_sw": "Usafiri wa Anga",
                "name_fr": "Transport aérien",
                "name_ar": "النقل الجوي",
                "name_af": "Lugvervoer",
                "name_ha": "Sufurin Sama",
                "name_hi": "हवाई परिवहन",
                "name_ja": "航空輸送",
                "name_ko": "항공 운송",
                "name_lg": "Entambula y'Ebbanga",
                "name_pt": "Transporte Aéreo",
                "name_ru": "Воздушный транспорт",
                "name_rw": "Ubwikorezi bwo mu Kirere",
                "name_zh": "航空运输",
                "name_es": "Transporte Aéreo",
            },
            {
                "slug": "shipping",
                "name_en": "Shipping",
                "name_sw": "Usafirishaji wa Meli",
                "name_fr": "Transport maritime",
                "name_ar": "الشحن البحري",
                "name_af": "Skeepvaart",
                "name_ha": "Sufurin Ruwa",
                "name_hi": "शिपिंग",
                "name_ja": "海運",
                "name_ko": "해운",
                "name_lg": "Entambula y'Amaato",
                "name_pt": "Transporte Marítimo",
                "name_ru": "Морские перевозки",
                "name_rw": "Ubwikorezi bw'Amato",
                "name_zh": "航运",
                "name_es": "Transporte Marítimo",
            },
        ]
    },

    # TOURISM
    {
        "slug": "tourism-hospitality",
        "name_en": "Tourism & Hospitality",
        "name_sw": "Utalii na Ukarimu",
        "name_fr": "Tourisme et hôtellerie",
        "name_ar": "السياحة والضيافة",
        "name_af": "Toerisme en Gasvryheid",
        "name_ha": "Yawon Bude Ido da Karbar Baki",
        "name_hi": "पर्यटन और आतिथ्य",
        "name_ja": "観光・接客業",
        "name_ko": "관광 및 접객업",
        "name_lg": "Amatambula n'Obuyambi",
        "name_pt": "Turismo e Hospitalidade",
        "name_ru": "Туризм и гостеприимство",
        "name_rw": "Ubukerarugendo n'Ubwakiriro",
        "name_zh": "旅游与酒店业",
        "name_es": "Turismo y Hostelería",
        "description_en": "Travel, accommodation and visitor services",
        "description_sw": "Safari, malazi na huduma za wageni",
        "description_ar": "السفر والإقامة وخدمات الزوار",
        "description_af": "Reis, verblyf en besoekersdienste",
        "description_ha": "Tafiye-tafiye, wurin zama da ayyukan baki",
        "description_hi": "यात्रा, आवास और आगंतुक सेवाएं",
        "description_ja": "旅行、宿泊、来訪者サービス",
        "description_ko": "여행, 숙박 및 방문객 서비스",
        "description_lg": "Entambula, obuli n'obuweereza bw'abagenyi",
        "description_pt": "Viagens, hospedagem e serviços a visitantes",
        "description_ru": "Путешествия, размещение и обслуживание посетителей",
        "description_rw": "Ingendo, guturamo n'imirimo y'abashyitsi",
        "description_zh": "旅行、住宿与游客服务",
        "description_es": "Viajes, alojamiento y servicios para visitantes",
        "children": [
            {
                "slug": "hotels",
                "name_en": "Hotels",
                "name_sw": "Hoteli",
                "name_fr": "Hôtels",
                "name_ar": "الفنادق",
                "name_af": "Hotelle",
                "name_ha": "Otal-otal",
                "name_hi": "होटल",
                "name_ja": "ホテル",
                "name_ko": "호텔",
                "name_lg": "Wooteeri",
                "name_pt": "Hotéis",
                "name_ru": "Отели",
                "name_rw": "Amahoteri",
                "name_zh": "酒店",
                "name_es": "Hoteles",
            },
            {
                "slug": "travel-agencies",
                "name_en": "Travel Agencies",
                "name_sw": "Mashirika ya Safari",
                "name_fr": "Agences de voyage",
                "name_ar": "وكالات السفر",
                "name_af": "Reisagentskappe",
                "name_ha": "Hukumomin Yawon Bude Ido",
                "name_hi": "यात्रा एजेंसियां",
                "name_ja": "旅行代理店",
                "name_ko": "여행사",
                "name_lg": "Ebitongole by'Entambula",
                "name_pt": "Agências de Viagens",
                "name_ru": "Туристические агентства",
                "name_rw": "Ibigo by'Ingendo",
                "name_zh": "旅行社",
                "name_es": "Agencias de Viajes",
            },
            {
                "slug": "tour-operators",
                "name_en": "Tour Operators",
                "name_sw": "Waendeshaji Utalii",
                "name_fr": "Opérateurs touristiques",
                "name_ar": "منظمو الجولات السياحية",
                "name_af": "Toeroperateurs",
                "name_ha": "Kamfanonin Yawon Bude Ido",
                "name_hi": "टूर ऑपरेटर",
                "name_ja": "ツアーオペレーター",
                "name_ko": "투어 운영업체",
                "name_lg": "Abakwakulira Entambula",
                "name_pt": "Operadores de Turismo",
                "name_ru": "Туроператоры",
                "name_rw": "Abakora Ingendo z'Ubukerarugendo",
                "name_zh": "旅游运营商",
                "name_es": "Operadores Turísticos",
            },
        ]
    },

    # CREATIVE INDUSTRY
    {
        "slug": "creative-media",
        "name_en": "Creative & Media",
        "name_sw": "Ubunifu na Vyombo vya Habari",
        "name_fr": "Créatif et médias",
        "name_ar": "الإبداع والإعلام",
        "name_af": "Kreatief en Media",
        "name_ha": "Kere-kere da Watsa Labarai",
        "name_hi": "रचनात्मक और मीडिया",
        "name_ja": "クリエイティブ・メディア",
        "name_ko": "창작 및 미디어",
        "name_lg": "Eby'Obuyiiya n'Amawulire",
        "name_pt": "Criatividade e Mídia",
        "name_ru": "Творчество и медиа",
        "name_rw": "Ubuhanzi n'Itangazamakuru",
        "name_zh": "创意与媒体",
        "name_es": "Creatividad y Medios",
        "description_en": "Arts, entertainment, design and media production",
        "description_sw": "Sanaa, burudani, ubunifu na utengenezaji wa habari",
        "description_ar": "الفنون والترفيه والتصميم وإنتاج الإعلام",
        "description_af": "Kuns, vermaak, ontwerp en mediaproduksie",
        "description_ha": "Fasaha, nishadi, zane-zane da samar da watsa labarai",
        "description_hi": "कला, मनोरंजन, डिज़ाइन और मीडिया उत्पादन",
        "description_ja": "芸術、エンターテインメント、デザイン、メディア制作",
        "description_ko": "예술, 엔터테인먼트, 디자인 및 미디어 제작",
        "description_lg": "Ebyobuyiiya, eby'okusanyusa, okuzimba enteekateeka n'okukola amawulire",
        "description_pt": "Artes, entretenimento, design e produção de mídia",
        "description_ru": "Искусство, развлечения, дизайн и медиапроизводство",
        "description_rw": "Ubuhanzi, imyidagaduro, igishushanyo n'ikoranabuhanga ry'itangazamakuru",
        "description_zh": "艺术、娱乐、设计与媒体制作",
        "description_es": "Arte, entretenimiento, diseño y producción de medios",
        "children": [
            {
                "slug": "music-production",
                "name_en": "Music Production",
                "name_sw": "Uzalishaji wa Muziki",
                "name_fr": "Production musicale",
                "name_ar": "إنتاج الموسيقى",
                "name_af": "Musiekproduksie",
                "name_ha": "Samar da Waƙa",
                "name_hi": "संगीत उत्पादन",
                "name_ja": "音楽制作",
                "name_ko": "음악 제작",
                "name_lg": "Okukola Ennyimba",
                "name_pt": "Produção Musical",
                "name_ru": "Музыкальное производство",
                "name_rw": "Gukora Umuziki",
                "name_zh": "音乐制作",
                "name_es": "Producción Musical",
            },
            {
                "slug": "film-production",
                "name_en": "Film Production",
                "name_sw": "Utengenezaji wa Filamu",
                "name_fr": "Production cinématographique",
                "name_ar": "إنتاج الأفلام",
                "name_af": "Filmproduksie",
                "name_ha": "Samar da Fina-finai",
                "name_hi": "फिल्म निर्माण",
                "name_ja": "映画制作",
                "name_ko": "영화 제작",
                "name_lg": "Okukola Firimu",
                "name_pt": "Produção Cinematográfica",
                "name_ru": "Кинопроизводство",
                "name_rw": "Gukora Amashusho",
                "name_zh": "电影制作",
                "name_es": "Producción Cinematográfica",
            },
            {
                "slug": "graphic-design",
                "name_en": "Graphic Design",
                "name_sw": "Ubunifu wa Michoro",
                "name_fr": "Conception graphique",
                "name_ar": "التصميم الجرافيكي",
                "name_af": "Grafiese Ontwerp",
                "name_ha": "Zanen Hoto",
                "name_hi": "ग्राफिक डिज़ाइन",
                "name_ja": "グラフィックデザイン",
                "name_ko": "그래픽 디자인",
                "name_lg": "Okuzimba Ebifaananyi",
                "name_pt": "Design Gráfico",
                "name_ru": "Графический дизайн",
                "name_rw": "Igishushanyo mbonera",
                "name_zh": "平面设计",
                "name_es": "Diseño Gráfico",
            },
        ]
    },

    # FINANCIAL SERVICES
    {
        "slug": "financial-services",
        "name_en": "Financial Services",
        "name_sw": "Huduma za Kifedha",
        "name_fr": "Services financiers",
        "name_ar": "الخدمات المالية",
        "name_af": "Finansiële Dienste",
        "name_ha": "Ayyukan Kudi",
        "name_hi": "वित्तीय सेवाएं",
        "name_ja": "金融サービス",
        "name_ko": "금융 서비스",
        "name_lg": "Obuweereza bw'Ensimbi",
        "name_pt": "Serviços Financeiros",
        "name_ru": "Финансовые услуги",
        "name_rw": "Serivisi z'Imari",
        "name_zh": "金融服务",
        "name_es": "Servicios Financieros",
        "description_en": "Banking, insurance, investments and money services",
        "description_sw": "Benki, bima, uwekezaji na huduma za fedha",
        "description_ar": "الخدمات المصرفية والتأمين والاستثمار والخدمات المالية",
        "description_af": "Bankwese, versekering, beleggings en gelddienste",
        "description_ha": "Banki, inshora, saka hannun jari da ayyukan kudi",
        "description_hi": "बैंकिंग, बीमा, निवेश और धन सेवाएं",
        "description_ja": "銀行、保険、投資、金融サービス",
        "description_ko": "은행, 보험, 투자 및 금융 서비스",
        "description_lg": "Ebbanka, inshuwa, okusimba ssente n'obuweereza bw'ensimbi",
        "description_pt": "Serviços bancários, seguros, investimentos e serviços financeiros",
        "description_ru": "Банковское дело, страхование, инвестиции и денежные услуги",
        "description_rw": "Banki, ubwishingizi, ishoramari na serivisi z'amafaranga",
        "description_zh": "银行、保险、投资与货币服务",
        "description_es": "Banca, seguros, inversiones y servicios monetarios",
        "children": [
            {
                "slug": "banking",
                "name_en": "Banking",
                "name_sw": "Benki",
                "name_fr": "Banque",
                "name_ar": "الخدمات المصرفية",
                "name_af": "Bankwese",
                "name_ha": "Banki",
                "name_hi": "बैंकिंग",
                "name_ja": "銀行業",
                "name_ko": "은행업",
                "name_lg": "Ebbanka",
                "name_pt": "Serviços Bancários",
                "name_ru": "Банковское дело",
                "name_rw": "Serivisi za Banki",
                "name_zh": "银行业务",
                "name_es": "Banca",
            },
            {
                "slug": "insurance",
                "name_en": "Insurance",
                "name_sw": "Bima",
                "name_fr": "Assurance",
                "name_ar": "التأمين",
                "name_af": "Versekering",
                "name_ha": "Inshora",
                "name_hi": "बीमा",
                "name_ja": "保険",
                "name_ko": "보험",
                "name_lg": "Inshuwa",
                "name_pt": "Seguros",
                "name_ru": "Страхование",
                "name_rw": "Ubwishingizi",
                "name_zh": "保险",
                "name_es": "Seguros",
            },
            {
                "slug": "microfinance",
                "name_en": "Microfinance",
                "name_sw": "Fedha ndogo ndogo",
                "name_fr": "Microfinance",
                "name_ar": "التمويل الأصغر",
                "name_af": "Mikrofinansiering",
                "name_ha": "Ƙananan Kuɗi",
                "name_hi": "सूक्ष्म वित्त",
                "name_ja": "マイクロファイナンス",
                "name_ko": "소액 금융",
                "name_lg": "Ensimbi Entono",
                "name_pt": "Microfinanças",
                "name_ru": "Микрофинансирование",
                "name_rw": "Imari Ntoya",
                "name_zh": "小额信贷",
                "name_es": "Microfinanzas",
            },
            {
                "slug": "investments",
                "name_en": "Investments",
                "name_sw": "Uwekezaji",
                "name_fr": "Investissements",
                "name_ar": "الاستثمارات",
                "name_af": "Beleggings",
                "name_ha": "Saka Hannun Jari",
                "name_hi": "निवेश",
                "name_ja": "投資",
                "name_ko": "투자",
                "name_lg": "Okusimba Ssente",
                "name_pt": "Investimentos",
                "name_ru": "Инвестиции",
                "name_rw": "Ishoramari",
                "name_zh": "投资",
                "name_es": "Inversiones",
            },
        ]
    },

    # PROFESSIONAL SERVICES
    {
        "slug": "professional-services",
        "name_en": "Professional Services",
        "name_sw": "Huduma za Kitaalamu",
        "name_fr": "Services professionnels",
        "name_ar": "الخدمات المهنية",
        "name_af": "Professionele Dienste",
        "name_ha": "Ayyukan Ƙwararru",
        "name_hi": "व्यावसायिक सेवाएं",
        "name_ja": "専門サービス",
        "name_ko": "전문 서비스",
        "name_lg": "Obuweereza bw'Abakugu",
        "name_pt": "Serviços Profissionais",
        "name_ru": "Профессиональные услуги",
        "name_rw": "Serivisi z'Abanyamwuga",
        "name_zh": "专业服务",
        "name_es": "Servicios Profesionales",
        "description_en": "Legal, accounting, consulting and business support",
        "description_sw": "Huduma za kisheria, uhasibu, ushauri na msaada wa biashara",
        "description_ar": "الخدمات القانونية والمحاسبية والاستشارية ودعم الأعمال",
        "description_af": "Regs-, rekeningkundige, konsultasie- en besigheidsondersteuningsdienste",
        "description_ha": "Shari'a, lissafin kudi, shawarwari da tallafin kasuwanci",
        "description_hi": "कानूनी, लेखांकन, परामर्श और व्यावसायिक सहायता",
        "description_ja": "法務、会計、コンサルティング、ビジネスサポート",
        "description_ko": "법률, 회계, 컨설팅 및 비즈니스 지원",
        "description_lg": "Eby'amateeka, obukalimagezi, obuwabuzi n'obuyambi mu bizinensi",
        "description_pt": "Serviços jurídicos, contábeis, de consultoria e apoio empresarial",
        "description_ru": "Юридические, бухгалтерские, консультационные услуги и поддержка бизнеса",
        "description_rw": "Amategeko, ibaruramari, ubujyanama n'ubufasha ku bucuruzi",
        "description_zh": "法律、会计、咨询与商业支持服务",
        "description_es": "Servicios legales, contables, de consultoría y apoyo empresarial",
        "children": [
            {
                "slug": "legal",
                "name_en": "Legal Services",
                "name_sw": "Huduma za Kisheria",
                "name_fr": "Services juridiques",
                "name_ar": "الخدمات القانونية",
                "name_af": "Regsdienste",
                "name_ha": "Ayyukan Shari'a",
                "name_hi": "कानूनी सेवाएं",
                "name_ja": "法務サービス",
                "name_ko": "법률 서비스",
                "name_lg": "Obuweereza bw'Amateeka",
                "name_pt": "Serviços Jurídicos",
                "name_ru": "Юридические услуги",
                "name_rw": "Serivisi z'Amategeko",
                "name_zh": "法律服务",
                "name_es": "Servicios Legales",
            },
            {
                "slug": "accounting",
                "name_en": "Accounting",
                "name_sw": "Uhasibu",
                "name_fr": "Comptabilité",
                "name_ar": "المحاسبة",
                "name_af": "Rekeningkunde",
                "name_ha": "Lissafin Kudi",
                "name_hi": "लेखांकन",
                "name_ja": "会計",
                "name_ko": "회계",
                "name_lg": "Obukalimagezi",
                "name_pt": "Contabilidade",
                "name_ru": "Бухгалтерский учёт",
                "name_rw": "Ibaruramari",
                "name_zh": "会计",
                "name_es": "Contabilidad",
            },
            {
                "slug": "consulting",
                "name_en": "Consulting",
                "name_sw": "Ushauri",
                "name_fr": "Conseil",
                "name_ar": "الاستشارات",
                "name_af": "Konsultasie",
                "name_ha": "Shawarwari",
                "name_hi": "परामर्श",
                "name_ja": "コンサルティング",
                "name_ko": "컨설팅",
                "name_lg": "Obuwabuzi",
                "name_pt": "Consultoria",
                "name_ru": "Консалтинг",
                "name_rw": "Ubujyanama",
                "name_zh": "咨询",
                "name_es": "Consultoría",
            },
            {
                "slug": "marketing",
                "name_en": "Marketing",
                "name_sw": "Masoko",
                "name_fr": "Marketing",
                "name_ar": "التسويق",
                "name_af": "Bemarking",
                "name_ha": "Talla",
                "name_hi": "विपणन",
                "name_ja": "マーケティング",
                "name_ko": "마케팅",
                "name_lg": "Ekitongole ky'Amasoko",
                "name_pt": "Marketing",
                "name_ru": "Маркетинг",
                "name_rw": "Isoko",
                "name_zh": "市场营销",
                "name_es": "Marketing",
            },
        ]
    },

    # INFORMAL & INDIVIDUAL SERVICES (wafanyabiashara/wafanyakazi binafsi)
    {
        "slug": "informal-individual-services",
        "name_en": "Informal & Individual Services",
        "name_sw": "Huduma Binafsi na Wafanyabiashara Wadogo",
        "name_fr": "Services Informels et Individuels",
        "name_ar": "الخدمات غير الرسمية والفردية",
        "name_af": "Informele en Individuele Dienste",
        "name_ha": "Ayyukan Yau da Kullum da na Mutum Ɗaya",
        "name_hi": "अनौपचारिक और व्यक्तिगत सेवाएं",
        "name_ja": "インフォーマル・個人サービス",
        "name_ko": "비공식 및 개인 서비스",
        "name_lg": "Obuweereza obw'Ekifo n'Obwannoomu",
        "name_pt": "Serviços Informais e Individuais",
        "name_ru": "Неформальные и индивидуальные услуги",
        "name_rw": "Serivisi Zidasanzwe n'Iz'Umuntu ku Giti Cye",
        "name_zh": "非正规与个体服务",
        "name_es": "Servicios Informales e Individuales",
        "description_en": "Independent workers and small-scale traders serving their communities directly",
        "description_sw": "Wafanyakazi huru na wafanyabiashara wadogo wanaohudumia jamii zao moja kwa moja",
        "description_fr": "Travailleurs indépendants et petits commerçants au service direct de leurs communautés",
        "description_ar": "العمال المستقلون وصغار التجار الذين يخدمون مجتمعاتهم مباشرة",
        "description_af": "Onafhanklike werkers en kleinskaalse handelaars wat hul gemeenskappe direk bedien",
        "description_ha": "Ma'aikata masu zaman kansu da ƙananan 'yan kasuwa da ke hidimtawa al'ummominsu kai tsaye",
        "description_hi": "स्वतंत्र कार्यकर्ता और छोटे व्यापारी जो सीधे अपने समुदायों की सेवा करते हैं",
        "description_ja": "地域社会に直接サービスを提供する独立労働者と小規模事業者",
        "description_ko": "지역사회에 직접 서비스를 제공하는 독립 근로자 및 소규모 상인",
        "description_lg": "Abakozi abeetongodde n'abasuubuzi abato abaweereza obuwatiro bwabwe butereevu",
        "description_pt": "Trabalhadores independentes e pequenos comerciantes que atendem diretamente suas comunidades",
        "description_ru": "Независимые работники и мелкие торговцы, обслуживающие свои сообщества напрямую",
        "description_rw": "Abakozi bigenga n'abadandaza bato bakorera imibereho y'abaturage batuye",
        "description_zh": "直接服务于社区的独立工作者和小型商贩",
        "description_es": "Trabajadores independientes y pequeños comerciantes que atienden directamente a sus comunidades",
        "children": [
            {
                "slug": "driver",
                "name_en": "Driver",
                "name_sw": "Dereva",
                "name_fr": "Chauffeur",
                "name_ar": "سائق",
                "name_af": "Bestuurder",
                "name_ha": "Direba",
                "name_hi": "चालक",
                "name_ja": "ドライバー",
                "name_ko": "운전기사",
                "name_lg": "Omuvvuzi",
                "name_pt": "Motorista",
                "name_ru": "Водитель",
                "name_rw": "Umushoferi",
                "name_zh": "司机",
                "name_es": "Conductor",
            },
            {
                "slug": "food-vendor",
                "name_en": "Food Vendor",
                "name_sw": "Mama Ntilie",
                "name_fr": "Vendeur de Nourriture",
                "name_ar": "بائع طعام",
                "name_af": "Kosverkoper",
                "name_ha": "Mai Sayar da Abinci",
                "name_hi": "खाद्य विक्रेता",
                "name_ja": "食品販売業者",
                "name_ko": "음식 노점상",
                "name_lg": "Omuguzi w'Emmere",
                "name_pt": "Vendedor de Alimentos",
                "name_ru": "Продавец еды",
                "name_rw": "Ucuruza Ibiribwa",
                "name_zh": "食品小贩",
                "name_es": "Vendedor de Alimentos",
            },
            {
                "slug": "small-scale-farmer",
                "name_en": "Small-Scale Farmer",
                "name_sw": "Mkulima Mdogo",
                "name_fr": "Petit Agriculteur",
                "name_ar": "مزارع صغير",
                "name_af": "Kleinboer",
                "name_ha": "Manomin Ƙaramin Gona",
                "name_hi": "लघु किसान",
                "name_ja": "小規模農家",
                "name_ko": "소규모 농업인",
                "name_lg": "Omulimi Omutono",
                "name_pt": "Pequeno Agricultor",
                "name_ru": "Мелкий фермер",
                "name_rw": "Umuhinzi Muto",
                "name_zh": "小型农户",
                "name_es": "Pequeño Agricultor",
            },
            {
                "slug": "artisan-repair",
                "name_en": "Artisan / Repair Technician",
                "name_sw": "Fundi",
                "name_fr": "Artisan / Réparateur",
                "name_ar": "حرفي / فني إصلاح",
                "name_af": "Ambagsman / Herstelltegnikus",
                "name_ha": "Masani / Mai Gyara",
                "name_hi": "शिल्पकार / मरम्मत तकनीशियन",
                "name_ja": "職人・修理技術者",
                "name_ko": "장인/수리 기술자",
                "name_lg": "Omukozi w'Emikono / Omuddaabiriza",
                "name_pt": "Artesão / Técnico de Reparos",
                "name_ru": "Ремесленник / мастер по ремонту",
                "name_rw": "Umukozi w'Ubuhanga / Umukanishi",
                "name_zh": "工匠/维修技师",
                "name_es": "Artesano / Técnico de Reparaciones",
            },
            {
                "slug": "small-shopkeeper",
                "name_en": "Small Shopkeeper",
                "name_sw": "Muuza Duka Mdogo",
                "name_fr": "Petit Commerçant",
                "name_ar": "بائع متجر صغير",
                "name_af": "Klein Winkelier",
                "name_ha": "Ɗan Kasuwa Ƙarami",
                "name_hi": "छोटा दुकानदार",
                "name_ja": "小規模店主",
                "name_ko": "소규모 상점 주인",
                "name_lg": "Omusuubuzi w'Eduuka Ettono",
                "name_pt": "Pequeno Lojista",
                "name_ru": "Мелкий лавочник",
                "name_rw": "Ucuruza mu Iduka Rito",
                "name_zh": "小店主",
                "name_es": "Pequeño Comerciante",
            },
        ]
    },
]

# =====================================================
# COMMAND - Bila Icon Field
# =====================================================

class Command(BaseCommand):
    help = "Seed Business Categories with translations and hierarchy"

    # Languages zinazotumika
    LANGUAGES = ['sw', 'fr', 'ar', 'af', 'ha', 'hi', 'ja', 'ko', 'lg', 'pt', 'ru', 'rw', 'zh', 'es']

    # Fields za kutafsiri
    TRANSLATABLE_FIELDS = ['name', 'description']

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Dry run: show what would be created without actually creating',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )
        parser.add_argument(
            '--categories',
            nargs='+',
            type=str,
            help='Specific category slugs to seed (e.g., --categories agriculture technology)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing categories before seeding (use with caution)',
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip existing categories instead of updating them',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.verbose = options['verbose']
        self.skip_existing = options['skip_existing']

        # Kama ni dry run, onyesha tahadhari
        if self.dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN MODE - No changes will be made"))
            self.stdout.write("=" * 60)

        # Clear categories kama imeombwa
        if options['clear'] and not self.dry_run:
            self.clear_categories()

        # Chuja categories kama zimetajwa
        categories_to_seed = self.filter_categories(options.get('categories'))

        # Anza seeding
        start_time = timezone.now()
        stats = self.seed_categories(categories_to_seed)
        end_time = timezone.now()

        # Ripoti
        self.print_summary(stats, end_time - start_time, self.dry_run)

    def filter_categories(self, slug_list: Optional[List[str]]) -> List[Dict]:
        """Chuja categories kulingana na slugs"""
        if not slug_list:
            return CATEGORIES

        filtered = []
        for cat in CATEGORIES:
            if cat['slug'] in slug_list:
                filtered.append(cat)
            else:
                # Angalia kama mtoto yupo kwenye list
                children = cat.get('children', [])
                filtered_children = [c for c in children if c['slug'] in slug_list]
                if filtered_children:
                    cat_copy = cat.copy()
                    cat_copy['children'] = filtered_children
                    filtered.append(cat_copy)

        if not filtered:
            self.stdout.write(
                self.style.WARNING(f"No categories found for slugs: {', '.join(slug_list)}")
            )

        return filtered

    def clear_categories(self):
        """Futa categories zote"""
        self.stdout.write(self.style.WARNING("Clearing all existing categories..."))
        count = BusinessCategory.objects.count()
        BusinessCategory.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"✅ Deleted {count} categories"))

    @transaction.atomic
    def seed_categories(self, categories: List[Dict], parent: Optional[BusinessCategory] = None,
                       depth: int = 0, stats: Optional[Dict] = None) -> Dict:
        """Seed categories kwa kutumia transaction"""
        if stats is None:
            stats = {'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0}

        indent = "  " * depth

        for data in categories:
            try:
                # Validate data
                self.validate_category_data(data)

                # Angalia kama category ipo
                exists = BusinessCategory.objects.filter(slug=data["slug"]).exists()

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
                    # Create or update category
                    category, created = self.create_or_update_category(data, parent)

                    if created:
                        stats['created'] += 1
                        self.stdout.write(self.style.SUCCESS(f"{indent}✅ Created: {data['slug']}"))
                    else:
                        stats['updated'] += 1
                        if self.verbose:
                            self.stdout.write(self.style.SUCCESS(f"{indent}🔄 Updated: {data['slug']}"))

                # Process children
                children = data.get("children", [])
                if children:
                    if self.dry_run:
                        self.stdout.write(f"{indent}  Children:")

                    # Rekodi statistics za watoto
                    self.seed_categories(
                        children,
                        parent=None if self.dry_run else category,
                        depth=depth + 1,
                        stats=stats
                    )

            except Exception as e:
                stats['errors'] += 1
                error_msg = f"Error seeding {data.get('slug', 'unknown')}: {str(e)}"
                self.stderr.write(self.style.ERROR(f"{indent}❌ {error_msg}"))
                logger.error(error_msg, exc_info=True)

                if not self.dry_run:
                    # Rollback transaction kwa category hii na watoto wake
                    raise CommandError(f"Seeding failed: {error_msg}")

        return stats

    def validate_category_data(self, data: Dict):
        """Validate category data structure"""
        required_fields = ['slug', 'name_en']

        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: '{field}'")

        # Validate slug format
        slug = data['slug']
        if not slug.replace('-', '').replace('_', '').isalnum():
            raise ValueError(
                f"Invalid slug format: '{slug}'. Use only letters, numbers, hyphens and underscores."
            )

        # Validate no duplicate names kwa level moja
        if 'children' in data:
            child_slugs = [c['slug'] for c in data['children']]
            if len(child_slugs) != len(set(child_slugs)):
                raise ValueError(f"Duplicate child slugs found in {slug}")

        return True

    def create_or_update_category(self, data: Dict, parent: Optional[BusinessCategory] = None) -> tuple:
        """Create au update category na translations zake"""

        # Prepare defaults - HAKUNA ICON FIELD
        defaults = {
            "parent": parent,
            "name": data.get("name_en"),
            "description": data.get("description_en", ""),
        }

        # Ongeza order kama ipo (kama field ipo kwenye model)
        if "order" in data:
            try:
                # Angalia kama field order ipo kwenye model
                if hasattr(BusinessCategory, 'order'):
                    defaults["order"] = data["order"]
            except:
                pass  # Ignore kama haipo

        # Create or update
        category, created = BusinessCategory.objects.update_or_create(
            slug=data["slug"],
            defaults=defaults
        )

        # Update translations
        for field in self.TRANSLATABLE_FIELDS:
            for lang in self.LANGUAGES:
                key = f"{field}_{lang}"
                if key in data:
                    setattr(category, key, data[key])

        category.save()

        return category, created

    def print_summary(self, stats: Dict, duration, dry_run: bool):
        """Print summary ya seeding"""
        self.stdout.write("=" * 60)

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN SUMMARY"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ SEEDING COMPLETED"))

        self.stdout.write(f"Categories:")
        self.stdout.write(f"  ✅ Created:  {stats.get('created', 0)}")
        self.stdout.write(f"  🔄 Updated:  {stats.get('updated', 0)}")
        self.stdout.write(f"  ⏭️ Skipped:  {stats.get('skipped', 0)}")

        if stats.get('errors', 0) > 0:
            self.stdout.write(self.style.ERROR(f"  ❌ Errors:   {stats.get('errors', 0)}"))
        else:
            self.stdout.write(f"  ✅ Errors:   0")

        self.stdout.write(f"⏱️ Time: {duration.total_seconds():.2f} seconds")

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN - No changes were made"))
        else:
            total = BusinessCategory.objects.count()
            self.stdout.write(self.style.SUCCESS(f"📊 Total categories in DB: {total}"))
