"""Tests for API endpoints (dashboard, students, marksheets, mappings)."""

from app.models import Student, Marksheet, Mark


class TestHealthCheck:
    def test_health(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestDashboardAPI:
    def test_stats_empty(self, client, auth_headers):
        response = client.get("/api/dashboard/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_students"] == 0
        assert data["total_marksheets"] == 0

    def test_stats_with_data(self, client, auth_headers, db, seed_data):
        student = Student(
            name="Test Student", roll_number="12345",
            board_id=seed_data["cbse"].id, exam_year=2024,
        )
        db.add(student)
        db.flush()

        ms = Marksheet(
            student_id=student.id, file_path="/tmp/test.jpg",
            file_name="test.jpg", file_type="jpg",
            processing_status="completed",
        )
        db.add(ms)
        db.commit()

        response = client.get("/api/dashboard/stats", headers=auth_headers)
        data = response.json()
        assert data["total_students"] == 1
        assert data["total_marksheets"] == 1


class TestStudentsAPI:
    def test_list_empty(self, client, auth_headers):
        response = client.get("/api/students", headers=auth_headers)
        assert response.status_code == 200

    def test_list_with_students(self, client, auth_headers, db, seed_data):
        db.add(Student(
            name="Rahul Sharma", roll_number="12345",
            board_id=seed_data["cbse"].id, exam_year=2024,
        ))
        db.commit()

        response = client.get("/api/students", headers=auth_headers)
        assert response.status_code == 200

    def test_search_students(self, client, auth_headers, db, seed_data):
        db.add(Student(
            name="Rahul Sharma", roll_number="12345",
            board_id=seed_data["cbse"].id, exam_year=2024,
        ))
        db.commit()

        response = client.get("/api/students?search=Rahul", headers=auth_headers)
        assert response.status_code == 200


class TestMappingsAPI:
    def test_list_mappings(self, client, auth_headers, seed_data):
        response = client.get("/api/mappings", headers=auth_headers)
        assert response.status_code == 200

    def test_create_mapping(self, client, auth_headers, seed_data):
        response = client.post("/api/mappings", json={
            "raw_text": "GANIT",
            "standard_subject_id": seed_data["math"].id,
        }, headers=auth_headers)
        assert response.status_code == 200

    def test_list_subjects(self, client, auth_headers, seed_data):
        response = client.get("/api/mappings/subjects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5

    def test_create_subject(self, client, auth_headers):
        response = client.post("/api/mappings/subjects", json={
            "name": "Biology",
            "code": "BIO",
            "category": "Science",
        }, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Biology"


class TestMarksheetsAPI:
    def test_list_empty(self, client, auth_headers):
        response = client.get("/api/marksheets", headers=auth_headers)
        assert response.status_code == 200

    def test_get_nonexistent(self, client, auth_headers):
        response = client.get("/api/marksheets/99999", headers=auth_headers)
        assert response.status_code == 404
