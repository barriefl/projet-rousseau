from enum import Enum


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


class MistakeType(str, Enum):
    D = "Dessin"
    S = "Sens"
    R = "Règle"
    AUTRE = "Autre"
