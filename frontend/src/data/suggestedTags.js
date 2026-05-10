// src/data/suggestedTags.js

export const SUGGESTED_TAGS_BY_CATEGORY = {
  // Hair & Beauty
  "Hair Dressing & Salon": [
    "haircut", "styling", "hair color", "braiding", "weaving",
    "treatment", "men haircut", "women haircut", "kids haircut",
    "blow dry", "hair wash", "perm", "relaxer", "extensions",
    "wig", "makeup", "bridal", "nails", "pedicure", "manicure",
    "facial", "waxing", "threading", "massage", "spa"
  ],
  
  // Restaurant & Food
  "Restaurant & Food Services": [
    "breakfast", "lunch", "dinner", "brunch", "buffet",
    "vegetarian", "vegan", "halal", "gluten-free", "organic",
    "delivery", "takeaway", "dine-in", "catering", "fast food",
    "pizza", "burger", "chicken", "seafood", "grill", "bbq",
    "african", "tanzanian", "indian", "chinese", "italian",
    "coffee", "tea", "juice", "dessert", "cake", "ice cream"
  ],
  
  // Retail
  "Retail Shop": [
    "new", "sale", "discount", "clearance", "limited edition",
    "imported", "local", "handmade", "custom", "personalized",
    "clothing", "shoes", "bags", "accessories", "jewelry",
    "electronics", "phones", "laptops", "tablets", "accessories",
    "home decor", "furniture", "kitchen", "bedding", "bath",
    "groceries", "fresh", "organic", "wholesale", "retail"
  ],
  
  // Professional Services
  "Professional Services": [
    "consulting", "advisory", "legal", "accounting", "tax",
    "audit", "bookkeeping", "business plan", "marketing",
    "branding", "design", "web development", "app development",
    "seo", "social media", "content creation", "photography",
    "videography", "printing", "copywriting", "translation"
  ],
  
  // Health & Wellness
  "Health & Wellness": [
    "doctor", "nurse", "clinic", "hospital", "pharmacy",
    "dentist", "optometrist", "physiotherapy", "chiropractor",
    "counseling", "therapy", "mental health", "nutrition",
    "dietitian", "fitness", "gym", "yoga", "pilates",
    "personal trainer", "weight loss", "wellness", "meditation"
  ],
  
  // Education & Training
  "Education & Training": [
    "tutoring", "coaching", "mentoring", "training", "workshop",
    "seminar", "webinar", "online course", "certification",
    "language", "english", "swahili", "french", "arabic",
    "math", "science", "computer", "coding", "programming",
    "driving school", "music", "art", "dance", "cooking"
  ],
  
  // Technology & IT
  "Technology & IT": [
    "software", "hardware", "networking", "cybersecurity",
    "cloud", "hosting", "domain", "email", "website",
    "mobile app", "desktop app", "saas", "api", "database",
    "repair", "maintenance", "support", "consulting", "training",
    "ai", "machine learning", "blockchain", "iot"
  ],
  
  // Construction & Real Estate
  "Construction & Real Estate": [
    "building", "renovation", "remodeling", "extension", "repair",
    "plumbing", "electrical", "painting", "carpentry", "masonry",
    "roofing", "flooring", "tiling", "landscaping", "gardening",
    "real estate", "property", "rent", "sale", "lease",
    "commercial", "residential", "land", "apartment", "house"
  ],
  
  // Transport & Logistics
  "Transport & Logistics": [
    "delivery", "shipping", "freight", "cargo", "courier",
    "taxi", "uber", "bolt", "bus", "coach",
    "truck", "van", "motorcycle", "bicycle", "car rental",
    "moving", "relocation", "storage", "warehouse", "logistics"
  ],
  
  // Entertainment & Events
  "Entertainment & Events": [
    "music", "band", "dj", "mc", "comedian",
    "event planning", "wedding", "birthday", "party", "conference",
    "decoration", "catering", "photography", "videography", "sound system",
    "lighting", "stage", "tent", "chairs", "tables"
  ],
  
  // Default for uncategorized
  "default": [
    "new", "popular", "trending", "best seller", "limited",
    "quality", "affordable", "premium", "luxury", "budget",
    "fast", "reliable", "professional", "experienced", "certified"
  ]
};

// Common tags across all categories
export const COMMON_TAGS = [
  "new", "sale", "discount", "popular", "trending",
  "quality", "affordable", "premium", "fast", "reliable"
];

// Get suggested tags for a business category
export function getSuggestedTags(categoryName) {
  if (!categoryName) return SUGGESTED_TAGS_BY_CATEGORY.default;
  
  // Try exact match
  if (SUGGESTED_TAGS_BY_CATEGORY[categoryName]) {
    return SUGGESTED_TAGS_BY_CATEGORY[categoryName];
  }
  
  // Try partial match
  for (const key of Object.keys(SUGGESTED_TAGS_BY_CATEGORY)) {
    if (categoryName.toLowerCase().includes(key.toLowerCase()) ||
        key.toLowerCase().includes(categoryName.toLowerCase())) {
      return SUGGESTED_TAGS_BY_CATEGORY[key];
    }
  }
  
  // Return default + common tags
  return [...SUGGESTED_TAGS_BY_CATEGORY.default, ...COMMON_TAGS];
}