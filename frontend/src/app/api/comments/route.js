import { NextResponse } from 'next/server';

// In-memory storage for comments (in a real app, this would be a database)
let comments = [];

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const docId = searchParams.get('docId');
    
    if (!docId) {
      return NextResponse.json(
        { error: 'DOCiD is required' },
        { status: 400 }
      );
    }

    // Filter comments for the specific docId
    const docComments = comments.filter(comment => comment.docId === docId);
    
    // Organize comments with replies
    const organizedComments = [];
    const commentMap = {};
    
    // First pass: create map of all comments
    docComments.forEach(comment => {
      commentMap[comment.id] = { ...comment, replies: [] };
    });
    
    // Second pass: organize replies under parent comments
    docComments.forEach(comment => {
      const parentId = comment.parent_comment_id || comment.parentId;
      if (parentId && parentId !== 0 && commentMap[parentId.toString()]) {
        commentMap[parentId.toString()].replies.push(commentMap[comment.id]);
      } else if (!parentId || parentId === 0) {
        organizedComments.push(commentMap[comment.id]);
      }
    });
    
    return NextResponse.json(
      { comments: organizedComments },
      {
        status: 200,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        },
      }
    );
  } catch (error) {
    console.error('Error fetching comments:', error);
    return NextResponse.json(
      { error: 'Failed to fetch comments' },
      { status: 500 }
    );
  }
}

export async function POST(request) {
  try {
    const body = await request.json();
    const { 
      docId, 
      comment_text, 
      comment_type = "general", 
      parent_comment_id = 0, 
      user_id = 0,
      // Backward compatibility
      comment,
      author = 'Anonymous User',
      parentId
    } = body;
    
    // Use new structure if available, fall back to old structure
    const commentText = comment_text || comment;
    const parentCommentId = parent_comment_id || parentId || null;
    const userId = user_id;
    const commentType = comment_type;
    
    if (!docId || !commentText || !author) {
      return NextResponse.json(
        { error: 'DOCiD, comment_text, and author are required' },
        { status: 400 }
      );
    }

    // Validate parent_comment_id if provided (for replies)
    if (parentCommentId && parentCommentId !== 0) {
      const parentComment = comments.find(c => c.id === parentCommentId.toString());
      if (!parentComment) {
        return NextResponse.json(
          { error: 'Parent comment not found' },
          { status: 400 }
        );
      }
    }

    // Create new comment
    const newComment = {
      id: Date.now().toString(),
      docId,
      comment: commentText.trim(),
      comment_text: commentText.trim(),
      comment_type: commentType,
      parent_comment_id: parentCommentId && parentCommentId !== 0 ? parentCommentId : null,
      parentId: parentCommentId && parentCommentId !== 0 ? parentCommentId : null, // Backward compatibility
      user_id: userId,
      author,
      timestamp: new Date().toISOString(),
      likes: 0
    };

    // Add to comments array
    comments.push(newComment);
    
    return NextResponse.json(
      { 
        message: 'Comment submitted successfully',
        comment: newComment
      },
      {
        status: 201,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        },
      }
    );
  } catch (error) {
    console.error('Error submitting comment:', error);
    return NextResponse.json(
      { error: 'Failed to submit comment' },
      { status: 500 }
    );
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
} 