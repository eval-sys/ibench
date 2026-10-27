#!/usr/bin/env bash
set -euo pipefail
fixture_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
bash "$fixture_dir/cleanup.sh"
cd /workspace/app
# The environment already seeded admin/password. Its location seed is random
# and has no parents. Use the supported importer for only the missing hierarchy.
import_dir=/workspace/app/storage/private_uploads/imports
mkdir -p "$import_dir"
trap 'rm -f "$import_dir/cedar-campus-root.csv" "$import_dir/cedar-campus-children.csv"' EXIT
cat > "$import_dir/cedar-campus-root.csv" <<'CSV'
Name
Cedar Technologies
CSV
cat > "$import_dir/cedar-campus-children.csv" <<'CSV'
Name,Parent Name
North Building,Cedar Technologies
Room 101,North Building
CSV
php artisan snipeit:import-locations cedar-campus-root.csv
php artisan snipeit:import-locations cedar-campus-children.csv
# Stable searchable notes make the entire Given inspectable in one list.
# Resolve every relationship anew; never keep generated IDs between runs.
php artisan tinker --execute='$names = ["Cedar Technologies", "North Building", "Room 101"]; $parent = null; foreach ($names as $name) { $location = \App\Models\Location::where("name", $name)->firstOrFail(); if ($location->parent_id !== $parent) { throw new \RuntimeException("Incorrect location hierarchy"); } $parent = $location->id; } \Illuminate\Support\Facades\DB::table("locations")->whereIn("name", $names)->update(["notes" => "Cedar campus directory"]); if (!\App\Models\User::where("username", "admin")->where("activated", 1)->exists()) { throw new \RuntimeException("Prepared admin account is missing"); }'
