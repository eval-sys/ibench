DO $$
DECLARE
  fixture_tenant_id uuid;
BEGIN
  SELECT tenant_account_joins.tenant_id
    INTO fixture_tenant_id
    FROM accounts
    JOIN tenant_account_joins ON tenant_account_joins.account_id = accounts.id
   WHERE lower(accounts.email) = 'admin@local.host'
     AND tenant_account_joins.role = 'owner'
   ORDER BY tenant_account_joins.created_at
   LIMIT 1;

  IF fixture_tenant_id IS NULL THEN
    RAISE EXCEPTION 'The bootstrap workspace for admin@local.host was not found';
  END IF;

  INSERT INTO accounts (
    id,
    name,
    email,
    password,
    password_salt,
    interface_language,
    interface_theme,
    timezone,
    status,
    initialized_at,
    created_at,
    updated_at,
    last_active_at
  ) VALUES (
    '7f3a20d1-4fb4-48a2-ae5b-e754c6089a40',
    'Studio Editor',
    'studio.editor@local.host',
    'Y2NlYTQ0MTZjYTc4ZDJkMjZhZGEyNmVmMzgwNzkxOWY3NzU1ZjNlYjI3NDA2YzJhZTQ4N2YzZmZkOGEyMDZlMQ==',
    'ABEiM0RVZneImaq7zN3u/w==',
    'en-US',
    'light',
    'UTC',
    'active',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
  );

  INSERT INTO tenant_account_joins (
    id,
    tenant_id,
    account_id,
    role,
    current,
    created_at,
    updated_at
  ) VALUES (
    'f5d38307-948f-40e6-9c82-c4ae80bcc84e',
    fixture_tenant_id,
    '7f3a20d1-4fb4-48a2-ae5b-e754c6089a40',
    'editor',
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
  );

  INSERT INTO apps (
    id,
    tenant_id,
    name,
    mode,
    icon,
    icon_background,
    status,
    enable_site,
    enable_api,
    api_rpm,
    api_rph,
    is_demo,
    is_public,
    is_universal,
    description,
    icon_type,
    created_by,
    updated_by,
    maintainer,
    use_icon_as_answer_icon,
    created_at,
    updated_at
  ) VALUES (
    '5e2bb497-11fd-4d28-a68c-09c7c6623b31',
    fixture_tenant_id,
    'Support Release Flow',
    'advanced-chat',
    '🤖',
    '#FFEAD5',
    'normal',
    true,
    true,
    0,
    0,
    false,
    false,
    false,
    '',
    'emoji',
    '7f3a20d1-4fb4-48a2-ae5b-e754c6089a40',
    '7f3a20d1-4fb4-48a2-ae5b-e754c6089a40',
    '7f3a20d1-4fb4-48a2-ae5b-e754c6089a40',
    false,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
  );

  INSERT INTO workflows (
    id,
    tenant_id,
    app_id,
    type,
    version,
    graph,
    features,
    created_by,
    created_at,
    updated_by,
    updated_at,
    environment_variables,
    conversation_variables,
    marked_name,
    marked_comment,
    rag_pipeline_variables,
    kind
  ) VALUES (
    '1cc14e14-dd4e-4cba-acd2-9892f7cc390d',
    fixture_tenant_id,
    '5e2bb497-11fd-4d28-a68c-09c7c6623b31',
    'chat',
    'draft',
    $graph${"nodes":[{"id":"start","type":"custom","data":{"variables":[],"type":"start","title":"User Input"},"position":{"x":80,"y":282},"targetPosition":"left","sourcePosition":"right","positionAbsolute":{"x":80,"y":282},"width":242,"height":73},{"id":"llm","type":"custom","data":{"model":{"provider":"","name":"","mode":"chat","completion_params":{"temperature":0.7}},"prompt_template":[{"role":"system","text":""}],"context":{"enabled":false,"variable_selector":[]},"vision":{"enabled":false},"memory":{"window":{"enabled":false,"size":10},"query_prompt_template":"{{#sys.query#}}\n\n{{#sys.files#}}"},"selected":true,"type":"llm","title":"LLM"},"position":{"x":380,"y":282},"targetPosition":"left","sourcePosition":"right","positionAbsolute":{"x":380,"y":282},"width":242,"height":52},{"id":"answer","type":"custom","data":{"variables":[],"answer":"{{#llm.text#}}","type":"answer","title":"Answer"},"position":{"x":680,"y":282},"targetPosition":"left","sourcePosition":"right","positionAbsolute":{"x":680,"y":282},"width":242,"height":103}],"edges":[{"id":"start-llm","source":"start","sourceHandle":"source","target":"llm","targetHandle":"target","type":"custom","data":{"sourceType":"start","targetType":"llm"}},{"id":"llm-answer","source":"llm","sourceHandle":"source","target":"answer","targetHandle":"target","type":"custom","data":{"sourceType":"llm","targetType":"answer"}}],"viewport":{"x":0,"y":0,"zoom":1}}$graph$,
    $features${"opening_statement":"","suggested_questions":[],"suggested_questions_after_answer":{"enabled":false},"text_to_speech":{"enabled":false,"voice":"","language":""},"speech_to_text":{"enabled":false},"retriever_resource":{"enabled":true},"sensitive_word_avoidance":{"enabled":false},"file_upload":{"image":{"enabled":false,"number_limits":3,"transfer_methods":["local_file","remote_url"]},"enabled":false,"allowed_file_types":["image"],"allowed_file_extensions":[".JPG",".JPEG",".PNG",".GIF",".WEBP",".SVG"],"allowed_file_upload_methods":["local_file","remote_url"],"number_limits":3}}$features$,
    '7f3a20d1-4fb4-48a2-ae5b-e754c6089a40',
    CURRENT_TIMESTAMP,
    '7f3a20d1-4fb4-48a2-ae5b-e754c6089a40',
    CURRENT_TIMESTAMP,
    '{}',
    '{}',
    '',
    '',
    '{}',
    'standard'
  );

  INSERT INTO sites (
    id,
    app_id,
    title,
    icon,
    icon_background,
    description,
    default_language,
    customize_token_strategy,
    prompt_public,
    status,
    code,
    custom_disclaimer,
    show_workflow_steps,
    chat_color_theme_inverted,
    icon_type,
    created_by,
    updated_by,
    use_icon_as_answer_icon,
    created_at,
    updated_at
  ) VALUES (
    '2848a69c-b7d2-435a-a0c2-d5a7fc497a31',
    '5e2bb497-11fd-4d28-a68c-09c7c6623b31',
    'Support Release Flow',
    '🤖',
    '#FFEAD5',
    '',
    'en-US',
    'not_allow',
    false,
    'normal',
    'support-release-flow-local',
    '',
    true,
    false,
    'emoji',
    '7f3a20d1-4fb4-48a2-ae5b-e754c6089a40',
    '7f3a20d1-4fb4-48a2-ae5b-e754c6089a40',
    false,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
  );

  INSERT INTO installed_apps (
    id,
    tenant_id,
    app_id,
    app_owner_tenant_id,
    position,
    is_pinned,
    created_at
  ) VALUES (
    'd34b949e-3524-482b-810b-1a3503a7d93a',
    fixture_tenant_id,
    '5e2bb497-11fd-4d28-a68c-09c7c6623b31',
    fixture_tenant_id,
    0,
    false,
    CURRENT_TIMESTAMP
  );
END
$$;
