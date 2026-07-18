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
        "description_en": "Farming, crop production and livestock keeping",
        "description_sw": "Kilimo, uzalishaji wa mazao na ufugaji",
        "description_fr": "Agriculture, production végétale et élevage",
        "description_ar": "الزراعة وإنتاج المحاصيل وتربية الماشية",
        "children": [
            {
                "slug": "crop-production",
                "name_en": "Crop Production",
                "name_sw": "Uzalishaji wa Mazao",
                "name_fr": "Production végétale",
                "name_ar": "إنتاج المحاصيل",
                "description_en": "Growing crops for food and commercial purposes",
                "description_sw": "Kulima mazao ya chakula na biashara",
                "description_ar": "زراعة المحاصيل للأغراض الغذائية والتجارية",
                "children": [
                    {
                        "slug": "grain-farming",
                        "name_en": "Grain Farming",
                        "name_sw": "Kilimo cha Nafaka",
                        "name_fr": "Culture céréalière",
                        "name_ar": "زراعة الحبوب"
                    },
                    {
                        "slug": "horticulture",
                        "name_en": "Horticulture",
                        "name_sw": "Kilimo cha Mboga na Matunda",
                        "name_fr": "Horticulture",
                        "name_ar": "البستنة"
                    },
                    {
                        "slug": "cash-crops",
                        "name_en": "Cash Crops",
                        "name_sw": "Mazao ya Biashara",
                        "name_fr": "Cultures de rente",
                        "name_ar": "المحاصيل النقدية"
                    },
                ]
            },
            {
                "slug": "livestock",
                "name_en": "Livestock Farming",
                "name_sw": "Ufugaji",
                "name_fr": "Élevage",
                "name_ar": "تربية الماشية",
                "description_en": "Raising animals for food, fiber and other products",
                "description_sw": "Ufugaji wa wanyama kwa ajili ya chakula na bidhaa nyingine",
                "description_ar": "تربية الحيوانات لإنتاج الغذاء والألياف ومنتجات أخرى",
                "children": [
                    {
                        "slug": "poultry",
                        "name_en": "Poultry Farming",
                        "name_sw": "Ufugaji wa Kuku",
                        "name_fr": "Aviculture",
                        "name_ar": "تربية الدواجن"
                    },
                    {
                        "slug": "dairy",
                        "name_en": "Dairy Farming",
                        "name_sw": "Ufugaji wa Maziwa",
                        "name_fr": "Élevage laitier",
                        "name_ar": "تربية الألبان"
                    },
                    {
                        "slug": "goat-farming",
                        "name_en": "Goat Farming",
                        "name_sw": "Ufugaji wa Mbuzi",
                        "name_fr": "Élevage de chèvres",
                        "name_ar": "تربية الماعز"
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
        "description_en": "Buying and selling of goods and services",
        "description_sw": "Kununua na kuuza bidhaa na huduma",
        "description_ar": "بيع وشراء السلع والخدمات",
        "children": [
            {
                "slug": "retail",
                "name_en": "Retail Trade",
                "name_sw": "Rejareja",
                "name_fr": "Commerce de détail",
                "name_ar": "تجارة التجزئة"
            },
            {
                "slug": "wholesale",
                "name_en": "Wholesale Trade",
                "name_sw": "Biashara ya Jumla",
                "name_fr": "Commerce de gros",
                "name_ar": "تجارة الجملة"
            },
            {
                "slug": "ecommerce",
                "name_en": "E-Commerce",
                "name_sw": "Biashara Mtandao",
                "name_fr": "Commerce électronique",
                "name_ar": "التجارة الإلكترونية"
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
        "description_en": "Digital solutions, software and IT services",
        "description_sw": "Suluhisho za kidijitali, programu na huduma za TEHAMA",
        "description_ar": "الحلول الرقمية والبرمجيات وخدمات تقنية المعلومات",
        "children": [
            {
                "slug": "software-development",
                "name_en": "Software Development",
                "name_sw": "Utengenezaji wa Programu",
                "name_fr": "Développement logiciel",
                "name_ar": "تطوير البرمجيات"
            },
            {
                "slug": "it-services",
                "name_en": "IT Services",
                "name_sw": "Huduma za TEHAMA",
                "name_fr": "Services informatiques",
                "name_ar": "خدمات تقنية المعلومات"
            },
            {
                "slug": "telecommunications",
                "name_en": "Telecommunications",
                "name_sw": "Mawasiliano",
                "name_fr": "Télécommunications",
                "name_ar": "الاتصالات"
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
        "description_en": "Medical services, health facilities and wellness",
        "description_sw": "Huduma za matibabu, vituo vya afya na ustawi",
        "description_ar": "الخدمات الطبية والمرافق الصحية والعافية",
        "children": [
            {
                "slug": "clinics",
                "name_en": "Clinics",
                "name_sw": "Kliniki",
                "name_fr": "Cliniques",
                "name_ar": "العيادات"
            },
            {
                "slug": "pharmacies",
                "name_en": "Pharmacies",
                "name_sw": "Maduka ya Dawa",
                "name_fr": "Pharmacies",
                "name_ar": "الصيدليات"
            },
            {
                "slug": "diagnostic-centers",
                "name_en": "Diagnostic Centers",
                "name_sw": "Vituo vya Vipimo",
                "name_fr": "Centres de diagnostic",
                "name_ar": "مراكز التشخيص"
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
        "description_en": "Learning institutions and educational services",
        "description_sw": "Taasisi za elimu na huduma za kujifunza",
        "description_ar": "مؤسسات التعليم وخدمات التعلم",
        "children": [
            {
                "slug": "schools",
                "name_en": "Schools",
                "name_sw": "Shule",
                "name_fr": "Écoles",
                "name_ar": "المدارس"
            },
            {
                "slug": "training-centers",
                "name_en": "Training Centers",
                "name_sw": "Vituo vya Mafunzo",
                "name_fr": "Centres de formation",
                "name_ar": "مراكز التدريب"
            },
            {
                "slug": "e-learning",
                "name_en": "E-learning",
                "name_sw": "Elimu Mtandao",
                "name_fr": "Apprentissage en ligne",
                "name_ar": "التعلم الإلكتروني"
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
        "description_en": "Building, infrastructure and property development",
        "description_sw": "Ujenzi wa majengo, miundombinu na nyumba",
        "description_ar": "بناء المباني والبنية التحتية وتطوير العقارات",
        "children": [
            {
                "slug": "building",
                "name_en": "Building Construction",
                "name_sw": "Ujenzi wa Majengo",
                "name_fr": "Construction de bâtiments",
                "name_ar": "بناء المباني"
            },
            {
                "slug": "civil-engineering",
                "name_en": "Civil Engineering",
                "name_sw": "Uhandisi wa Miundombinu",
                "name_fr": "Génie civil",
                "name_ar": "الهندسة المدنية"
            },
            {
                "slug": "real-estate",
                "name_en": "Real Estate",
                "name_sw": "Biashara ya Majengo",
                "name_fr": "Immobilier",
                "name_ar": "العقارات"
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
        "description_en": "Moving goods and people from one place to another",
        "description_sw": "Kusafirisha bidhaa na watu kutoka sehemu moja hadi nyingine",
        "description_ar": "نقل البضائع والأشخاص من مكان إلى آخر",
        "children": [
            {
                "slug": "road-transport",
                "name_en": "Road Transport",
                "name_sw": "Usafiri wa Barabarani",
                "name_fr": "Transport routier",
                "name_ar": "النقل البري"
            },
            {
                "slug": "air-transport",
                "name_en": "Air Transport",
                "name_sw": "Usafiri wa Anga",
                "name_fr": "Transport aérien",
                "name_ar": "النقل الجوي"
            },
            {
                "slug": "shipping",
                "name_en": "Shipping",
                "name_sw": "Usafirishaji wa Meli",
                "name_fr": "Transport maritime",
                "name_ar": "الشحن البحري"
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
        "description_en": "Travel, accommodation and visitor services",
        "description_sw": "Safari, malazi na huduma za wageni",
        "description_ar": "السفر والإقامة وخدمات الزوار",
        "children": [
            {
                "slug": "hotels",
                "name_en": "Hotels",
                "name_sw": "Hoteli",
                "name_fr": "Hôtels",
                "name_ar": "الفنادق"
            },
            {
                "slug": "travel-agencies",
                "name_en": "Travel Agencies",
                "name_sw": "Mashirika ya Safari",
                "name_fr": "Agences de voyage",
                "name_ar": "وكالات السفر"
            },
            {
                "slug": "tour-operators",
                "name_en": "Tour Operators",
                "name_sw": "Waendeshaji Utalii",
                "name_fr": "Opérateurs touristiques",
                "name_ar": "منظمو الجولات السياحية"
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
        "description_en": "Arts, entertainment, design and media production",
        "description_sw": "Sanaa, burudani, ubunifu na utengenezaji wa habari",
        "description_ar": "الفنون والترفيه والتصميم وإنتاج الإعلام",
        "children": [
            {
                "slug": "music-production",
                "name_en": "Music Production",
                "name_sw": "Uzalishaji wa Muziki",
                "name_fr": "Production musicale",
                "name_ar": "إنتاج الموسيقى"
            },
            {
                "slug": "film-production",
                "name_en": "Film Production",
                "name_sw": "Utengenezaji wa Filamu",
                "name_fr": "Production cinématographique",
                "name_ar": "إنتاج الأفلام"
            },
            {
                "slug": "graphic-design",
                "name_en": "Graphic Design",
                "name_sw": "Ubunifu wa Michoro",
                "name_fr": "Conception graphique",
                "name_ar": "التصميم الجرافيكي"
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
        "description_en": "Banking, insurance, investments and money services",
        "description_sw": "Benki, bima, uwekezaji na huduma za fedha",
        "description_ar": "الخدمات المصرفية والتأمين والاستثمار والخدمات المالية",
        "children": [
            {
                "slug": "banking",
                "name_en": "Banking",
                "name_sw": "Benki",
                "name_fr": "Banque",
                "name_ar": "الخدمات المصرفية"
            },
            {
                "slug": "insurance",
                "name_en": "Insurance",
                "name_sw": "Bima",
                "name_fr": "Assurance",
                "name_ar": "التأمين"
            },
            {
                "slug": "microfinance",
                "name_en": "Microfinance",
                "name_sw": "Fedha ndogo ndogo",
                "name_fr": "Microfinance",
                "name_ar": "التمويل الأصغر"
            },
            {
                "slug": "investments",
                "name_en": "Investments",
                "name_sw": "Uwekezaji",
                "name_fr": "Investissements",
                "name_ar": "الاستثمارات"
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
        "description_en": "Legal, accounting, consulting and business support",
        "description_sw": "Huduma za kisheria, uhasibu, ushauri na msaada wa biashara",
        "description_ar": "الخدمات القانونية والمحاسبية والاستشارية ودعم الأعمال",
        "children": [
            {
                "slug": "legal",
                "name_en": "Legal Services",
                "name_sw": "Huduma za Kisheria",
                "name_fr": "Services juridiques",
                "name_ar": "الخدمات القانونية"
            },
            {
                "slug": "accounting",
                "name_en": "Accounting",
                "name_sw": "Uhasibu",
                "name_fr": "Comptabilité",
                "name_ar": "المحاسبة"
            },
            {
                "slug": "consulting",
                "name_en": "Consulting",
                "name_sw": "Ushauri",
                "name_fr": "Conseil",
                "name_ar": "الاستشارات"
            },
            {
                "slug": "marketing",
                "name_en": "Marketing",
                "name_sw": "Masoko",
                "name_fr": "Marketing",
                "name_ar": "التسويق"
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
        "description_en": "Independent workers and small-scale traders serving their communities directly",
        "description_sw": "Wafanyakazi huru na wafanyabiashara wadogo wanaohudumia jamii zao moja kwa moja",
        "description_fr": "Travailleurs indépendants et petits commerçants au service direct de leurs communautés",
        "description_ar": "العمال المستقلون وصغار التجار الذين يخدمون مجتمعاتهم مباشرة",
        "children": [
            {
                "slug": "driver",
                "name_en": "Driver",
                "name_sw": "Dereva",
                "name_fr": "Chauffeur",
                "name_ar": "سائق"
            },
            {
                "slug": "food-vendor",
                "name_en": "Food Vendor",
                "name_sw": "Mama Ntilie",
                "name_fr": "Vendeur de Nourriture",
                "name_ar": "بائع طعام"
            },
            {
                "slug": "small-scale-farmer",
                "name_en": "Small-Scale Farmer",
                "name_sw": "Mkulima Mdogo",
                "name_fr": "Petit Agriculteur",
                "name_ar": "مزارع صغير"
            },
            {
                "slug": "artisan-repair",
                "name_en": "Artisan / Repair Technician",
                "name_sw": "Fundi",
                "name_fr": "Artisan / Réparateur",
                "name_ar": "حرفي / فني إصلاح"
            },
            {
                "slug": "small-shopkeeper",
                "name_en": "Small Shopkeeper",
                "name_sw": "Muuza Duka Mdogo",
                "name_fr": "Petit Commerçant",
                "name_ar": "بائع متجر صغير"
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
    LANGUAGES = ['sw', 'fr', 'ar']

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
