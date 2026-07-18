from django.contrib import admin

from construction.models.construction_project import ConstructionProject
from construction.models.project_bid import ProjectBid
from construction.models.project_milestone import ProjectMilestone


class ProjectBidInline(admin.TabularInline):
    model = ProjectBid
    extra = 0


class ProjectMilestoneInline(admin.TabularInline):
    model = ProjectMilestone
    extra = 0


@admin.register(ConstructionProject)
class ConstructionProjectAdmin(admin.ModelAdmin):
    list_display = ("scope_description", "client", "contractor", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("escrow_hold",)
    inlines = [ProjectBidInline, ProjectMilestoneInline]
