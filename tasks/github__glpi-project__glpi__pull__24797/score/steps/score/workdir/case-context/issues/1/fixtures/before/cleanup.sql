START TRANSACTION;
SET @form_id = (SELECT id FROM glpi_forms_forms WHERE uuid = 'e9d24797-1000-4000-8000-000000000001');
DELETE q FROM glpi_forms_questions q JOIN glpi_forms_sections s ON q.forms_sections_id = s.id WHERE s.forms_forms_id = @form_id;
DELETE FROM glpi_forms_sections WHERE forms_forms_id = @form_id;
DELETE FROM glpi_forms_accesscontrols_formaccesscontrols WHERE forms_forms_id = @form_id;
DELETE FROM glpi_forms_destinations_formdestinations WHERE forms_forms_id = @form_id;
DELETE FROM glpi_forms_forms WHERE id = @form_id;
COMMIT;
