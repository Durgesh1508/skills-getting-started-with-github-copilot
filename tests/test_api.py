"""
Comprehensive edge case and validation tests for FastAPI endpoints.
Tests focus on error conditions, boundary cases, and validation.
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client):
        """Should return all activities with correct structure."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_response_structure(self, client):
        """Should return activities with all required fields."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_get_activities_participants_count(self, client):
        """Should correctly reflect participant counts."""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club should have 2 participants (at capacity)
        assert len(data["Chess Club"]["participants"]) == 2
        # Programming Class should have 1 participant
        assert len(data["Programming Class"]["participants"]) == 1
        # Gym Class should have 0 participants
        assert len(data["Gym Class"]["participants"]) == 0


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success(self, client):
        """Should successfully sign up a student for an activity with available spots."""
        response = client.post(
            "/activities/Gym%20Class/signup",
            params={"email": "john@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "john@mergington.edu" in data["message"]
        assert "Gym Class" in data["message"]
    
    def test_signup_nonexistent_activity(self, client):
        """Should return 404 when signing up for non-existent activity."""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_duplicate_registration(self, client):
        """Should return 400 when student tries to sign up twice for same activity."""
        # First signup (Michael already signed up for Chess Club in fixtures)
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_activity_at_capacity(self, client):
        """Should return 400 when activity is at full capacity."""
        # Chess Club has max_participants=2 and already has 2 participants
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 400
        assert "full capacity" in response.json()["detail"]
    
    def test_signup_missing_email_parameter(self, client):
        """Should return 422 when email parameter is missing."""
        response = client.post("/activities/Gym%20Class/signup")
        assert response.status_code == 422
    
    def test_signup_with_special_characters_in_activity_name(self, client):
        """Should handle activity names with special characters correctly."""
        response = client.post(
            "/activities/Gym%20Class/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 200
    
    def test_signup_case_sensitivity_in_activity_name(self, client):
        """Should respect case sensitivity in activity names."""
        response = client.post(
            "/activities/gym%20class/signup",  # lowercase
            params={"email": "student@mergington.edu"}
        )
        # Should fail - activity name is "Gym Class" not "gym class"
        assert response.status_code == 404
    
    def test_signup_multiple_students_same_activity(self, client):
        """Should allow multiple different students to sign up."""
        # Sign up first student
        response1 = client.post(
            "/activities/Gym%20Class/signup",
            params={"email": "student1@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Sign up second student
        response2 = client.post(
            "/activities/Gym%20Class/signup",
            params={"email": "student2@mergington.edu"}
        )
        assert response2.status_code == 200
        
        # Verify both are registered
        activities = client.get("/activities").json()
        gym_participants = activities["Gym Class"]["participants"]
        assert "student1@mergington.edu" in gym_participants
        assert "student2@mergington.edu" in gym_participants


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/remove endpoint."""
    
    def test_remove_participant_success(self, client):
        """Should successfully remove a participant from an activity."""
        response = client.delete(
            "/activities/Chess%20Club/remove",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]
        
        # Verify participant is removed
        activities = client.get("/activities").json()
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
    
    def test_remove_from_nonexistent_activity(self, client):
        """Should return 404 when removing from non-existent activity."""
        response = client.delete(
            "/activities/Nonexistent%20Activity/remove",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_remove_nonexistent_participant(self, client):
        """Should return 404 when trying to remove participant not in activity."""
        response = client.delete(
            "/activities/Chess%20Club/remove",
            params={"email": "nonexistent@mergington.edu"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_remove_from_empty_activity(self, client):
        """Should return 404 when trying to remove from activity with no participants."""
        response = client.delete(
            "/activities/Gym%20Class/remove",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
    
    def test_remove_missing_email_parameter(self, client):
        """Should return 422 when email parameter is missing."""
        response = client.delete("/activities/Chess%20Club/remove")
        assert response.status_code == 422
    
    def test_remove_case_sensitivity_in_activity_name(self, client):
        """Should respect case sensitivity in activity names."""
        response = client.delete(
            "/activities/chess%20club/remove",  # lowercase
            params={"email": "michael@mergington.edu"}
        )
        # Should fail - activity name is "Chess Club" not "chess club"
        assert response.status_code == 404
    
    def test_remove_then_signup_again(self, client):
        """Should allow re-signup after removal."""
        # Remove participant
        remove_response = client.delete(
            "/activities/Chess%20Club/remove",
            params={"email": "michael@mergington.edu"}
        )
        assert remove_response.status_code == 200
        
        # Sign up again
        signup_response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert signup_response.status_code == 200
        
        # Verify participant is back
        activities = client.get("/activities").json()
        assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
    
    def test_remove_creates_capacity_for_new_signup(self, client):
        """Should free up capacity when removing a participant."""
        # Chess Club is at capacity
        assert len(client.get("/activities").json()["Chess Club"]["participants"]) == 2
        
        # Remove one participant
        client.delete(
            "/activities/Chess%20Club/remove",
            params={"email": "michael@mergington.edu"}
        )
        
        # New signup should now succeed
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
