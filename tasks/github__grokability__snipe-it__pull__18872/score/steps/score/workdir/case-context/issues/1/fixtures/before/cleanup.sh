#!/usr/bin/env bash
set -euo pipefail
cd /workspace/app
# These three fixed location keys belong exclusively to this issue.
# Query deletion avoids generating new deletion-history rows during cleanup.
php artisan tinker --execute='$names = ["Cedar Technologies", "North Building", "Room 101"]; $ids = \App\Models\Location::withTrashed()->whereIn("name", $names)->pluck("id"); \Illuminate\Support\Facades\DB::transaction(function () use ($ids) { \App\Models\Actionlog::where("item_type", \App\Models\Location::class)->whereIn("item_id", $ids)->delete(); \Illuminate\Support\Facades\DB::table("locations")->whereIn("id", $ids)->delete(); });'
rm -f storage/private_uploads/imports/cedar-campus-root.csv storage/private_uploads/imports/cedar-campus-children.csv
