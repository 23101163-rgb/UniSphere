from django.contrib import admin
from .models import (
    ResearchGroup,
    SupervisorRequest,
    KnowledgeAssessment,
    AssessmentQuestion,
    AssessmentSubmission,
    ReferencePaper,
    ResearchPaper,
    PaperReview
)

admin.site.register(ResearchGroup)
admin.site.register(SupervisorRequest)
admin.site.register(KnowledgeAssessment)
admin.site.register(AssessmentQuestion)
admin.site.register(AssessmentSubmission)
admin.site.register(ReferencePaper)
admin.site.register(ResearchPaper)
admin.site.register(PaperReview)