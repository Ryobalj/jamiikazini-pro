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
        "description_en": "Food staples, groceries and cooking essentials",
        "description_sw": "Vyakula vya kila siku, chakula cha dukani na vya kupikia",
        "description_ar": "المواد الغذائية الأساسية ولوازم الطبخ",
        "children": [
            {"slug": "nafaka-unga", "name_en": "Grains & Flour", "name_sw": "Nafaka na Unga", "name_fr": "Céréales et farine", "name_ar": "الحبوب والدقيق"},
            {"slug": "mafuta-kupikia", "name_en": "Cooking Oil", "name_sw": "Mafuta ya Kupikia", "name_fr": "Huile de cuisson", "name_ar": "زيت الطبخ"},
            {"slug": "vyakula-makopo", "name_en": "Canned & Packaged Foods", "name_sw": "Vyakula vya Makopo", "name_fr": "Aliments en conserve", "name_ar": "الأغذية المعلبة والمعبأة"},
            {"slug": "viungo", "name_en": "Spices & Condiments", "name_sw": "Viungo", "name_fr": "Épices", "name_ar": "التوابل"},
        ],
    },
    {
        "slug": "vinywaji",
        "name_en": "Beverages",
        "name_sw": "Vinywaji",
        "name_fr": "Boissons",
        "name_ar": "المشروبات",
        "description_en": "Drinks - soft drinks, water, tea and coffee",
        "description_sw": "Soda, maji, chai na kahawa",
        "description_ar": "المشروبات الغازية والماء والشاي والقهوة",
        "children": [
            {"slug": "soda-juisi", "name_en": "Soft Drinks & Juice", "name_sw": "Soda na Juisi", "name_fr": "Sodas et jus", "name_ar": "المشروبات الغازية والعصائر"},
            {"slug": "maji", "name_en": "Water", "name_sw": "Maji", "name_fr": "Eau", "name_ar": "الماء"},
            {"slug": "chai-kahawa", "name_en": "Tea & Coffee", "name_sw": "Chai na Kahawa", "name_fr": "Thé et café", "name_ar": "الشاي والقهوة"},
        ],
    },
    {
        "slug": "nguo-mavazi",
        "name_en": "Clothing & Apparel",
        "name_sw": "Nguo na Mavazi",
        "name_fr": "Vêtements",
        "name_ar": "الملابس والأزياء",
        "description_en": "Clothes, shoes and fashion accessories",
        "description_sw": "Nguo, viatu na vifaa vya mavazi",
        "description_ar": "الملابس والأحذية وإكسسوارات الأزياء",
        "children": [
            {"slug": "nguo-wanaume", "name_en": "Men's Clothing", "name_sw": "Nguo za Wanaume", "name_fr": "Vêtements pour hommes", "name_ar": "ملابس رجالية"},
            {"slug": "nguo-wanawake", "name_en": "Women's Clothing", "name_sw": "Nguo za Wanawake", "name_fr": "Vêtements pour femmes", "name_ar": "ملابس نسائية"},
            {"slug": "nguo-watoto", "name_en": "Children's Clothing", "name_sw": "Nguo za Watoto", "name_fr": "Vêtements pour enfants", "name_ar": "ملابس أطفال"},
            {"slug": "viatu", "name_en": "Shoes", "name_sw": "Viatu", "name_fr": "Chaussures", "name_ar": "الأحذية"},
        ],
    },
    {
        "slug": "vifaa-nyumbani",
        "name_en": "Household Items",
        "name_sw": "Vifaa vya Nyumbani",
        "name_fr": "Articles ménagers",
        "name_ar": "مستلزمات منزلية",
        "description_en": "Furniture, kitchenware and cleaning supplies",
        "description_sw": "Samani, vyombo vya jikoni na vifaa vya kusafisha",
        "description_ar": "الأثاث وأدوات المطبخ ومستلزمات التنظيف",
        "children": [
            {"slug": "samani", "name_en": "Furniture", "name_sw": "Samani", "name_fr": "Meubles", "name_ar": "الأثاث"},
            {"slug": "vyombo-jikoni", "name_en": "Kitchenware", "name_sw": "Vyombo vya Jikoni", "name_fr": "Ustensiles de cuisine", "name_ar": "أدوات المطبخ"},
            {"slug": "vifaa-kusafisha", "name_en": "Cleaning Supplies", "name_sw": "Vifaa vya Kusafisha", "name_fr": "Produits de nettoyage", "name_ar": "مستلزمات التنظيف"},
        ],
    },
    {
        "slug": "elektroniki",
        "name_en": "Electronics",
        "name_sw": "Elektroniki",
        "name_fr": "Électronique",
        "name_ar": "الإلكترونيات",
        "description_en": "Phones, computers and electrical equipment",
        "description_sw": "Simu, kompyuta na vifaa vya umeme",
        "description_ar": "الهواتف والحواسيب والأجهزة الكهربائية",
        "children": [
            {"slug": "simu-vifaa", "name_en": "Phones & Accessories", "name_sw": "Simu na Vifaa", "name_fr": "Téléphones et accessoires", "name_ar": "الهواتف والملحقات"},
            {"slug": "kompyuta", "name_en": "Computers", "name_sw": "Kompyuta", "name_fr": "Ordinateurs", "name_ar": "الحواسيب"},
            {"slug": "vifaa-umeme", "name_en": "Electrical Appliances", "name_sw": "Vifaa vya Umeme", "name_fr": "Appareils électriques", "name_ar": "الأجهزة الكهربائية"},
        ],
    },
    {
        "slug": "vipodozi-urembo",
        "name_en": "Cosmetics & Beauty",
        "name_sw": "Vipodozi na Urembo",
        "name_fr": "Cosmétiques et beauté",
        "name_ar": "مستحضرات التجميل والجمال",
        "description_en": "Cosmetics, perfumes and hair products",
        "description_sw": "Vipodozi, manukato na bidhaa za nywele",
        "description_ar": "مستحضرات التجميل والعطور ومنتجات الشعر",
        "children": [
            {"slug": "vipodozi", "name_en": "Cosmetics", "name_sw": "Vipodozi", "name_fr": "Cosmétiques", "name_ar": "مستحضرات التجميل"},
            {"slug": "manukato", "name_en": "Perfumes", "name_sw": "Manukato", "name_fr": "Parfums", "name_ar": "العطور"},
            {"slug": "bidhaa-nywele", "name_en": "Hair Products", "name_sw": "Bidhaa za Nywele", "name_fr": "Produits capillaires", "name_ar": "منتجات الشعر"},
        ],
    },
    {
        "slug": "afya-dawa",
        "name_en": "Health & Medicine",
        "name_sw": "Afya na Dawa",
        "name_fr": "Santé et médicaments",
        "name_ar": "الصحة والدواء",
        "description_en": "Medicines and health products",
        "description_sw": "Dawa na bidhaa za afya",
        "description_ar": "الأدوية والمنتجات الصحية",
        "children": [
            {"slug": "dawa", "name_en": "Medicines", "name_sw": "Dawa", "name_fr": "Médicaments", "name_ar": "الأدوية"},
            {"slug": "bidhaa-afya", "name_en": "Health Products", "name_sw": "Bidhaa za Afya", "name_fr": "Produits de santé", "name_ar": "منتجات صحية"},
        ],
    },
    {
        "slug": "kilimo-mifugo",
        "name_en": "Agriculture & Livestock",
        "name_sw": "Kilimo na Mifugo",
        "name_fr": "Agriculture et élevage",
        "name_ar": "الزراعة والثروة الحيوانية",
        "description_en": "Seeds, fertilizer and farming/livestock supplies",
        "description_sw": "Mbegu, mbolea na vifaa vya kilimo na ufugaji",
        "description_ar": "البذور والأسمدة ولوازم الزراعة والثروة الحيوانية",
        "children": [
            {"slug": "mbegu-mbolea", "name_en": "Seeds & Fertilizer", "name_sw": "Mbegu na Mbolea", "name_fr": "Semences et engrais", "name_ar": "البذور والأسمدة"},
            {"slug": "dawa-kilimo", "name_en": "Agro-chemicals", "name_sw": "Dawa za Kilimo", "name_fr": "Produits agrochimiques", "name_ar": "المواد الكيميائية الزراعية"},
            {"slug": "vifaa-kilimo", "name_en": "Farm Equipment", "name_sw": "Vifaa vya Kilimo", "name_fr": "Équipement agricole", "name_ar": "معدات المزرعة"},
        ],
    },
    {
        "slug": "zana-vifaa-kazi",
        "name_en": "Tools & Equipment",
        "name_sw": "Zana na Vifaa vya Kazi",
        "name_fr": "Outils et équipement",
        "name_ar": "الأدوات والمعدات",
        "description_en": "Construction and artisan tools",
        "description_sw": "Zana za ujenzi na za mafundi",
        "description_ar": "أدوات البناء وأدوات الحرفيين",
        "children": [
            {"slug": "zana-ujenzi", "name_en": "Construction Tools", "name_sw": "Zana za Ujenzi", "name_fr": "Outils de construction", "name_ar": "أدوات البناء"},
            {"slug": "zana-mafundi", "name_en": "Artisan Tools", "name_sw": "Zana za Mafundi", "name_fr": "Outils d'artisan", "name_ar": "أدوات الحرفيين"},
        ],
    },
    {
        "slug": "huduma",
        "name_en": "Services",
        "name_sw": "Huduma",
        "name_fr": "Services",
        "name_ar": "الخدمات",
        "description_en": "Repair, cleaning and skilled trade services",
        "description_sw": "Huduma za ukarabati, usafi na ufundi",
        "description_ar": "خدمات الإصلاح والتنظيف والحرف المهنية",
        "children": [
            {"slug": "huduma-ukarabati", "name_en": "Repair Services", "name_sw": "Huduma za Ukarabati", "name_fr": "Services de réparation", "name_ar": "خدمات الإصلاح"},
            {"slug": "huduma-usafi", "name_en": "Cleaning Services", "name_sw": "Huduma za Usafi", "name_fr": "Services de nettoyage", "name_ar": "خدمات التنظيف"},
            {"slug": "huduma-ufundi", "name_en": "Skilled Trade Services", "name_sw": "Huduma za Ufundi", "name_fr": "Services d'artisanat", "name_ar": "خدمات الحرف المهنية"},
        ],
    },
    {
        "slug": "vitabu-elimu",
        "name_en": "Books & Stationery",
        "name_sw": "Vitabu na Vifaa vya Elimu",
        "name_fr": "Livres et papeterie",
        "name_ar": "الكتب والقرطاسية",
        "description_en": "Books, stationery and school supplies",
        "description_sw": "Vitabu, vifaa vya ofisi na shule",
        "description_ar": "الكتب والقرطاسية ومستلزمات المدرسة",
        "children": [],
    },
    {
        "slug": "michezo-burudani",
        "name_en": "Sports & Entertainment",
        "name_sw": "Michezo na Burudani",
        "name_fr": "Sport et loisirs",
        "name_ar": "الرياضة والترفيه",
        "description_en": "Sporting goods and entertainment items",
        "description_sw": "Bidhaa za michezo na burudani",
        "description_ar": "أدوات رياضية ومستلزمات ترفيهية",
        "children": [],
    },
]


class Command(BaseCommand):
    help = "Seed Product Categories with translations and hierarchy"

    LANGUAGES = ['sw', 'fr', 'ar']
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
