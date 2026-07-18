# homepage/admin.py

from django.contrib import admin

from homepage.models import (
    HomePage, HeroSection, AboutSection, AboutImage,
    WhatWeDo, WhatWeDoService, WhatWeDoImage, Faq, Testimonial,
)

admin.site.register(HomePage)
admin.site.register(HeroSection)
admin.site.register(AboutSection)
admin.site.register(AboutImage)
admin.site.register(WhatWeDo)
admin.site.register(WhatWeDoService)
admin.site.register(WhatWeDoImage)
admin.site.register(Faq)
admin.site.register(Testimonial)
