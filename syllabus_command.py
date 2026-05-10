import os
import re
import logging
import spacy
import fitz
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from django.core.management.base import BaseCommand
from django.db import transaction
from syllabus.models import (
    ClassLevel, Masomo, MainCompetence, SpecificCompetence, 
    Activities, SpecificActivities, Methodology, SyllabusVersion
)
from concurrent.futures import ThreadPoolExecutor
import pdfplumber

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "AI-powered syllabus extraction and hierarchical data insertion."

    def add_arguments(self, parser):
        parser.add_argument('--pdf-folder', type=str, default="syllabus_pdfs/", help="Folder containing PDFs")

    def handle(self, *args, **kwargs):
        pdf_folder = kwargs['pdf_folder']
        logger.info(f"Processing syllabus PDFs from: {pdf_folder}")

        # Process PDFs concurrently
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(self.process_pdf, os.path.join(pdf_folder, filename)) 
                       for filename in os.listdir(pdf_folder) if filename.endswith(".pdf")]
            for future in futures:
                future.result()  # Wait for all tasks to complete

        logger.info("Syllabus extraction completed.")

    def process_pdf(self, pdf_path):
        """Extracts and processes syllabus data from a PDF using a hybrid approach."""
        logger.info(f"Processing: {pdf_path}")

        try:
            # Extract text and tables
            text = self.extract_text_from_pdf(pdf_path)
            tables = self.extract_tables_from_pdf(pdf_path)

            # Parse text and tables using AI and rule-based methods
            data = self.parse_text_and_tables(text, tables)

            if data:
                self.save_to_db(data)  # Save data using AI-driven hierarchical insertion
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}", exc_info=True)

    def extract_text_from_pdf(self, pdf_path):
        """Extracts text from a PDF using PyMuPDF."""
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text("text") + "\n"
        return text

    def extract_tables_from_pdf(self, pdf_path):
        """Extracts tables from a PDF using pdfplumber."""
        tables = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables()
                if page_tables:
                    tables.extend(page_tables)
        return tables

    def parse_text_and_tables(self, text, tables):
        """Uses AI and rule-based methods to extract structured syllabus data."""
        # Extract class and subject using regex (rule-based)
        class_match = re.search(r'(Class|Darasa):\s*(.+)', text)
        subject_match = re.search(r'(Subject|Somo):\s*(.+)', text)

        # Extract entities using spaCy (AI-driven)
        doc = nlp(text)
        competencies = [ent.text for ent in doc.ents if ent.label_ in ["ORG", "PRODUCT"]]
        specific_competences = [ent.text for ent in doc.ents if ent.label_ == "SPECIFIC_COMPETENCE"]
        activities = [ent.text for ent in doc.ents if ent.label_ == "ACTIVITY"]
        specific_activities = [ent.text for ent in doc.ents if ent.label_ == "SPECIFIC_ACTIVITY"]
        methodologies = [ent.text for ent in doc.ents if ent.label_ == "METHODOLOGY"]

        # Parse tables (rule-based)
        for table in tables:
            for row in table:
                if len(row) >= 5:
                    main_comp, spec_comp, activity, spec_act, methodology = row[:5]
                    if main_comp:
                        competencies.append(main_comp.strip())
                    if spec_comp:
                        specific_competences.append(spec_comp.strip())
                    if activity:
                        activities.append(activity.strip())
                    if spec_act:
                        specific_activities.append(spec_act.strip())
                    if methodology:
                        methodologies.append(methodology.strip())

        return {
            "class": class_match.group(2).strip() if class_match else None,
            "subject": subject_match.group(2).strip() if subject_match else None,
            "competencies": competencies,
            "specific_competences": specific_competences,
            "activities": activities,
            "specific_activities": specific_activities,
            "methodologies": methodologies,
        }

    def get_class_short_form(self, class_name):
        """Generates a standardized short form using a hybrid approach."""
        # Rule-based logic for extracting numbers
        num_match = re.search(r'\d+', class_name)
        if num_match:
            num = num_match.group()
            return f"STD {num}" if "Class" in class_name else f"DRS {num}"
        else:
            # Fallback to AI-based short form generation (placeholder)
            return class_name[:5].upper()

    def handle_duplicate_methodology(self, method, specific_activity):
        """
        Checks if a methodology with the same name already exists under the same SpecificActivity.
        If it does, return the existing methodology. Otherwise, create a new one.
        """
        # Check if the methodology already exists under the same SpecificActivity
        existing_method = Methodology.objects.filter(
            specificactivity=specific_activity,
            name=method
        ).first()
    
        if existing_method:
            # If it exists under the same SpecificActivity, return the existing one
            return existing_method.name
        else:
            # If it doesn't exist under the same SpecificActivity, create a new one
            Methodology.objects.create(specificactivity=specific_activity, name=method)
            return method

    @transaction.atomic
    def save_to_db(self, data):
        """Saves hierarchical data to the database using a hybrid approach."""
        try:
            class_short_form = self.get_class_short_form(data["class"])
    
            # Save Class Level
            class_level, _ = ClassLevel.objects.get_or_create(name=data["class"])
    
            # Save Subject
            subject, _ = Masomo.objects.get_or_create(classlevel=class_level, name=f"{data['subject']}_{class_short_form}")
    
            # Save MainCompetence
            for comp in data["competencies"]:
                main_comp, _ = MainCompetence.objects.get_or_create(somo=subject, name=f"{comp}_{class_short_form}")
    
                # Save SpecificCompetence
                for spec_comp in data["specific_competences"]:
                    spec_comp, _ = SpecificCompetence.objects.get_or_create(maincompetence=main_comp, name=f"{spec_comp}_{class_short_form}")
    
                    # Save Activities
                    for act in data["activities"]:
                        activity, _ = Activities.objects.get_or_create(specificcompetence=spec_comp, name=f"{act}_{class_short_form}")
    
                        # Save SpecificActivities
                        for spec_act in data["specific_activities"]:
                            spec_act, _ = SpecificActivities.objects.get_or_create(activity=activity, name=f"{spec_act}_{class_short_form}")
    
                            # Save Methodology
                            for method in data["methodologies"]:
                                method_name = self.handle_duplicate_methodology(method, spec_act)
                                # No need to call Methodology.objects.get_or_create here since it's handled in handle_duplicate_methodology
    
            logger.info(f"✅ Saved {data['class']} - {data['subject']} with full hierarchy!")
        except Exception as e:
            logger.error(f"❌ Failed to save full data: {e}", exc_info=True)
            raise