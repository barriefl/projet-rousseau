from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from sqlmodel import JSON, Column, SQLModel, Field, Relationship
from enum import Enum
import uuid

class CSP(str, Enum):
    FARMER = "Agriculteurs exploitants"
    ARTISAN_MERCHANT = "Artisans, commerçants, chefs entreprise"
    EXECUTIVE = "Cadres, professions intellectuelles sup."
    EMPLOYEE_WORKER = "Employés / ouvriers"
    RETIRED = "Retraités"
    OTHER_INACTIVE = "Autres sans activité professionnelle"
    UNKNOWN = "Je ne sais pas"

class Degree(str, Enum):
    NONE = "Aucun"
    VOCATIONAL = "CAP BEP BP"
    HIGH_SCHOOL = "Bac"
    ASSOCIATE_DEGREE = "Bac+2 BTS Licence"
    MASTER_PHD = "Bac+4 Master Doctorat"
    OTHER = "Autres"
    UNKNOWN = "Je ne sais pas"

class ReadingSupport(str, Enum):
    SCREEN = "Ecran"
    PAPER = "Papier"
    MOSTLY_SCREEN = "Beaucoup écran - un peu papier"
    MOSTLY_PAPER = "Beaucoup papier - un peu écran"

class Library(str, Enum):
    YES = "Oui"
    NO = "Non"

class Platform(str, Enum):
    VOLTAIRE = "Voltaire"
    ECRIPLUS = "Ecri+"

class AssessmentType(str, Enum):
    INITIAL = "Initiale"
    FINAL = "Finale"

class Group(str, Enum):
    G0 = "G0"
    G1 = "G1"
    G2 = "G2"
    G3 = "G3"
    G4 = "G4"
    G5 = "G5"

class TimestampMixin(SQLModel):
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        description="Date de création de l'enregistrement."
    )
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
        description="Date de la dernière modification de l'enregistrement."
    )

class Student(TimestampMixin, table=True):
    __tablename__ = "students"

    id: Optional[int] = Field(default=None, primary_key=True)
    anonymous_id: uuid.UUID = Field(
        default_factory=uuid.uuid4, 
        index=True, 
        unique=True, 
        nullable=False,
        description="UUID unique pour l'anonymisation RGPD."
    )

    group: Optional[Group] = Field(default=None, index=True, description="Groupe d'étude de l'étudiant (G0-G5).")

    appetence_level: Optional[str] = Field(default=None, description="Niveau d'appétence pour la lecture (note de 1 à 5).")
    has_library: Optional[Library] = Field(default=None, description="L'étudiant a-t-il une bibliothèque chez lui ?")
    reading_support: Optional[ReadingSupport] = Field(default=None, description="Préférence de support de lecture.")
    reading_works: Optional[str] = Field(default=None, description="Liste des types d'œuvres (séparés par ;).")
    motive: Optional[str] = Field(default=None, description="Motivation de l'étudiant pour la lecture (ex: Distraction;Information).")

    parent_1_degree: Optional[Degree] = Field(default=None, description="Diplôme du parent 1.")
    parent_1_csp: Optional[CSP] = Field(default=None, description="Catégorie socioprofessionnelle du parent 1.")
    parent_2_degree: Optional[Degree] = Field(default=None, description="Diplôme du parent 2.")
    parent_2_csp: Optional[CSP] = Field(default=None, description="Catégorie socioprofessionnelle du parent 2.")

    declared_level: Optional[str] = Field(default=None, description="Niveau déclaré par l'étudiant.")

    submissions: list["Submission"] = Relationship(
        back_populates="student",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    assessments: List["AssessmentResult"] = Relationship(
        back_populates="student",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    def __repr__(self):
        return f"<Student id={self.id} group={self.group} uuid={self.anonymous_id}>"

class Dictation(TimestampMixin, table=True):
    __tablename__ = "dictations"

    id: Optional[int] = Field(default=None, primary_key=True)

    rules_config: Dict = Field(
        default={}, 
        sa_column=Column(JSON),
        description="Configuration des règles appliquées pour cette dictée."
    )

    title: str
    content_reference: str = Field(description="Texte de référence de la dictée.")

    submissions: list["Submission"] = Relationship(
        back_populates="dictation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class Submission(TimestampMixin, table=True):
    __tablename__ = "submissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="students.id")
    dictation_id: int = Field(foreign_key="dictations.id")

    assessment_type: AssessmentType
    content_student: str = Field(description="Texte soumis par l'étudiant.")
    scores: Dict = Field(
        default={}, 
        sa_column=Column(JSON),
        description="Scores détaillés. Ex: {'raw': 10, 'final': 15/20}."
    )

    student: Student = Relationship(back_populates="submissions")
    dictation: Dictation = Relationship(back_populates="submissions")
    mistakes: list["Mistake"] = Relationship(
        back_populates="submission",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class Mistake(TimestampMixin, table=True):
    __tablename__ = "mistakes"

    id: Optional[int] = Field(default=None, primary_key=True)
    submission_id: int = Field(foreign_key="submissions.id")

    student_word: str
    correct_word: str
    position_index: int = Field(description="Index de position du mot dans le texte (pour le surlignage).")
    category: str
    type_rousseau: str = Field(description="Type de faute selon la typologie demandée (D : dessin graphique du mot, S : sens, R : règle de grammaire ou de conjugaison).")
    rule_id: str
    context: str
    malus: float

    submission: Submission = Relationship(back_populates="mistakes")

class AssessmentResult(TimestampMixin, table=True):
    __tablename__ = "assessment_results"

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="students.id")

    platform: Platform
    assessment_type: AssessmentType

    score: float = Field(default=0.0)

    details: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    student: "Student" = Relationship(back_populates="assessments")