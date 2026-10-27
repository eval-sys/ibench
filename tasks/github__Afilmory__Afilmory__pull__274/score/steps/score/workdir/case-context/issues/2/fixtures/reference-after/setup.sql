-- Trusted environment preparation owns these fixtures. Validate Given without
-- replacing product measurements or altering the fixture's photo metadata.
DO $$
BEGIN
  IF (SELECT count(*) FROM tenant
      WHERE (id = 'fixture-small' AND name = 'small workspace')
         OR (id = 'fixture-empty' AND name = 'empty workspace')) <> 2 THEN
    RAISE EXCEPTION 'Required workspace fixtures are missing';
  END IF;
  IF (SELECT count(*) FROM photo_asset WHERE tenant_id = 'fixture-small') <> 1
     OR (SELECT coalesce(sum(size), 0) FROM photo_asset WHERE tenant_id = 'fixture-small') <> 13858
     OR NOT EXISTS (SELECT 1 FROM photo_asset WHERE tenant_id = 'fixture-small' AND storage_key LIKE '%.jpg') THEN
    RAISE EXCEPTION 'small workspace must contain one 13858-byte JPEG';
  END IF;
  IF EXISTS (SELECT 1 FROM photo_asset WHERE tenant_id = 'fixture-empty')
     OR EXISTS (SELECT 1 FROM managed_storage_file_reference
                WHERE tenant_id IN ('fixture-small', 'fixture-empty') AND coalesce(size, 0) <> 0) THEN
    RAISE EXCEPTION 'Unexpected storage in the comparison fixtures';
  END IF;
END
$$;
