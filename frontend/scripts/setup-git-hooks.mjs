import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const frontendDirectory = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const repositoryDirectory = path.resolve(frontendDirectory, '..')
const huskyCli = path.join(frontendDirectory, 'node_modules', 'husky', 'bin.js')

process.chdir(repositoryDirectory)
execFileSync(process.execPath, [huskyCli, '.husky'], { stdio: 'inherit' })
