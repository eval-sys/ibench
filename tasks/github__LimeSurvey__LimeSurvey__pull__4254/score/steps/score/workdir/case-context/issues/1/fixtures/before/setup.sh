#!/usr/bin/env bash
set -euo pipefail
# Use the existing native install/demo administrator. No shared settings are changed.
# Only this isolated survey needs initialization: prepared demo attachments are empty.
command_dir="$(mktemp -d /tmp/attachment-scenario.XXXXXX)"
trap 'rm -rf -- "$command_dir"' EXIT
cat > "$command_dir/AttachmentScenarioCommand.php" <<'PHP'
<?php
/** Issue-owned data, run by LimeSurvey's documented YII_CONSOLE_COMMANDS loader. */
class AttachmentScenarioCommand extends CConsoleCommand
{
    const SID = 425401;
    const TITLE = 'Community feedback';

    private function saveRecord($record) {
        if (!$record->save()) {
            throw new Exception(json_encode($record->getErrors()));
        }
    }

    public function run($args) {
        Yii::app()->loadHelper('common');
        Yii::app()->loadHelper('surveytranslator');
        Yii::app()->session['loginID'] = 1; // Native install/demo account; never recreate it.
        $survey = Survey::model()->findByPk(self::SID);
        if ($survey) {
            $language = SurveyLanguageSetting::model()->findByPk([
                'surveyls_survey_id' => self::SID, 'surveyls_language' => 'en'
            ]);
            if (($language && $language->surveyls_title !== self::TITLE)
                || (!$language && $survey->admin !== 'Community feedback team')) {
                throw new Exception('Reserved survey ID belongs to another survey');
            }
            if (!$survey->delete()) throw new Exception('Survey cleanup failed');
        }
        // Remove the native survey theme config associated only with this survey.
        TemplateConfiguration::model()->deleteAllByAttributes(['sid' => self::SID]);
        if (($args[0] ?? '') === 'cleanup') return 0;
        if (($args[0] ?? '') !== 'setup') throw new Exception('Expected setup or cleanup');

        $survey = Survey::model()->insertNewSurvey([
            'wishSID' => self::SID, 'owner_id' => 1, 'active' => 'N',
            'language' => 'en', 'format' => 'G', 'template' => 'fruity',
            'admin' => 'Community feedback team', 'adminemail' => 'feedback@example.test',
            'htmlemail' => 'N', 'anonymized' => 'N', 'gsid' => 1
        ]);
        if (!$survey || (int)$survey->sid !== self::SID) throw new Exception('Survey creation failed');
        Permission::model()->giveAllSurveyPermissions(1, self::SID);
        $language = new SurveyLanguageSetting();
        $language->insertNewSurvey([
            'surveyls_survey_id' => self::SID, 'surveyls_language' => 'en',
            'surveyls_title' => self::TITLE
        ]);
        $language = SurveyLanguageSetting::model()->findByPk(['surveyls_survey_id' => self::SID, 'surveyls_language' => 'en']);
        $language->surveyls_email_invite_subj = 'Invitation to Community feedback';
        $language->surveyls_email_invite = "Hello {FIRSTNAME},\nPlease share your feedback: {SURVEYURL}\nThank you,\nAdministrator";
        $language->attachments = json_encode(['invitation' => [[
            'url' => '/workspace/app/upload/surveys/425401/participant-guide.pdf',
            'size' => '0', 'relevance' => '1'
        ]]]);
        // Persist the stale reference as it would remain after an uploaded file is lost.
        // Form validators strip absent attachments; this precondition must survive them.
        if (!$language->save(false)) throw new Exception('Language settings save failed');
        if (file_exists('/workspace/app/upload/surveys/425401/participant-guide.pdf')) {
            throw new Exception('Attachment unexpectedly exists');
        }

        $group = new QuestionGroup();
        $group->sid = self::SID; $group->group_order = 0; $group->grelevance = '1';
        $this->saveRecord($group);
        $groupText = new QuestionGroupL10n();
        $groupText->gid = $group->gid; $groupText->language = 'en'; $groupText->group_name = 'Feedback';
        $this->saveRecord($groupText);
        $question = new Question();
        $question->sid = self::SID; $question->gid = $group->gid; $question->type = 'T';
        $question->title = 'Feedback'; $question->mandatory = 'N'; $question->relevance = '1'; $question->question_order = 0;
        $this->saveRecord($question);
        $questionText = new QuestionL10n();
        $questionText->qid = $question->qid; $questionText->language = 'en';
        $questionText->question = 'What would you like to share?';
        $this->saveRecord($questionText);
        Yii::app()->loadHelper('admin.activate');
        Yii::import('application.helpers.expressions.*');
        Yii::app()->loadHelper('expressions.em_manager');
        Yii::app()->loadHelper('expressions.em_core');
        $survey->setOptionsFromDatabase();
        $result = (new SurveyActivator($survey))->activate();
        if (isset($result['error'])) throw new Exception(json_encode($result));
        Token::createTable(self::SID);
        $participant = TokenDynamic::model(self::SID)->insertParticipant([
            'firstname' => 'Alex', 'lastname' => 'Morgan', 'email' => 'alex.morgan@example.test',
            'emailstatus' => 'OK', 'token' => 'community-feedback-alex', 'language' => 'en',
            'sent' => 'N', 'remindersent' => 'N', 'completed' => 'N', 'usesleft' => 1
        ]);
        if (!$participant) throw new Exception('Participant creation failed');
        echo "Community feedback survey ready\n";
        return 0;
    }
}
PHP
cd /workspace/app
YII_CONSOLE_COMMANDS="$command_dir" php application/commands/console.php attachmentscenario "${1:-setup}"
