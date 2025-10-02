CREATE TABLE IF NOT EXISTS feedback_profile (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),

  reviewer_profile_id  uuid NOT NULL,
  reviewee_profile_id  uuid NOT NULL,
  match_id             uuid NULL,

  -- Ratings / outcomes
  overall_experience   smallint NOT NULL CHECK (overall_experience BETWEEN 1 AND 5),
  would_meet_again     boolean NULL,
  safety_feeling       smallint NULL CHECK (safety_feeling BETWEEN 1 AND 5),
  respectfulness       smallint NULL CHECK (respectfulness BETWEEN 1 AND 5),

  -- Qualitative
  headline             varchar(120) NULL,
  comment              text NULL,
  tags                 text[] NULL,

  -- Timestamps
  created_at           timestamptz NOT NULL DEFAULT NOW(),
  updated_at           timestamptz NOT NULL DEFAULT NOW(),

  CONSTRAINT feedback_profile_reviewer_ne_reviewee
    CHECK (reviewer_profile_id <> reviewee_profile_id),

  CONSTRAINT feedback_profile_comment_len
    CHECK (comment IS NULL OR char_length(comment) <= 2000),

  CONSTRAINT feedback_profile_tags_count
    CHECK (tags IS NULL OR array_length(tags, 1) <= 20)

  /* Optional FKs
  ,CONSTRAINT fk_feedback_profile_reviewer FOREIGN KEY (reviewer_profile_id)
      REFERENCES profiles(id) ON DELETE CASCADE
  ,CONSTRAINT fk_feedback_profile_reviewee FOREIGN KEY (reviewee_profile_id)
      REFERENCES profiles(id) ON DELETE CASCADE
  ,CONSTRAINT fk_feedback_profile_match FOREIGN KEY (match_id)
      REFERENCES matches(id) ON DELETE SET NULL
  */
);

DROP TRIGGER IF EXISTS trg_feedback_profile_set_updated_at ON feedback_profile;
CREATE TRIGGER trg_feedback_profile_set_updated_at
BEFORE UPDATE ON feedback_profile
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE UNIQUE INDEX IF NOT EXISTS ux_feedback_profile_match_reviewer
  ON feedback_profile (match_id, reviewer_profile_id)
  WHERE match_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_feedback_profile_reviewee_created
  ON feedback_profile (reviewee_profile_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_feedback_profile_reviewer_created
  ON feedback_profile (reviewer_profile_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_feedback_profile_match
  ON feedback_profile (match_id);

CREATE INDEX IF NOT EXISTS ix_feedback_profile_overall
  ON feedback_profile (overall_experience);

CREATE INDEX IF NOT EXISTS ix_feedback_profile_tags_gin
  ON feedback_profile USING GIN (tags);



CREATE TABLE IF NOT EXISTS feedback_app (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),

  author_profile_id    uuid NULL, -- can be NULL if you allow anonymous

  -- Ratings
  overall              smallint NOT NULL CHECK (overall BETWEEN 1 AND 5),
  usability            smallint NULL CHECK (usability BETWEEN 1 AND 5),
  reliability          smallint NULL CHECK (reliability BETWEEN 1 AND 5),
  performance          smallint NULL CHECK (performance BETWEEN 1 AND 5),
  support_experience   smallint NULL CHECK (support_experience BETWEEN 1 AND 5),

  -- Qualitative
  headline             varchar(120) NULL,
  comment              text NULL,
  tags                 text[] NULL,

  -- Timestamps
  created_at           timestamptz NOT NULL DEFAULT NOW(),
  updated_at           timestamptz NOT NULL DEFAULT NOW(),

  -- Optional: cap comment length to 2000 chars
  CONSTRAINT feedback_app_comment_len
    CHECK (comment IS NULL OR char_length(comment) <= 2000),

  -- Optional: cap number of tags to 20
  CONSTRAINT feedback_app_tags_count
    CHECK (tags IS NULL OR array_length(tags, 1) <= 20)

  /* Optional FK if profiles live here:
  ,CONSTRAINT fk_feedback_app_author FOREIGN KEY (author_profile_id)
      REFERENCES profiles(id) ON DELETE SET NULL
  */
);

-- Keep updated_at fresh
DROP TRIGGER IF EXISTS trg_feedback_app_set_updated_at ON feedback_app;
CREATE TRIGGER trg_feedback_app_set_updated_at
BEFORE UPDATE ON feedback_app
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Query indexes
CREATE INDEX IF NOT EXISTS ix_feedback_app_created
  ON feedback_app (created_at DESC);

CREATE INDEX IF NOT EXISTS ix_feedback_app_overall
  ON feedback_app (overall);

CREATE INDEX IF NOT EXISTS ix_feedback_app_author
  ON feedback_app (author_profile_id);

-- Tags overlap queries
CREATE INDEX IF NOT EXISTS ix_feedback_app_tags_gin
  ON feedback_app USING GIN (tags);
