-- API 访问令牌表（存量环境执行）
CREATE TABLE IF NOT EXISTS t_api_token (
    id              BIGSERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES t_user(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    token_hash      VARCHAR(64) NOT NULL,
    token_prefix    VARCHAR(12) NOT NULL,
    status          INTEGER NOT NULL DEFAULT 1,
    expires_at      TIMESTAMP NULL,
    last_used_at    TIMESTAMP NULL,
    created_by      INTEGER NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_t_api_token_hash ON t_api_token(token_hash);
CREATE INDEX IF NOT EXISTS idx_t_api_token_user_id ON t_api_token(user_id);
CREATE INDEX IF NOT EXISTS idx_t_api_token_status ON t_api_token(status);

COMMENT ON TABLE t_api_token IS 'API 访问令牌';
COMMENT ON COLUMN t_api_token.id IS '主键ID';
COMMENT ON COLUMN t_api_token.user_id IS '绑定用户ID（须为 admin 角色）';
COMMENT ON COLUMN t_api_token.name IS 'Token 备注名';
COMMENT ON COLUMN t_api_token.token_hash IS 'SHA-256(明文token)，不存明文';
COMMENT ON COLUMN t_api_token.token_prefix IS '明文前12位，用于列表展示';
COMMENT ON COLUMN t_api_token.status IS '状态：1=启用 0=禁用';
COMMENT ON COLUMN t_api_token.expires_at IS '过期时间，NULL 表示永久有效';
COMMENT ON COLUMN t_api_token.last_used_at IS '最近使用时间';
COMMENT ON COLUMN t_api_token.created_by IS '创建人用户ID';
COMMENT ON COLUMN t_api_token.created_at IS '创建时间';
COMMENT ON COLUMN t_api_token.updated_at IS '更新时间';
