-- Migration: Add publication_comments table
-- Date: 2025-08-06
-- Description: Create table for storing comments on publications

-- Create the publication_comments table
CREATE TABLE IF NOT EXISTS publication_comments (
    id SERIAL PRIMARY KEY,
    publication_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    parent_comment_id INTEGER,
    comment_text TEXT NOT NULL,
    comment_type VARCHAR(50) DEFAULT 'general',
    status VARCHAR(20) DEFAULT 'active',
    is_edited BOOLEAN DEFAULT FALSE,
    edit_count INTEGER DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT fk_publication_comments_publication
        FOREIGN KEY (publication_id) 
        REFERENCES publications(id) 
        ON DELETE CASCADE,
    
    CONSTRAINT fk_publication_comments_user
        FOREIGN KEY (user_id) 
        REFERENCES user_accounts(user_id) 
        ON DELETE CASCADE,
    
    CONSTRAINT fk_publication_comments_parent
        FOREIGN KEY (parent_comment_id) 
        REFERENCES publication_comments(id) 
        ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX idx_publication_comments_publication_id ON publication_comments(publication_id);
CREATE INDEX idx_publication_comments_user_id ON publication_comments(user_id);
CREATE INDEX idx_publication_comments_parent_comment_id ON publication_comments(parent_comment_id);
CREATE INDEX idx_publication_comments_status ON publication_comments(status);
CREATE INDEX idx_publication_comments_created_at ON publication_comments(created_at DESC);

-- Create trigger to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_publication_comments_updated_at 
    BEFORE UPDATE ON publication_comments 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add comment on table
COMMENT ON TABLE publication_comments IS 'Stores user comments on publications with support for nested replies';

-- Add comments on columns
COMMENT ON COLUMN publication_comments.id IS 'Primary key';
COMMENT ON COLUMN publication_comments.publication_id IS 'Foreign key to publications table';
COMMENT ON COLUMN publication_comments.user_id IS 'Foreign key to user_accounts table';
COMMENT ON COLUMN publication_comments.parent_comment_id IS 'Self-referencing foreign key for nested comments/replies';
COMMENT ON COLUMN publication_comments.comment_text IS 'The actual comment text';
COMMENT ON COLUMN publication_comments.comment_type IS 'Type of comment: general, review, question, suggestion';
COMMENT ON COLUMN publication_comments.status IS 'Comment status: active, edited, deleted, flagged';
COMMENT ON COLUMN publication_comments.is_edited IS 'Flag indicating if comment has been edited';
COMMENT ON COLUMN publication_comments.edit_count IS 'Number of times comment has been edited';
COMMENT ON COLUMN publication_comments.likes_count IS 'Number of likes on the comment';
COMMENT ON COLUMN publication_comments.created_at IS 'Timestamp when comment was created';
COMMENT ON COLUMN publication_comments.updated_at IS 'Timestamp when comment was last updated';