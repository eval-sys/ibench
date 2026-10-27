import { readFile, readdir } from 'node:fs/promises'
import * as schema from '@afilmory/db'
import { CreateBucketCommand, HeadBucketCommand, PutBucketPolicyCommand, S3Client } from '@aws-sdk/client-s3'
import { HttpContext } from '@tsuki-hono/common'
import { eq } from 'drizzle-orm'

import { createConfiguredApp } from './src/app.factory'
import { DbAccessor, PgPoolProvider } from './src/database/database.provider'
import { StorageSettingService } from './src/modules/configuration/storage-setting/storage-setting.service'
import { SystemSettingService } from './src/modules/configuration/system-setting/system-setting.service'
import { PhotoAssetService } from './src/modules/content/photo/assets/photo-asset.service'
import { RedisProvider } from './src/redis/redis.provider'

// Run inside the historical core checkout, using its schema and photo processing.
const app = await createConfiguredApp({ globalPrefix: '/api' })
const container = app.getContainer()
const db = container.resolve(DbAccessor).get()
const storage = container.resolve(StorageSettingService)
const config = {
  endpoint: 'http://rustfs:9000', region: 'us-east-1',
  accessKeyId: 'afilmory-development', secretAccessKey: 'afilmory-development-secret',
  bucket: 'afilmory-development', prefix: '', customDomain: '', excludeRegex: '',
}
const s3 = new S3Client({ ...config, credentials: config, forcePathStyle: true })
const timestamp = '2020-01-01T00:00:00.000Z'

try {
  try {
    await s3.send(new HeadBucketCommand({ Bucket: config.bucket }))
  } catch {
    await s3.send(new CreateBucketCommand({ Bucket: config.bucket }))
  }
  await s3.send(new PutBucketPolicyCommand({
    Bucket: config.bucket,
    Policy: JSON.stringify({ Version: '2012-10-17', Statement: [{
      Effect: 'Allow', Principal: '*', Action: 's3:GetObject', Resource: `arn:aws:s3:::${config.bucket}/*`,
    }] }),
  }))
  await container.resolve(SystemSettingService).updateSettings({
    baseDomain: 'localhost', oauthGatewayUrl: 'http://localhost:3210',
  })

  for (const slug of ['gallery', 'small', 'empty']) {
    const id = `fixture-${slug}`
    await db.insert(schema.tenants).values({
      id, slug, name: `${slug} workspace`, planId: slug === 'gallery' ? 'pro' : 'free',
      status: 'active', createdAt: timestamp, updatedAt: timestamp,
    }).onConflictDoNothing()
    // Afilmory moved workspace ownership from auth_user to tenant_membership.
    const userId = `fixture-${slug}-owner`
    await db.insert(schema.authUsers).values({
      id: userId, name: `${slug} owner`, email: `${slug}@fixture.local`, emailVerified: true,
      createdAt: timestamp, updatedAt: timestamp,
      ...('tenantId' in schema.authUsers ? { tenantId: id, role: 'admin' } : {}),
    }).onConflictDoNothing()
    if ('tenantMemberships' in schema) {
      await db.insert(schema.tenantMemberships).values({
        id: `${id}-owner`, tenantId: id, userId, role: 'owner', status: 'active',
        createdAt: timestamp, updatedAt: timestamp,
      }).onConflictDoNothing()
    }
    if (slug === 'gallery') {
      await db.insert(schema.tenantDomains).values({
        id: `${id}-domain`, tenantId: id, domain: 'localhost', status: 'verified',
        ...('verificationToken' in schema.tenantDomains ? { verificationToken: 'fixture-development' } : {}),
      }).onConflictDoNothing()
    }
    const provider = {
      id: 'local-rustfs', name: 'Local RustFS', type: 's3',
      config: { ...config, prefix: slug === 'gallery' ? '' : slug },
    }
    await storage.setMany([
      { key: 'builder.storage.providers', options: { tenantId: id }, value: JSON.stringify([provider]) },
      { key: 'builder.storage.activeProvider', options: { tenantId: id }, value: provider.id },
    ])
    const photos = await db.select().from(schema.photoAssets).where(eq(schema.photoAssets.tenantId, id))
    if (slug === 'empty' || photos.length > 0) continue
    const [tenant] = await db.select().from(schema.tenants).where(eq(schema.tenants.id, id))
    const filenames = slug === 'small' ? ['landscape.jpg'] : (await readdir('/opt/dev-env-fixtures/photos')).sort()
    await HttpContext.run({ req: { method: 'POST', path: '/fixture-seed' } }, async () => {
      HttpContext.assign({ tenant: { tenant } })
      await container.resolve(PhotoAssetService).uploadAssets(await Promise.all(filenames.map(async filename => ({
        filename, contentType: 'image/jpeg', buffer: await readFile(`/opt/dev-env-fixtures/photos/${filename}`),
      }))))
    })
  }
} finally {
  s3.destroy()
  await app.close('cli')
  await container.resolve(PgPoolProvider).getPool().end()
  container.resolve(RedisProvider).getClient().disconnect()
}
