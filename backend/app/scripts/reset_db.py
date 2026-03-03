from sqlmodel import SQLModel
from app.database import engine

from app.models import Category, Dictation, Mistake, Rule, Student, Submission, Promotion, Group

def reset_database():
    print("🗑️  Suppression de toutes les tables existantes...")
    SQLModel.metadata.drop_all(engine)
    
    print("✨ Création des nouvelles tables vierges...")
    SQLModel.metadata.create_all(engine)
    
    print("✅ Base de données réinitialisée avec succès ! Elle est totalement vide.")

if __name__ == "__main__":
    reset_database()