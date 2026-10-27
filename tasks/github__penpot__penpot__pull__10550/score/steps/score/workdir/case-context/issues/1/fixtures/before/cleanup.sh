#!/usr/bin/env bash
set -euo pipefail

nrepl_code='(do
  (require (symbol "app.db"))
  (let [system @(requiring-resolve (symbol "app.main/system"))]
    (app.db/tx-run!
     system
     (fn [cfg]
       (let [conn (:app.db/conn cfg)
             profile (app.db/get* conn :profile
                                  {:email "path.badge@example.com"}
                                  :app.db/remove-deleted false)
             teams (if profile
                     (app.db/exec! conn
                                   ["SELECT t.* FROM team t JOIN team_profile_rel tpr ON tpr.team_id=t.id WHERE tpr.profile_id=? AND tpr.is_owner IS TRUE"
                                    (:id profile)])
                     [])
             projects (mapv identity
                            (mapcat #(app.db/query conn :project
                                                   {:team-id (:id %)}
                                                   :app.db/remove-deleted false)
                                    teams))
             files (mapv identity
                         (mapcat #(app.db/query conn :file
                                                {:project-id (:id %)}
                                                :app.db/remove-deleted false)
                                 projects))
             media-ids (distinct
                        (concat
                         (keep :photo-id (cons profile teams))
                         (mapcat #(keep :media-id
                                        (app.db/query conn :file-thumbnail
                                                      {:file-id (:id %)}
                                                      :app.db/remove-deleted false))
                                 files)))]
         (app.db/exec-one! conn ["SET LOCAL rules.deletion_protection TO off"])
         (doseq [id media-ids]
           (app.db/exec-one! conn
                             ["UPDATE storage_object SET touched_at=clock_timestamp() WHERE id=?" id]))
         (when profile
           (app.db/delete! conn :profile {:id (:id profile)}))
         (doseq [{:keys [id]} files]
           (app.db/exec-one! conn ["DELETE FROM file_media_object WHERE file_id=?" id])
           (app.db/exec-one! conn ["DELETE FROM file_object_thumbnail WHERE file_id=?" id])
           (app.db/exec-one! conn ["DELETE FROM file_tagged_object_thumbnail WHERE file_id=?" id])
           (app.db/exec-one! conn ["DELETE FROM file_thumbnail WHERE file_id=?" id])
           (app.db/exec-one! conn ["DELETE FROM file_data WHERE file_id=?" id])
           (app.db/exec-one! conn ["DELETE FROM file_change WHERE file_id=?" id])
           (app.db/delete! conn :file {:id id}))
         (doseq [{:keys [id]} projects]
           (app.db/delete! conn :project {:id id}))
         (doseq [{:keys [id]} teams]
           (app.db/exec-one! conn ["DELETE FROM team_font_variant WHERE team_id=?" id])
           (app.db/delete! conn :team {:id id}))
         true)))))'
cleanup_result="$(
  {
    printf 'd4:code%d:%s2:op4:evale' "${#nrepl_code}" "$nrepl_code"
    sleep 0.2
  } | nc -q 2 127.0.0.1 6064
)"

case "$cleanup_result" in
  *"5:value4:true"*) ;;
  *)
    printf '%s\n' "$cleanup_result" >&2
    exit 1
    ;;
esac
