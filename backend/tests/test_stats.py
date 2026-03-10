from fastapi import status


def test_get_rousseau_stats_empty_db(auth_client):
    """
    Vérifie que l'endpoint Rousseau renvoie un 200 OK et une structure JSON valide (avec des listes vides) quand il n'y a aucun étudiant.
    """

    # ACT.
    response = auth_client.get("/api/stats/rousseau")

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK, (
        f"Erreur de l'API: {response.text}"
    )

    data = response.json()

    expected_keys = [
        "h1_summary",
        "h2_equivalence",
        "h2_boxplots",
        "h2_stats_test",
        "h3_teacher",
        "h4_sociocultural",
        "regression_model",
    ]
    for key in expected_keys:
        assert key in data, f"La clé {key} est manquante dans la réponse"

    assert data["h1_summary"]["labels"] == []
    assert data["h1_summary"]["dictation_initial"] == []
    assert data["h1_summary"]["dictation_final"] == []
    assert data["h1_summary"]["tools_initial"] == []
    assert data["h1_summary"]["tools_final"] == []
    assert data["h1_summary"]["effectif"] == []

    assert data["h2_equivalence"]["labels"] == []
    assert data["h2_equivalence"]["g2_final"] == []
    assert data["h2_equivalence"]["g2_progress"] == []
    assert data["h2_equivalence"]["g5_final"] == []
    assert data["h2_equivalence"]["g5_progress"] == []
    assert data["h2_equivalence"]["effectif"] == []

    assert data["h2_boxplots"] == {}

    assert data["h3_teacher"]["Accompagnement Humain (G4)"]["score"] == 0.0
    assert data["h3_teacher"]["Accompagnement Humain (G4)"]["effectif"] == 0.0
    assert data["h3_teacher"]["Autonomie / Outils (G2/G3/G5)"]["score"] == 0.0
    assert data["h3_teacher"]["Autonomie / Outils (G2/G3/G5)"]["effectif"] == 0.0

    assert data["h4_sociocultural"]["Catégorie socio-culturelle"]["CSP Parents"] == {}
    assert data["h4_sociocultural"]["Catégorie socio-culturelle"]["Diplôme Parents"] == {}
    assert data["h4_sociocultural"]["Pratique de la lecture"]["Appétence"] == {}
    assert data["h4_sociocultural"]["Pratique de la lecture"]["Bibliothèque"] == {}
    assert data["h4_sociocultural"]["Pratique de la lecture"]["Support"] == {}
    assert data["h4_sociocultural"]["Pratique de la lecture"]["Œuvres lues"] == {}
    assert data["h4_sociocultural"]["Pratique de la lecture"]["Motifs"] == {}
    assert data["h4_sociocultural"]["Orthographe, grammaire, conjugaison"]["Niveau déclaré"] == {}

    assert data["regression_model"]["r2"] == 0.0
    assert data["regression_model"]["coefficients"] == []
