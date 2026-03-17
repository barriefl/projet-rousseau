import csv
import io
from typing import Any, Dict, List

from sqlmodel import Session, select

from app.models import Group, Student
from app.models.entities import Tool
from app.schemas.import_schema import (
    CsvRowData,
    ImportExecuteRequest,
    ImportPreviewResponse,
    StudentMatchPreview,
)
from app.utils.crypto import decrypt_text, encrypt_text
from app.utils.import_utils import is_fuzzy_match, normalize_text, sort_semicolon_list


class ImportService:
    def __init__(self, session: Session):
        self.session = session

    def _get_or_create_default_tool(self) -> int:
        """Récupère le premier outil disponible ou en crée un par défaut."""
        tool = self.session.exec(select(Tool)).first()

        if not tool:
            tool = Tool(name="PV", full_name="Projet Voltaire")
            self.session.add(tool)
            self.session.flush()

        return tool.id

    def _parse_csv(self, file_content: bytes) -> List[CsvRowData]:
        """Convertit le fichier CSV en liste d'objets Pydantic."""
        try:
            csv_text = file_content.decode("utf-8-sig")
        except UnicodeDecodeError:
            csv_text = file_content.decode("cp1252", errors="replace")

        reader = csv.DictReader(io.StringIO(csv_text), delimiter=";")

        parsed_data = []
        for row in reader:
            data = CsvRowData(
                first_name=row.get("16. prenom", "").strip(),
                last_name=row.get("15. nom", "").strip(),
                group_name=row.get("17. groupe", "").strip(),
                appetence_level=row.get(
                    "1. Comment_evaluez-vous_votre_gout_personne", ""
                ).strip(),
                reading_works=row.get("2. oeuvres", "").strip(),
                motive=row.get("3. motif", "").strip(),
                reading_support=row.get("4. support", "").strip(),
                declared_level=row.get("5. niveau", "").strip(),
                parent_1_degree=row.get("10. diplome_parent_1", "").strip(),
                parent_2_degree=row.get("11. diplome_parent_2", "").strip(),
                parent_1_csp=row.get("12. CSP_parent1", "").strip(),
                parent_2_csp=row.get("13. CSP_parent2", "").strip(),
                has_library=row.get("14. bibliotheque", "").strip(),
            )
            if data.first_name and data.last_name:
                parsed_data.append(data)

        return parsed_data

    def analyze_import(
        self, promotion_id: int, file_content: bytes
    ) -> ImportPreviewResponse:
        """Étape 1 : Analyse le CSV sans rien sauvegarder (Preview)."""
        csv_rows = self._parse_csv(file_content)

        existing_groups = self.session.exec(select(Group)).all()
        group_names_db = {normalize_text(g.name): g for g in existing_groups}

        existing_students = self.session.exec(
            select(Student).where(Student.promotion_id == promotion_id)
        ).all()

        db_students_decrypted = []
        for s in existing_students:
            db_students_decrypted.append(
                {
                    "student": s,
                    "norm_first": normalize_text(decrypt_text(s.first_name_encrypted)),
                    "norm_last": normalize_text(decrypt_text(s.last_name_encrypted)),
                }
            )

        groups_to_create = set()
        exact_matches = []
        fuzzy_matches = []
        new_students = []

        for row in csv_rows:
            if row.group_name:
                norm_group = normalize_text(row.group_name)
                if norm_group and norm_group not in group_names_db:
                    groups_to_create.add(row.group_name)

            norm_csv_first = normalize_text(row.first_name)
            norm_csv_last = normalize_text(row.last_name)

            match_found = False
            for db_s in db_students_decrypted:
                if (
                    norm_csv_first == db_s["norm_first"]
                    and norm_csv_last == db_s["norm_last"]
                ):
                    exact_matches.append(
                        StudentMatchPreview(
                            csv_data=row,
                            match_type="exact",
                            db_student_id=db_s["student"].id,
                            db_first_name=decrypt_text(
                                db_s["student"].first_name_encrypted
                            ),
                            db_last_name=decrypt_text(
                                db_s["student"].last_name_encrypted
                            ),
                        )
                    )
                    match_found = True
                    break

                elif is_fuzzy_match(
                    norm_csv_first, db_s["norm_first"]
                ) and is_fuzzy_match(norm_csv_last, db_s["norm_last"]):
                    fuzzy_matches.append(
                        StudentMatchPreview(
                            csv_data=row,
                            match_type="fuzzy",
                            db_student_id=db_s["student"].id,
                            db_first_name=decrypt_text(
                                db_s["student"].first_name_encrypted
                            ),
                            db_last_name=decrypt_text(
                                db_s["student"].last_name_encrypted
                            ),
                        )
                    )
                    match_found = True
                    break

            if not match_found:
                new_students.append(StudentMatchPreview(csv_data=row, match_type="new"))

        return ImportPreviewResponse(
            promotion_id=promotion_id,
            groups_to_create=list(groups_to_create),
            exact_matches=exact_matches,
            fuzzy_matches=fuzzy_matches,
            new_students=new_students,
        )

    def execute_import(self, request: ImportExecuteRequest) -> Dict[str, Any]:
        """Étape 3 : Exécute l'importation validée avec une transaction stricte."""
        try:
            existing_groups = self.session.exec(select(Group)).all()
            group_map = {normalize_text(g.name): g for g in existing_groups}

            if request.create_missing_groups:
                csv_group_names = set(
                    s.csv_data.group_name
                    for s in request.students
                    if s.csv_data.group_name
                )
                for g_name in csv_group_names:
                    if normalize_text(g_name) not in group_map:
                        new_group = Group(name=g_name)
                        self.session.add(new_group)
                        self.session.flush()
                        group_map[normalize_text(g_name)] = new_group

            created_count = 0
            updated_count = 0

            for action_req in request.students:
                csv_data = action_req.csv_data

                group_id = None
                if csv_data.group_name:
                    group_obj = group_map.get(normalize_text(csv_data.group_name))
                    group_id = group_obj.id if group_obj else None

                student_data = {
                    "promotion_id": request.promotion_id,
                    "group_id": group_id,
                    "tool_id": request.tool_id,
                    "first_name_encrypted": encrypt_text(csv_data.first_name.title()),
                    "last_name_encrypted": encrypt_text(csv_data.last_name.upper()),
                    "appetence_level": csv_data.appetence_level or None,
                    "reading_works": sort_semicolon_list(csv_data.reading_works),
                    "motive": sort_semicolon_list(csv_data.motive),
                    "reading_support": csv_data.reading_support or None,
                    "declared_level": csv_data.declared_level or None,
                    "parent_1_degree": csv_data.parent_1_degree or None,
                    "parent_2_degree": csv_data.parent_2_degree or None,
                    "parent_1_csp": csv_data.parent_1_csp or None,
                    "parent_2_csp": csv_data.parent_2_csp or None,
                    "has_library": csv_data.has_library or None,
                }

                if action_req.action == "update" and action_req.db_student_id:
                    student = self.session.get(Student, action_req.db_student_id)
                    if student:
                        for key, value in student_data.items():
                            setattr(student, key, value)
                        self.session.add(student)
                        updated_count += 1
                else:
                    new_student = Student(**student_data)
                    self.session.add(new_student)
                    created_count += 1

            self.session.commit()

            return {
                "status": "success",
                "created": created_count,
                "updated": updated_count,
            }

        except Exception as e:
            self.session.rollback()
            raise e
