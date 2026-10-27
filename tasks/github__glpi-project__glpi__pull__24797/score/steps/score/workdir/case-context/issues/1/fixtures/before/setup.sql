-- Isolated form: the installed default forms have no conditional questions.
START TRANSACTION;
INSERT INTO glpi_forms_forms
 (uuid, entities_id, is_recursive, name, submit_button_visibility_strategy, submit_button_conditions)
VALUES ('e9d24797-1000-4000-8000-000000000001', 0, 1, 'Service request details', 'always_visible', '[]');
SET @form_id = LAST_INSERT_ID();
INSERT INTO glpi_forms_sections
 (uuid, forms_forms_id, name, rank, visibility_strategy, conditions)
VALUES ('e9d24797-1000-4000-8000-000000000002', @form_id, 'Request details', 0, 'always_visible', '[]');
SET @section_id = LAST_INSERT_ID();
INSERT INTO glpi_forms_questions
 (uuid, forms_sections_id, forms_sections_uuid, name, type, vertical_rank,
  description, default_value, visibility_strategy, conditions, validation_strategy, validation_conditions)
VALUES
 ('e9d24797-1000-4000-8000-000000000003', @section_id, 'e9d24797-1000-4000-8000-000000000002',
  'Category', 'Glpi\\Form\\QuestionType\\QuestionTypeShortText', 0,
  '', '', 'always_visible', '[]', 'no_validation', '[]'),
 ('e9d24797-1000-4000-8000-000000000004', @section_id, 'e9d24797-1000-4000-8000-000000000002',
  'Summary', 'Glpi\\Form\\QuestionType\\QuestionTypeShortText', 1,
  '', '', 'visible_if',
  '[{"item":"question-e9d24797-1000-4000-8000-000000000003","value_operator":"equals","logic_operator":"and","value":"Assistance"}]',
  'valid_if',
  '[{"item":"question-e9d24797-1000-4000-8000-000000000004","value_operator":"length_greater_than","logic_operator":"and","value":5}]');
INSERT INTO glpi_forms_accesscontrols_formaccesscontrols
 (forms_forms_id, strategy, config, is_active)
VALUES (@form_id, 'Glpi\\Form\\AccessControl\\ControlType\\AllowList', '{"user_ids":["all"],"group_ids":[],"profile_ids":[]}', 1);
INSERT INTO glpi_forms_destinations_formdestinations
 (forms_forms_id, itemtype, name, config, creation_strategy, conditions)
VALUES (@form_id, 'Glpi\\Form\\Destination\\FormDestinationTicket', 'Ticket', '[]', 'always_created', '[]');
COMMIT;
