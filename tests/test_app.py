"""
Tests for Mergington High School API
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    from app import activities
    initial_state = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    activities.clear()
    activities.update(initial_state)


class TestGetActivities:
    """Test the GET /activities endpoint"""

    def test_get_activities_success(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_structure(self, client):
        """Test that activities have correct structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_activities_have_participants(self, client):
        """Test that activities have participants"""
        response = client.get("/activities")
        data = response.json()
        assert len(data["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]


class TestSignup:
    """Test the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant"""
        client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert "newstudent@mergington.edu" in participants

    def test_signup_duplicate_student(self, client):
        """Test that duplicate signup fails"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity(self, client):
        """Test signup for nonexistent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_multiple_students(self, client):
        """Test multiple students signing up"""
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        for email in emails:
            response = client.post(
                "/activities/Programming Class/signup",
                params={"email": email}
            )
            assert response.status_code == 200

        response = client.get("/activities")
        participants = response.json()["Programming Class"]["participants"]
        for email in emails:
            assert email in participants


class TestUnregister:
    """Test the DELETE /activities/{activity_name}/participants/{email} endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration"""
        response = client.delete(
            "/activities/Chess Club/participants/michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "unregistered" in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        client.delete(
            "/activities/Chess Club/participants/michael@mergington.edu"
        )
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert "michael@mergington.edu" not in participants

    def test_unregister_nonexistent_participant(self, client):
        """Test unregistering nonexistent participant"""
        response = client.delete(
            "/activities/Chess Club/participants/nonexistent@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Participant not found" in data["detail"]

    def test_unregister_nonexistent_activity(self, client):
        """Test unregistering from nonexistent activity"""
        response = client.delete(
            "/activities/Nonexistent Club/participants/michael@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_then_signup_again(self, client):
        """Test that a student can sign up again after unregistering"""
        # Unregister
        client.delete(
            "/activities/Chess Club/participants/michael@mergington.edu"
        )
        # Sign up again
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 200
        # Verify participant is back
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert "michael@mergington.edu" in participants


class TestIntegration:
    """Integration tests combining multiple operations"""

    def test_signup_and_unregister_workflow(self, client):
        """Test complete workflow: signup and then unregister"""
        # Initial state
        response = client.get("/activities")
        initial_count = len(response.json()["Programming Class"]["participants"])

        # Sign up
        client.post(
            "/activities/Programming Class/signup",
            params={"email": "workflow@mergington.edu"}
        )

        # Verify signup
        response = client.get("/activities")
        after_signup = len(response.json()["Programming Class"]["participants"])
        assert after_signup == initial_count + 1

        # Unregister
        client.delete(
            "/activities/Programming Class/participants/workflow@mergington.edu"
        )

        # Verify unregister
        response = client.get("/activities")
        after_unregister = len(response.json()["Programming Class"]["participants"])
        assert after_unregister == initial_count

    def test_all_activities_accessible(self, client):
        """Test that all activities are accessible and valid"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()

        for activity_name, activity_data in activities.items():
            assert activity_name is not None
            assert activity_data["description"]
            assert activity_data["schedule"]
            assert activity_data["max_participants"] > 0
            assert isinstance(activity_data["participants"], list)
