# syllabus/services/competence_tree_service.py

from typing import Dict, List, Any, Optional
from django.db.models import Prefetch
import logging

from syllabus.models.main_competence import MainCompetence
from syllabus.models.specific_competence import SpecificCompetence
from syllabus.models.learning_activity import LearningActivity
from syllabus.models.specific_learning_activity import SpecificLearningActivity
from syllabus.models.subject_version import SubjectVersion

logger = logging.getLogger(__name__)

class CompetenceTreeService:
    """
    Service to build hierarchical competence tree from SubjectVersion.
    
    Returns structure:
    {
        "subject_version_id": "uuid",
        "subject_name": "string",
        "class_level": "string",
        "competences": [
            {
                "id": "uuid",
                "name": "string",
                "order": int,
                "specific_competences": [
                    {
                        "id": "uuid",
                        "name": "string",
                        "order": int,
                        "learning_activities": [
                            {
                                "id": "uuid",
                                "name": "string",
                                "order": int,
                                "specific_learning_activities": [
                                    {
                                        "id": "uuid",
                                        "name": "string",
                                        "method": "string",
                                        "leading": "string",
                                        "assessment_criteria": "string",
                                        "teaching_aids": "string",
                                        "references": "string",
                                        "periods": int,
                                        "order": int
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    """
    
    def __init__(self, subject_version: SubjectVersion):
        self.subject_version = subject_version
        self.tree: Dict[str, Any] = {}
        self.activities: List[Dict[str, Any]] = []
    
    def build_tree(self) -> Dict[str, Any]:
        """Build hierarchical competence tree."""
        try:
            logger.info(f"Building competence tree for subject version: {self.subject_version.id}")
            
            # Get main competences with prefetched related objects
            main_competences = MainCompetence.objects.filter(
                subject_version=self.subject_version
            ).select_related('subject_version').prefetch_related(
                Prefetch(
                    'specific_competences',
                    queryset=SpecificCompetence.objects.all().prefetch_related(
                        Prefetch(
                            'learning_activities',
                            queryset=LearningActivity.objects.all().prefetch_related(
                                'specific_activities'  # Note: 'specific_activities' not 'specificlearningactivity_set'
                            )
                        )
                    )
                )
            ).order_by('order')
            
            if not main_competences.exists():
                logger.warning(f"No main competences found for subject version: {self.subject_version.id}")
                return self._build_empty_tree()
            
            competences_list = []
            
            for main_comp in main_competences:
                main_data = {
                    "id": str(main_comp.id),
                    "name": main_comp.name,
                    "order": main_comp.order,
                    "specific_competences": []
                }
                
                # Get specific competences
                specific_competences = main_comp.specific_competences.all()
                
                for spec_comp in specific_competences:
                    spec_data = {
                        "id": str(spec_comp.id),
                        "name": spec_comp.name,
                        "order": spec_comp.order,
                        "learning_activities": []
                    }
                    
                    # Get learning activities
                    learning_activities = spec_comp.learning_activities.all()
                    
                    for learn_act in learning_activities:
                        learn_data = {
                            "id": str(learn_act.id),
                            "name": learn_act.name,
                            "order": learn_act.order,
                            "specific_learning_activities": []
                        }
                        
                        # Get specific learning activities
                        specific_activities = learn_act.specific_activities.all()
                        
                        for spec_act in specific_activities:
                            activity_data = {
                                "id": str(spec_act.id),
                                "name": spec_act.name,
                                "method": spec_act.method or "Majadiliano na mazoezi",
                                "leading": spec_act.leading or "",
                                "assessment_criteria": spec_act.assessment_criteria or "Ushiriki na mazoezi",
                                "teaching_aids": spec_act.teaching_aids or "Kadi, chati, kitabu",
                                "references": spec_act.references or "Kitabu cha mwanafunzi",
                                "periods": spec_act.periods or 1,
                                "order": spec_act.order
                            }
                            learn_data["specific_learning_activities"].append(activity_data)
                        
                        spec_data["learning_activities"].append(learn_data)
                    
                    main_data["specific_competences"].append(spec_data)
                
                competences_list.append(main_data)
            
            # Build final tree
            self.tree = {
                "subject_version_id": str(self.subject_version.id),
                "subject_name": self.subject_version.subject.name,
                "class_level": self.subject_version.class_level.name,
                "competences": competences_list
            }
            
            # Log statistics
            total_activities = sum(
                len(spec_act) 
                for main in competences_list 
                for spec in main["specific_competences"] 
                for learn in spec["learning_activities"] 
                for spec_act in learn["specific_learning_activities"]
            )
            
            logger.info(
                f"Built competence tree: {len(competences_list)} main competences, "
                f"{total_activities} specific activities"
            )
            
            return self.tree
            
        except Exception as e:
            logger.error(f"Error building competence tree: {str(e)}", exc_info=True)
            return self._build_empty_tree()
    
    def _build_empty_tree(self) -> Dict[str, Any]:
        """Build empty tree structure when no competences exist."""
        return {
            "subject_version_id": str(self.subject_version.id),
            "subject_name": self.subject_version.subject.name,
            "class_level": self.subject_version.class_level.name,
            "competences": [],
            "error": "No competences found or error occurred"
        }
    
    def extract_activities_for_scheme(self) -> List[Dict[str, Any]]:
        """
        Extract activities in format needed by SchemeTimelineBuilder.
        
        Returns list of activities in the exact format SchemeTimelineBuilder expects.
        """
        if not self.tree:
            self.build_tree()
        
        self.activities = []
        activity_index = 0
        
        for main_comp in self.tree.get("competences", []):
            for spec_comp in main_comp.get("specific_competences", []):
                for learn_act in spec_comp.get("learning_activities", []):
                    for spec_act in learn_act.get("specific_learning_activities", []):
                        activity_index += 1
                        
                        activity = {
                            "index": activity_index,
                            "main_competence": main_comp.get("name", ""),
                            "main_order": main_comp.get("order", 0),
                            "specific_competence": spec_comp.get("name", ""),
                            "specific_order": spec_comp.get("order", 0),
                            "learning_activity": learn_act.get("name", ""),
                            "learning_order": learn_act.get("order", 0),
                            "specific_learning": spec_act.get("name", ""),
                            "specific_learning_order": spec_act.get("order", 0),
                            "periods_needed": spec_act.get("periods", 1),
                            "method": spec_act.get("method", "Majadiliano na mazoezi"),
                            "assessment_criteria": spec_act.get("assessment_criteria", "Ushiriki na mazoezi"),
                            "teaching_aids": spec_act.get("teaching_aids", "Kadi, chati, kitabu"),
                            "references": spec_act.get("references", "Kitabu cha mwanafunzi"),
                        }
                        
                        self.activities.append(activity)
        
        # Calculate cumulative periods
        cumulative = 0
        for activity in self.activities:
            cumulative += activity["periods_needed"]
            activity["cumulative_periods"] = cumulative
        
        logger.info(f"Extracted {len(self.activities)} activities for scheme building")
        return self.activities
    
    def get_tree_for_scheme_builder(self) -> Dict[str, Any]:
        """
        Get competence tree in format expected by SchemeTimelineBuilder.
        
        SchemeTimelineBuilder expects a tree with 'activities' key.
        """
        if not self.activities:
            self.extract_activities_for_scheme()
        
        return {
            "subject_version_id": str(self.subject_version.id),
            "subject_name": self.subject_version.subject.name,
            "class_level": self.subject_version.class_level.name,
            "activities": self.activities,
            "competences": self.tree.get("competences", []),  # Optional: keep original structure
        }
    
    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about the competence tree."""
        if not self.tree:
            self.build_tree()
        
        stats = {
            "main_competences": 0,
            "specific_competences": 0,
            "learning_activities": 0,
            "specific_learning_activities": 0,
            "total_periods": 0
        }
        
        for main_comp in self.tree.get("competences", []):
            stats["main_competences"] += 1
            
            for spec_comp in main_comp.get("specific_competences", []):
                stats["specific_competences"] += 1
                
                for learn_act in spec_comp.get("learning_activities", []):
                    stats["learning_activities"] += 1
                    
                    for spec_act in learn_act.get("specific_learning_activities", []):
                        stats["specific_learning_activities"] += 1
                        stats["total_periods"] += spec_act.get("periods", 0)
        
        return stats
    
    def get_flat_activities(self) -> List[Dict[str, Any]]:
        """Get flat list of all specific learning activities."""
        if not self.tree:
            self.build_tree()
        
        flat_list = []
        
        for main_comp in self.tree.get("competences", []):
            for spec_comp in main_comp.get("specific_competences", []):
                for learn_act in spec_comp.get("learning_activities", []):
                    for spec_act in learn_act.get("specific_learning_activities", []):
                        flat_activity = {
                            "main_competence": main_comp.get("name", ""),
                            "specific_competence": spec_comp.get("name", ""),
                            "learning_activity": learn_act.get("name", ""),
                            "specific_learning_activity": spec_act.get("name", ""),
                            "method": spec_act.get("method", ""),
                            "leading": spec_act.get("leading", ""),
                            "assessment_criteria": spec_act.get("assessment_criteria", ""),
                            "teaching_aids": spec_act.get("teaching_aids", ""),
                            "references": spec_act.get("references", ""),
                            "periods": spec_act.get("periods", 0),
                            "main_competence_order": main_comp.get("order", 0),
                            "specific_competence_order": spec_comp.get("order", 0),
                            "learning_activity_order": learn_act.get("order", 0),
                            "specific_activity_order": spec_act.get("order", 0),
                        }
                        flat_list.append(flat_activity)
        
        return flat_list
    
    def validate_tree(self) -> Dict[str, Any]:
        """Validate the competence tree structure."""
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        if not self.tree.get("competences"):
            validation["is_valid"] = False
            validation["errors"].append("No competences found")
        
        # Check for activities without periods
        for main_comp in self.tree.get("competences", []):
            for spec_comp in main_comp.get("specific_competences", []):
                for learn_act in spec_comp.get("learning_activities", []):
                    for spec_act in learn_act.get("specific_learning_activities", []):
                        if spec_act.get("periods", 0) <= 0:
                            validation["warnings"].append(
                                f"Activity '{spec_act.get('name', '')}' has 0 or negative periods"
                            )
        
        return validation