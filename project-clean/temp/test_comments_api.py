import pytest
import json
from app import create_app, db
from app.models import Publications, UserAccount, PublicationComments
from flask import Flask


@pytest.fixture
def app():
    """Create and configure test application"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def sample_data(app):
    """Create sample data for testing"""
    with app.app_context():
        # Create test user
        user = UserAccount(
            user_id=1,
            full_name="Test User",
            email="test@example.com",
            role="user"
        )
        db.session.add(user)
        
        # Create admin user
        admin = UserAccount(
            user_id=2,
            full_name="Admin User", 
            email="admin@example.com",
            role="admin"
        )
        db.session.add(admin)
        
        # Create test publication
        publication = Publications(
            id=1,
            title="Test Publication",
            status="published"
        )
        db.session.add(publication)
        
        # Create test comment
        comment = PublicationComments(
            id=1,
            publication_id=1,
            user_id=1,
            comment_text="Test comment",
            comment_type="general",
            likes_count=5
        )
        db.session.add(comment)
        
        # Create test reply
        reply = PublicationComments(
            id=2,
            publication_id=1,
            user_id=2,
            comment_text="Test reply",
            comment_type="general",
            parent_comment_id=1
        )
        db.session.add(reply)
        
        db.session.commit()
        
        return {
            'user_id': 1,
            'admin_id': 2,
            'publication_id': 1,
            'comment_id': 1,
            'reply_id': 2
        }


class TestGetPublicationComments:
    """Test GET /api/publications/<id>/comments endpoint"""
    
    def test_get_comments_success(self, client, sample_data):
        """Test successful retrieval of publication comments"""
        response = client.get(f'/api/publications/{sample_data["publication_id"]}/comments')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['publication_id'] == sample_data['publication_id']
        assert data['total_comments'] == 2
        assert len(data['comments']) == 2
        
    def test_get_comments_without_replies(self, client, sample_data):
        """Test getting comments without replies"""
        response = client.get(f'/api/publications/{sample_data["publication_id"]}/comments?include_replies=false')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_comments'] == 2
        # Should still get all comments but without nested replies
        
    def test_get_comments_nonexistent_publication(self, client, sample_data):
        """Test getting comments for non-existent publication"""
        response = client.get('/api/publications/999/comments')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'Publication not found'


class TestAddComment:
    """Test POST /api/publications/<id>/comments endpoint"""
    
    def test_add_comment_success(self, client, sample_data):
        """Test successful comment addition"""
        comment_data = {
            'user_id': sample_data['user_id'],
            'comment_text': 'New test comment',
            'comment_type': 'general'
        }
        
        response = client.post(
            f'/api/publications/{sample_data["publication_id"]}/comments',
            data=json.dumps(comment_data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == 'Comment added successfully'
        assert data['comment']['comment_text'] == 'New test comment'
        assert data['comment']['user_id'] == sample_data['user_id']
        
    def test_add_reply_success(self, client, sample_data):
        """Test successful reply addition"""
        reply_data = {
            'user_id': sample_data['user_id'],
            'comment_text': 'New reply',
            'parent_comment_id': sample_data['comment_id']
        }
        
        response = client.post(
            f'/api/publications/{sample_data["publication_id"]}/comments',
            data=json.dumps(reply_data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['comment']['parent_comment_id'] == sample_data['comment_id']
        
    def test_add_comment_missing_user_id(self, client, sample_data):
        """Test adding comment without user_id"""
        comment_data = {
            'comment_text': 'Test comment'
        }
        
        response = client.post(
            f'/api/publications/{sample_data["publication_id"]}/comments',
            data=json.dumps(comment_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'user_id is required'
        
    def test_add_comment_missing_text(self, client, sample_data):
        """Test adding comment without comment_text"""
        comment_data = {
            'user_id': sample_data['user_id']
        }
        
        response = client.post(
            f'/api/publications/{sample_data["publication_id"]}/comments',
            data=json.dumps(comment_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'comment_text is required'
        
    def test_add_comment_nonexistent_publication(self, client, sample_data):
        """Test adding comment to non-existent publication"""
        comment_data = {
            'user_id': sample_data['user_id'],
            'comment_text': 'Test comment'
        }
        
        response = client.post(
            '/api/publications/999/comments',
            data=json.dumps(comment_data),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Publication not found'
        
    def test_add_comment_nonexistent_user(self, client, sample_data):
        """Test adding comment with non-existent user"""
        comment_data = {
            'user_id': 999,
            'comment_text': 'Test comment'
        }
        
        response = client.post(
            f'/api/publications/{sample_data["publication_id"]}/comments',
            data=json.dumps(comment_data),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'User not found'
        
    def test_add_reply_nonexistent_parent(self, client, sample_data):
        """Test adding reply to non-existent parent comment"""
        reply_data = {
            'user_id': sample_data['user_id'],
            'comment_text': 'Test reply',
            'parent_comment_id': 999
        }
        
        response = client.post(
            f'/api/publications/{sample_data["publication_id"]}/comments',
            data=json.dumps(reply_data),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Parent comment not found'


class TestEditComment:
    """Test PUT /api/comments/<id> endpoint"""
    
    def test_edit_comment_success(self, client, sample_data):
        """Test successful comment editing"""
        edit_data = {
            'user_id': sample_data['user_id'],
            'comment_text': 'Updated comment text'
        }
        
        response = client.put(
            f'/api/comments/{sample_data["comment_id"]}',
            data=json.dumps(edit_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Comment updated successfully'
        assert data['comment']['comment_text'] == 'Updated comment text'
        
    def test_edit_comment_unauthorized(self, client, sample_data):
        """Test editing comment by non-author"""
        edit_data = {
            'user_id': sample_data['admin_id'],  # Different user
            'comment_text': 'Updated comment text'
        }
        
        response = client.put(
            f'/api/comments/{sample_data["comment_id"]}',
            data=json.dumps(edit_data),
            content_type='application/json'
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['error'] == 'Unauthorized: Only comment author can edit'
        
    def test_edit_comment_missing_text(self, client, sample_data):
        """Test editing comment without comment_text"""
        edit_data = {
            'user_id': sample_data['user_id']
        }
        
        response = client.put(
            f'/api/comments/{sample_data["comment_id"]}',
            data=json.dumps(edit_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'comment_text is required'
        
    def test_edit_nonexistent_comment(self, client, sample_data):
        """Test editing non-existent comment"""
        edit_data = {
            'user_id': sample_data['user_id'],
            'comment_text': 'Updated text'
        }
        
        response = client.put(
            '/api/comments/999',
            data=json.dumps(edit_data),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Comment not found'


class TestDeleteComment:
    """Test DELETE /api/comments/<id> endpoint"""
    
    def test_delete_comment_by_author(self, client, sample_data):
        """Test successful comment deletion by author"""
        delete_data = {
            'user_id': sample_data['user_id']
        }
        
        response = client.delete(
            f'/api/comments/{sample_data["comment_id"]}',
            data=json.dumps(delete_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Comment deleted successfully'
        
    def test_delete_comment_by_admin(self, client, sample_data):
        """Test successful comment deletion by admin"""
        delete_data = {
            'user_id': sample_data['admin_id']
        }
        
        response = client.delete(
            f'/api/comments/{sample_data["comment_id"]}',
            data=json.dumps(delete_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Comment deleted successfully'
        
    def test_delete_comment_unauthorized(self, client, sample_data):
        """Test deleting comment by unauthorized user"""
        # First create another regular user
        with pytest.current_app.app_context():
            other_user = UserAccount(
                user_id=3,
                full_name="Other User",
                email="other@example.com",
                role="user"
            )
            db.session.add(other_user)
            db.session.commit()
        
        delete_data = {
            'user_id': 3  # Different user, not admin
        }
        
        response = client.delete(
            f'/api/comments/{sample_data["comment_id"]}',
            data=json.dumps(delete_data),
            content_type='application/json'
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['error'] == 'Unauthorized: Only comment author or admin can delete'
        
    def test_delete_comment_missing_user_id(self, client, sample_data):
        """Test deleting comment without user_id"""
        delete_data = {}
        
        response = client.delete(
            f'/api/comments/{sample_data["comment_id"]}',
            data=json.dumps(delete_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'user_id is required'
        
    def test_delete_nonexistent_comment(self, client, sample_data):
        """Test deleting non-existent comment"""
        delete_data = {
            'user_id': sample_data['user_id']
        }
        
        response = client.delete(
            '/api/comments/999',
            data=json.dumps(delete_data),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Comment not found'
        
    def test_delete_comment_nonexistent_user(self, client, sample_data):
        """Test deleting comment with non-existent user"""
        delete_data = {
            'user_id': 999
        }
        
        response = client.delete(
            f'/api/comments/{sample_data["comment_id"]}',
            data=json.dumps(delete_data),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'User not found'


class TestLikeComment:
    """Test POST /api/comments/<id>/like endpoint"""
    
    def test_like_comment_success(self, client, sample_data):
        """Test successful comment liking"""
        response = client.post(f'/api/comments/{sample_data["comment_id"]}/like')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Comment liked successfully'
        assert data['likes_count'] == 6  # Original 5 + 1
        
    def test_like_nonexistent_comment(self, client, sample_data):
        """Test liking non-existent comment"""
        response = client.post('/api/comments/999/like')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Comment not found'


class TestGetUserComments:
    """Test GET /api/users/<id>/comments endpoint"""
    
    def test_get_user_comments_success(self, client, sample_data):
        """Test successful retrieval of user comments"""
        response = client.get(f'/api/users/{sample_data["user_id"]}/comments')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user_id'] == sample_data['user_id']
        assert data['total_comments'] == 1  # User 1 has 1 comment
        assert len(data['comments']) == 1
        
    def test_get_user_comments_nonexistent_user(self, client, sample_data):
        """Test getting comments for non-existent user"""
        response = client.get('/api/users/999/comments')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'User not found'


class TestGetCommentStats:
    """Test GET /api/comments/stats/<publication_id> endpoint"""
    
    def test_get_comment_stats_success(self, client, sample_data):
        """Test successful retrieval of comment statistics"""
        response = client.get(f'/api/comments/stats/{sample_data["publication_id"]}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['publication_id'] == sample_data['publication_id']
        
        stats = data['statistics']
        assert stats['total_comments'] == 2
        assert stats['top_level_comments'] == 1  # Only 1 comment without parent
        assert stats['replies'] == 1  # Only 1 reply
        assert stats['unique_commenters'] == 2  # 2 different users
        assert stats['total_likes'] == 5  # Only the first comment has likes
        assert stats['comment_types']['general'] == 2
        
    def test_get_comment_stats_nonexistent_publication(self, client, sample_data):
        """Test getting stats for non-existent publication"""
        response = client.get('/api/comments/stats/999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Publication not found'


class TestCommentErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_json_payload(self, client, sample_data):
        """Test handling of invalid JSON payload"""
        response = client.post(
            f'/api/publications/{sample_data["publication_id"]}/comments',
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == 400
        
    def test_empty_json_payload(self, client, sample_data):
        """Test handling of empty JSON payload"""
        response = client.post(
            f'/api/publications/{sample_data["publication_id"]}/comments',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'user_id is required'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])