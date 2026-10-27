# Local Afilmory fixtures

The environment provides four immutable, locally generated JPEGs under
`/opt/dev-env-fixtures/photos`. The preparation step uploads them through the
historical core's photo service into local RustFS storage and PostgreSQL.

- `landscape.jpg`: gallery navigation and map interactions, with standard GPS
  EXIF at fixed WGS84 test coordinates `48.85 N, 2.35 E`. The image and location
  are synthetic test data, not a claim about where a photograph was taken.
- `portrait.jpg`: gallery navigation and viewer interactions, without GPS.
- `xmp-no-unit.jpg`: an XMP region with normalized coordinates and no area unit.
- `xmp-normalized.jpg`: the same region with an explicit normalized area unit.

The historical photo service produces the manifest and thumbnails during
preparation. No manifest, expected verdict, or reference repair is supplied by the
environment. Do not edit these photos or replace their generated metadata.

Core serves the gallery at `http://localhost:3210/` and the administrator
dashboard at `http://root.localhost:3210/platform/root-login`. Sign in with
`root@local.host` / `Local-Development-2026` (local test credentials).
The tenant manager is `/platform/superadmin/tenants` on that administrator host.

The database contains three active workspaces with owners, dated 2020-01-01:

- `gallery`: four photos, Pro plan and a verified `localhost` domain.
- `small`: one small JPEG, Free plan, no custom domain.
- `empty`: no photos, Free plan, no custom domain.

In Account cleanup, set Max photos to 1 and Max storage (MB) to 1 to include
both `small` and `empty`; both their owners also qualify in the Users tab.
Their IDs start with `fixture-`. The gallery and root administrator are
protected from cleanup. These fixtures establish data, not expected UI verdicts.

Use `SELECT 1;` for SQL setup/cleanup when these persistent preconditions already
meet the episode's Given. Additional SQL and browser setup remain available under
the existing fixture protocol. If the environment does not establish the Given,
report that limitation; do not substitute a different scenario.
