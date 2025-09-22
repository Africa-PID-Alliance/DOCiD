"""
API endpoints for publication comments
"""
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from app import db
from app.models import PublicationComments, Publications, UserAccount
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create Blueprint
comments_bp = Blueprint('comments', __name__)

@comments_bp.route('/api/publications/<int:publication_id>/comments', methods=['GET'])
@cross_origin()
def get_publication_comments(publication_id):
    """
    Get all comments for a publication
    ---
    tags:
      - Comments
    parameters:
      - name: publication_id
        in: path
        type: integer
        required: true
        description: The ID of the publication
      - name: include_replies
        in: query
        type: boolean
        required: false
        default: true
        description: Whether to include replies in the response
    responses:
      200:
        description: Successfully retrieved comments
        schema:
          type: object
          properties:
            publication_id:
              type: integer
            total_comments:
              type: integer
            comments:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  user_id:
                    type: integer
                  publication_id:
                    type: integer
                  comment_text:
                    type: string
                  comment_type:
                    type: string
                  parent_comment_id:
                    type: integer
                  status:
                    type: string
                  likes_count:
                    type: integer
                  created_at:
                    type: string
                  updated_at:
                    type: string
                  replies:
                    type: array
      404:
        description: Publication not found
      500:
        description: Internal server error
    """
    try:
        # Check if publication exists
        publication = Publications.query.get(publication_id)
        if not publication:
            return jsonify({'error': 'Publication not found'}), 404
        
        # Get query parameters
        include_replies = request.args.get('include_replies', 'true').lower() == 'true'
        
        # Get comments
        comments = PublicationComments.get_publication_comments(publication_id, include_replies)
        
        # Convert to dictionary format
        comments_data = []
        for comment in comments:
            comment_dict = comment.to_dict()
            # Add replies if it's a top-level comment
            if not comment.parent_comment_id and include_replies:
                comment_dict['replies'] = [reply.to_dict() for reply in comment.replies if reply.status == 'active']
            comments_data.append(comment_dict)
        
        return jsonify({
            'publication_id': publication_id,
            'total_comments': len(comments),
            'comments': comments_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting comments for publication {publication_id}: {str(e)}")
        return jsonify({'error': 'Failed to get comments'}), 500

@comments_bp.route('/api/publications/<int:publication_id>/comments', methods=['POST'])
@cross_origin()
def add_comment(publication_id):
    """
    Add a new comment to a publication
    ---
    tags:
      - Comments
    parameters:
      - name: publication_id
        in: path
        type: integer
        required: true
        description: The ID of the publication
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - user_id
            - comment_text
          properties:
            user_id:
              type: integer
              description: ID of the user posting the comment
            comment_text:
              type: string
              description: The comment text
            comment_type:
              type: string
              default: general
              description: Type of comment (general, review, question, etc.)
            parent_comment_id:
              type: integer
              description: ID of parent comment if this is a reply
    responses:
      201:
        description: Comment added successfully
        schema:
          type: object
          properties:
            message:
              type: string
            comment:
              type: object
      400:
        description: Bad request - missing required fields
      404:
        description: Publication, user, or parent comment not found
      500:
        description: Internal server error
    """
    try:
        # Check if publication exists
        publication = Publications.query.get(publication_id)
        if not publication:
            return jsonify({'error': 'Publication not found'}), 404
        
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        if not data.get('user_id'):
            return jsonify({'error': 'user_id is required'}), 400
        if not data.get('comment_text'):
            return jsonify({'error': 'comment_text is required'}), 400
        
        # Check if user exists
        user = UserAccount.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if parent comment exists (for replies)
        parent_comment_id = data.get('parent_comment_id')
        if parent_comment_id:
            parent_comment = PublicationComments.query.get(parent_comment_id)
            if not parent_comment:
                return jsonify({'error': 'Parent comment not found'}), 404
            if parent_comment.publication_id != publication_id:
                return jsonify({'error': 'Parent comment belongs to different publication'}), 400
        
        # Add the comment
        comment = PublicationComments.add_comment(
            publication_id=publication_id,
            user_id=data['user_id'],
            comment_text=data['comment_text'],
            comment_type=data.get('comment_type', 'general'),
            parent_comment_id=parent_comment_id
        )
        
        logger.info(f"Comment {comment.id} added to publication {publication_id} by user {data['user_id']}")
        
        return jsonify({
            'message': 'Comment added successfully',
            'comment': comment.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding comment to publication {publication_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to add comment'}), 500

@comments_bp.route('/api/comments/<int:comment_id>', methods=['PUT'])
@cross_origin()
def edit_comment(comment_id):
    """
    Edit an existing comment
    ---
    tags:
      - Comments
    parameters:
      - name: comment_id
        in: path
        type: integer
        required: true
        description: The ID of the comment to edit
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - user_id
            - comment_text
          properties:
            user_id:
              type: integer
              description: ID of the user editing the comment (must be the author)
            comment_text:
              type: string
              description: The updated comment text
    responses:
      200:
        description: Comment updated successfully
        schema:
          type: object
          properties:
            message:
              type: string
            comment:
              type: object
      400:
        description: Bad request - missing comment_text
      403:
        description: Unauthorized - only comment author can edit
      404:
        description: Comment not found
      500:
        description: Internal server error
    """
    try:
        # Get the comment
        comment = PublicationComments.query.get(comment_id)
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404
        
        # Get request data
        data = request.get_json()
        
        # Validate user permission (only comment author can edit)
        if data.get('user_id') != comment.user_id:
            return jsonify({'error': 'Unauthorized: Only comment author can edit'}), 403
        
        # Validate new text
        new_text = data.get('comment_text')
        if not new_text:
            return jsonify({'error': 'comment_text is required'}), 400
        
        # Edit the comment
        comment.edit_comment(new_text)
        
        logger.info(f"Comment {comment_id} edited by user {comment.user_id}")
        
        return jsonify({
            'message': 'Comment updated successfully',
            'comment': comment.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error editing comment {comment_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to edit comment'}), 500

@comments_bp.route('/api/comments/<int:comment_id>', methods=['DELETE'])
@cross_origin()
def delete_comment(comment_id):
    """
    Delete a comment (soft delete)
    ---
    tags:
      - Comments
    parameters:
      - name: comment_id
        in: path
        type: integer
        required: true
        description: The ID of the comment to delete
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - user_id
          properties:
            user_id:
              type: integer
              description: ID of the user deleting the comment
    responses:
      200:
        description: Comment deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
      400:
        description: Bad request - missing user_id
      403:
        description: Unauthorized - only comment author or admin can delete
      404:
        description: Comment or user not found
      500:
        description: Internal server error
    """
    try:
        # Get the comment
        comment = PublicationComments.query.get(comment_id)
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404
        
        # Get request data
        data = request.get_json()
        
        # Validate user permission (only comment author or admin can delete)
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
            
        user = UserAccount.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Check permission
        is_admin = user.role == 'admin' if user.role else False
        if user_id != comment.user_id and not is_admin:
            return jsonify({'error': 'Unauthorized: Only comment author or admin can delete'}), 403
        
        # Soft delete the comment
        comment.delete_comment(soft_delete=True)
        
        logger.info(f"Comment {comment_id} deleted by user {user_id}")
        
        return jsonify({
            'message': 'Comment deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting comment {comment_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete comment'}), 500

@comments_bp.route('/api/comments/<int:comment_id>/like', methods=['POST'])
@cross_origin()
def like_comment(comment_id):
    """
    Like a comment
    ---
    tags:
      - Comments
    parameters:
      - name: comment_id
        in: path
        type: integer
        required: true
        description: The ID of the comment to like
    responses:
      200:
        description: Comment liked successfully
        schema:
          type: object
          properties:
            message:
              type: string
            likes_count:
              type: integer
              description: Updated number of likes
      404:
        description: Comment not found
      500:
        description: Internal server error
    """
    try:
        # Get the comment
        comment = PublicationComments.query.get(comment_id)
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404
        
        # Increment likes
        new_likes_count = comment.increment_likes()
        
        logger.info(f"Comment {comment_id} liked. New count: {new_likes_count}")
        
        return jsonify({
            'message': 'Comment liked successfully',
            'likes_count': new_likes_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error liking comment {comment_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to like comment'}), 500

@comments_bp.route('/api/users/<int:user_id>/comments', methods=['GET'])
@cross_origin()
def get_user_comments(user_id):
    """
    Get all comments by a specific user
    ---
    tags:
      - Comments
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: The ID of the user
    responses:
      200:
        description: Successfully retrieved user comments
        schema:
          type: object
          properties:
            user_id:
              type: integer
            user_name:
              type: string
            total_comments:
              type: integer
            comments:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  publication_id:
                    type: integer
                  comment_text:
                    type: string
                  comment_type:
                    type: string
                  parent_comment_id:
                    type: integer
                  status:
                    type: string
                  likes_count:
                    type: integer
                  created_at:
                    type: string
                  updated_at:
                    type: string
      404:
        description: User not found
      500:
        description: Internal server error
    """
    try:
        # Check if user exists
        user = UserAccount.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get all comments by user
        comments = PublicationComments.query.filter_by(
            user_id=user_id, 
            status='active'
        ).order_by(PublicationComments.created_at.desc()).all()
        
        # Convert to dictionary format
        comments_data = [comment.to_dict() for comment in comments]
        
        return jsonify({
            'user_id': user_id,
            'user_name': user.full_name,
            'total_comments': len(comments),
            'comments': comments_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting comments for user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to get user comments'}), 500

@comments_bp.route('/api/comments/stats/<int:publication_id>', methods=['GET'])
@cross_origin()
def get_comment_stats(publication_id):
    """
    Get comment statistics for a publication
    ---
    tags:
      - Comments
    parameters:
      - name: publication_id
        in: path
        type: integer
        required: true
        description: The ID of the publication
    responses:
      200:
        description: Successfully retrieved comment statistics
        schema:
          type: object
          properties:
            publication_id:
              type: integer
            statistics:
              type: object
              properties:
                total_comments:
                  type: integer
                  description: Total number of comments
                top_level_comments:
                  type: integer
                  description: Number of top-level comments
                replies:
                  type: integer
                  description: Number of replies
                unique_commenters:
                  type: integer
                  description: Number of unique users who commented
                total_likes:
                  type: integer
                  description: Total number of likes across all comments
                comment_types:
                  type: object
                  description: Breakdown of comments by type
      404:
        description: Publication not found
      500:
        description: Internal server error
    """
    try:
        # Check if publication exists
        publication = Publications.query.get(publication_id)
        if not publication:
            return jsonify({'error': 'Publication not found'}), 404
        
        # Get all comments for the publication
        all_comments = PublicationComments.query.filter_by(
            publication_id=publication_id,
            status='active'
        ).all()
        
        # Calculate statistics
        total_comments = len(all_comments)
        top_level_comments = len([c for c in all_comments if not c.parent_comment_id])
        replies = len([c for c in all_comments if c.parent_comment_id])
        
        # Get comment types breakdown
        comment_types = {}
        for comment in all_comments:
            comment_types[comment.comment_type] = comment_types.get(comment.comment_type, 0) + 1
        
        # Get unique commenters
        unique_users = len(set([c.user_id for c in all_comments]))
        
        # Get total likes
        total_likes = sum([c.likes_count for c in all_comments])
        
        return jsonify({
            'publication_id': publication_id,
            'statistics': {
                'total_comments': total_comments,
                'top_level_comments': top_level_comments,
                'replies': replies,
                'unique_commenters': unique_users,
                'total_likes': total_likes,
                'comment_types': comment_types
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting comment stats for publication {publication_id}: {str(e)}")
        return jsonify({'error': 'Failed to get comment statistics'}), 500