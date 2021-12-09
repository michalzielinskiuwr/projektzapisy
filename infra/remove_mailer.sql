BEGIN;
-- Modify many-to-many relationship (user x permission) to cascade deletes of user permissions
ALTER TABLE auth_user_user_permissions                                                        
DROP CONSTRAINT auth_user_user_permissions_permission_id_fkey,
ADD CONSTRAINT auth_user_user_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES auth_permission(id) ON DELETE CASCADE;

COMMIT;

BEGIN;
-- Remove (hopefully) everything related to mailer
--
-- Delete model DontSendEntry
--
DROP TABLE "mailer_dontsendentry" CASCADE;
--
-- Delete model Message
--
DROP TABLE "mailer_message" CASCADE;
--
-- Delete model MessageLog
--
DROP TABLE "mailer_messagelog" CASCADE;

-- Remove Django migrations.
DELETE FROM django_migrations WHERE app = 'mailer';

-- Get rid of permissions and content types.
DELETE FROM auth_permission WHERE content_type_id in (SELECT id FROM django_content_type WHERE app_label = 'mailer');

-- Get rid of admin changes.
DELETE FROM django_admin_log WHERE content_type_id in (SELECT id FROM django_content_type WHERE app_label = 'mailer');
-- Finally, delete the content type.
DELETE FROM django_content_type WHERE app_label = 'mailer';

COMMIT;

BEGIN;
-- Restore the many-to-many (user x permission) relationship to original state
ALTER TABLE auth_user_user_permissions                                                        
DROP CONSTRAINT auth_user_user_permissions_permission_id_fkey,
ADD CONSTRAINT auth_user_user_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED;
COMMIT;
