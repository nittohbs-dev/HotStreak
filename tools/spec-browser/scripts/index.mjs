#!/usr/bin/env node
/**
 * DesignIndexer (CLS-sb-001) + SourceScanner (CLS-sb-002)
 * REQ-sb-001 / REQ-sb-005 — reads only design-doc template headers.
 */
import fs from 'node:fs'
import path from 'node:path'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'

const require = createRequire(import.meta.url)
const yaml = require('js-yaml')

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const TOOL_ROOT = path.resolve(__dirname, '..')
const REPO_ROOT = path.resolve(TOOL_ROOT, '../..')
const DESIGN_ROOT = path.join(REPO_ROOT, 'docs/design')
const OUT_FILE = path.join(TOOL_ROOT, 'public/snapshot.json')

const SCAN_DIRS = ['frontend', 'backend', 'src']
const EXCLUDE_DIR_NAMES = new Set([
  'node_modules',
  'target',
  '.git',
  'dist',
  'build',
  'spec-browser',
])

const COL_FEATURE_MAP = ['機能ID', '名前', 'ステータス', '概要']
const COL_COMMON_CLS = ['CLS-ID', '名前', '層', '責務', '関連TBL']
const COL_FEATURE_CLS = ['CLS-ID', '共通or固有', '関連TBL']
const COL_LAYERS = ['層', 'CLS-ID', '責務', '関連API']
const COL_SCR = ['SCR-ID', '名前', 'ルート', '主な操作', '呼ぶAPI']
const COL_API = ['API-ID', 'メソッド', 'パス', '概要', '主な入力', '主な出力', '認証']

function readText(filePath) {
  if (!fs.existsSync(filePath)) return null
  return fs.readFileSync(filePath, 'utf8')
}

function parseTables(md) {
  if (!md) return []
  const lines = md.split(/\r?\n/)
  const tables = []
  let i = 0
  while (i < lines.length) {
    const line = lines[i]
    if (!line.includes('|')) {
      i += 1
      continue
    }
    const headerCells = splitRow(line)
    if (headerCells.length < 2) {
      i += 1
      continue
    }
    const next = lines[i + 1] || ''
    if (!/^\|?\s*-+/.test(next)) {
      i += 1
      continue
    }
    const rows = []
    i += 2
    while (i < lines.length && lines[i].includes('|')) {
      const cells = splitRow(lines[i])
      if (cells.length) rows.push(cells)
      i += 1
    }
    tables.push({ headers: headerCells, rows })
  }
  return tables
}

function splitRow(line) {
  const trimmed = line.trim().replace(/^\|/, '').replace(/\|$/, '')
  return trimmed.split('|').map((c) => c.trim())
}

function tableByHeaders(tables, expected) {
  return tables.find((t) => expected.every((h, idx) => t.headers[idx] === h)) || null
}

function rowsAsObjects(table) {
  if (!table) return []
  return table.rows
    .map((row) => {
      const obj = {}
      table.headers.forEach((h, i) => {
        obj[h] = row[i] ?? ''
      })
      return obj
    })
    .filter((obj) => Object.values(obj).some((v) => v && v !== '—'))
}

function extractReqSections(md) {
  if (!md) return []
  const reqs = []
  const re = /^###\s+(REQ-[^\s:]+):\s*(.+)$/gm
  let m
  while ((m = re.exec(md))) {
    const start = m.index + m[0].length
    const next = md.slice(start).search(/^###\s+/m)
    const body = (next === -1 ? md.slice(start) : md.slice(start, start + next)).trim()
    reqs.push({ id: m[1], title: m[2].trim(), body })
  }
  return reqs
}

function extractAsciiWires(md) {
  if (!md) return []
  const wires = []
  const scrRe = /^##\s+(SCR-[^\s:]+):\s*(.+)$/gm
  let m
  while ((m = scrRe.exec(md))) {
    const scrId = m[1]
    const name = m[2].trim()
    const chunkStart = m.index
    const rest = md.slice(chunkStart)
    const nextScr = rest.slice(1).search(/^##\s+SCR-/m)
    const chunk = nextScr === -1 ? rest : rest.slice(0, nextScr + 1)
    const wireMatch = chunk.match(/###\s*ワイヤー（ASCII）\s*```([\s\S]*?)```/)
    wires.push({
      id: scrId,
      name,
      wire: wireMatch ? wireMatch[1].replace(/^\n/, '') : '',
    })
  }
  return wires
}

function extractTableDefs(md) {
  if (!md) return []
  const defs = []
  const re = /^##\s+テーブル:\s*(TBL-\S+)/gm
  let m
  while ((m = re.exec(md))) {
    const id = m[1]
    const start = m.index + m[0].length
    const next = md.slice(start).search(/^##\s+/)
    const body = next === -1 ? md.slice(start) : md.slice(start, start + next)
    const tables = parseTables(body)
    const colTable = tables.find(
      (t) => t.headers[0] === 'カラム' && t.headers[1] === '型',
    )
    defs.push({
      id,
      columns: rowsAsObjects(colTable),
    })
  }
  return defs
}

function parseRelatedTbl(value) {
  if (!value) return []
  return value
    .split(/[,、\s]+/)
    .map((s) => s.trim())
    .filter((s) => /^TBL-/.test(s))
}

function ensureDir(filePath) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true })
}

function listDesignProjects() {
  if (!fs.existsSync(DESIGN_ROOT)) return []
  return fs
    .readdirSync(DESIGN_ROOT, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name)
    .filter((name) => fs.existsSync(path.join(DESIGN_ROOT, name, 'manifest.yaml')))
}

function indexProject(projectId) {
  const root = path.join(DESIGN_ROOT, projectId)
  const manifest = yaml.load(readText(path.join(root, 'manifest.yaml'))) || {}
  const featureMapMd = readText(path.join(root, '00-project/feature-map.md'))
  const commonClsMd = readText(path.join(root, '00-project/classes.md'))
  const commonDbMd = readText(path.join(root, '00-project/db.md'))

  const featureRows = rowsAsObjects(
    tableByHeaders(parseTables(featureMapMd), COL_FEATURE_MAP),
  )
  const commonClasses = rowsAsObjects(
    tableByHeaders(parseTables(commonClsMd), COL_COMMON_CLS),
  )
  const commonTables = extractTableDefs(commonDbMd)

  const nodes = []
  const edges = []
  const details = {}
  const classMeta = new Map()
  const tableMeta = new Map()
  const featureMeta = new Map()

  for (const c of commonClasses) {
    if (!c['CLS-ID'] || !/^CLS-/.test(c['CLS-ID'])) continue
    classMeta.set(c['CLS-ID'], {
      id: c['CLS-ID'],
      name: c['名前'] || c['CLS-ID'],
      layer: c['層'] || '',
      responsibility: c['責務'] || '',
      relatedTbl: parseRelatedTbl(c['関連TBL']),
      common: true,
      features: [],
      sourceHits: [],
    })
  }

  for (const t of commonTables) {
    tableMeta.set(t.id, {
      id: t.id,
      name: t.id,
      columns: t.columns,
      features: [],
      classes: [],
      sourceHits: [],
    })
  }

  const featureIds = featureRows.map((r) => r['機能ID']).filter(Boolean)
  const manifestFeatures = (manifest.features || []).map((f) => f.id)
  const allFeatureIds = [...new Set([...featureIds, ...manifestFeatures])]

  allFeatureIds.forEach((fid, featureIndex) => {
    const fdir = path.join(root, 'features', fid)
    const readme = readText(path.join(fdir, 'README.md'))
    const functional = readText(path.join(fdir, 'functional.md'))
    const screens = readText(path.join(fdir, 'screens.md'))
    const api = readText(path.join(fdir, 'api.md'))
    const layers = readText(path.join(fdir, 'layers.md'))
    const classes = readText(path.join(fdir, 'classes.md'))
    const db = readText(path.join(fdir, 'db.md'))

    const mapRow = featureRows.find((r) => r['機能ID'] === fid) || {}
    const reqs = extractReqSections(functional)
    const scrList = rowsAsObjects(tableByHeaders(parseTables(screens), COL_SCR))
    const apiList = rowsAsObjects(tableByHeaders(parseTables(api), COL_API))
    const wires = extractAsciiWires(screens)
    const layerRows = rowsAsObjects(tableByHeaders(parseTables(layers), COL_LAYERS))
    const classRows = rowsAsObjects(
      tableByHeaders(parseTables(classes), COL_FEATURE_CLS),
    )
    const featureTables = extractTableDefs(db)

    for (const t of featureTables) {
      const existing = tableMeta.get(t.id) || {
        id: t.id,
        name: t.id,
        columns: [],
        features: [],
        classes: [],
        sourceHits: [],
      }
      if (t.columns?.length) existing.columns = t.columns
      if (!existing.features.includes(fid)) existing.features.push(fid)
      tableMeta.set(t.id, existing)
    }

    const linkedCls = new Set()
    for (const row of classRows) {
      const id = row['CLS-ID']
      if (!id || !/^CLS-/.test(id)) continue
      linkedCls.add(id)
      const isCommon =
        row['共通or固有'] === '共通' || classMeta.get(id)?.common === true
      const relatedTbl = parseRelatedTbl(row['関連TBL'])
      const existing = classMeta.get(id) || {
        id,
        name: id,
        layer: '',
        responsibility: '',
        relatedTbl: [],
        common: isCommon,
        features: [],
        sourceHits: [],
      }
      existing.common = existing.common || isCommon
      existing.relatedTbl = [...new Set([...existing.relatedTbl, ...relatedTbl])]
      if (!existing.features.includes(fid)) existing.features.push(fid)
      classMeta.set(id, existing)
      for (const tbl of relatedTbl) {
        const tm = tableMeta.get(tbl) || {
          id: tbl,
          name: tbl,
          columns: [],
          features: [],
          classes: [],
          sourceHits: [],
        }
        if (!tm.features.includes(fid)) tm.features.push(fid)
        if (!tm.classes.includes(id)) tm.classes.push(id)
        tableMeta.set(tbl, tm)
      }
    }

    for (const row of layerRows) {
      const id = row['CLS-ID']
      if (!id || !/^CLS-/.test(id)) continue
      linkedCls.add(id)
      const existing = classMeta.get(id) || {
        id,
        name: id,
        layer: row['層'] || '',
        responsibility: row['責務'] || '',
        relatedTbl: [],
        common: false,
        features: [],
        sourceHits: [],
      }
      if (row['層']) existing.layer = row['層']
      if (row['責務']) existing.responsibility = row['責務']
      if (!existing.features.includes(fid)) existing.features.push(fid)
      classMeta.set(id, existing)
    }

    featureMeta.set(fid, {
      id: fid,
      name: mapRow['名前'] || fid,
      status: mapRow['ステータス'] || '',
      summary: mapRow['概要'] || '',
      readme: readme || '',
      reqs,
      screens: scrList,
      wires,
      apis: apiList,
      classIds: [...linkedCls],
      sourceHits: [],
    })

    const y = 80 + featureIndex * 160
    nodes.push({
      id: `feature:${fid}`,
      type: 'feature',
      position: { x: 40, y },
      data: {
        kind: 'Feature',
        label: mapRow['名前'] || fid,
        subLabel: fid,
        reqCount: reqs.length,
        implemented: false,
      },
    })

    for (const clsId of linkedCls) {
      edges.push({
        id: `e:${fid}->${clsId}`,
        source: `feature:${fid}`,
        target: `class:${clsId}`,
        type: 'default',
      })
    }
  })

  let classIndex = 0
  for (const [clsId, meta] of classMeta) {
    const y = 60 + classIndex * 120
    nodes.push({
      id: `class:${clsId}`,
      type: meta.common ? 'classCommon' : 'classFeature',
      position: { x: 360, y },
      data: {
        kind: meta.common ? 'ClassCommon' : 'ClassFeature',
        label: meta.name,
        subLabel: clsId,
        layer: meta.layer,
        featureIds: meta.features,
        implemented: false,
      },
    })
    for (const tbl of meta.relatedTbl) {
      if (!tableMeta.has(tbl)) {
        tableMeta.set(tbl, {
          id: tbl,
          name: tbl,
          columns: [],
          features: [...meta.features],
          classes: [clsId],
          sourceHits: [],
        })
      } else {
        const tm = tableMeta.get(tbl)
        if (!tm.classes.includes(clsId)) tm.classes.push(clsId)
      }
      edges.push({
        id: `e:${clsId}->${tbl}`,
        source: `class:${clsId}`,
        target: `table:${tbl}`,
        type: 'default',
      })
    }
    details[`class:${clsId}`] = meta
    classIndex += 1
  }

  let tableIndex = 0
  for (const [tblId, meta] of tableMeta) {
    nodes.push({
      id: `table:${tblId}`,
      type: 'table',
      position: { x: 700, y: 60 + tableIndex * 120 },
      data: {
        kind: 'Table',
        label: meta.name,
        subLabel: tblId,
        implemented: false,
      },
    })
    details[`table:${tblId}`] = meta
    tableIndex += 1
  }

  for (const [fid, meta] of featureMeta) {
    details[`feature:${fid}`] = meta
  }

  return {
    projectId,
    title: manifest.title || projectId,
    status: manifest.status || 'draft',
    nodes,
    edges,
    details,
    classMeta,
    tableMeta,
    featureMeta,
  }
}

function shouldSkipDir(name) {
  return EXCLUDE_DIR_NAMES.has(name) || name.startsWith('.')
}

function walkFiles(dir, out = []) {
  if (!fs.existsSync(dir)) return out
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.isDirectory()) {
      if (shouldSkipDir(entry.name)) continue
      walkFiles(path.join(dir, entry.name), out)
    } else if (/\.(java|ts|tsx|js|jsx|kt|sql)$/.test(entry.name)) {
      out.push(path.join(dir, entry.name))
    }
  }
  return out
}

function scanSources(indexed) {
  const files = []
  for (const d of SCAN_DIRS) {
    walkFiles(path.join(REPO_ROOT, d), files)
  }
  // also allow tools excluded already via name

  const contentByFile = files.map((f) => ({
    file: path.relative(REPO_ROOT, f).replace(/\\/g, '/'),
    text: fs.readFileSync(f, 'utf8'),
  }))

  let gapCount = 0

  for (const project of indexed) {
    for (const [fid, meta] of project.featureMeta) {
      const hits = []
      for (const req of meta.reqs) {
        for (const { file, text } of contentByFile) {
          if (text.includes(req.id)) hits.push({ id: req.id, file })
        }
      }
      for (const { file, text } of contentByFile) {
        if (text.includes(fid) || text.includes(`feature:${fid}`)) {
          hits.push({ id: fid, file })
        }
      }
      meta.sourceHits = uniqueHits(hits)
      const node = project.nodes.find((n) => n.id === `feature:${fid}`)
      if (node) node.data.implemented = meta.sourceHits.length > 0
      if (meta.reqs.length && meta.sourceHits.length === 0) gapCount += 1
      project.details[`feature:${fid}`] = meta
    }

    for (const [clsId, meta] of project.classMeta) {
      const hits = []
      for (const { file, text } of contentByFile) {
        if (text.includes(clsId)) hits.push({ id: clsId, file })
        if (meta.name && meta.name !== clsId && text.includes(meta.name)) {
          hits.push({ id: meta.name, file })
        }
      }
      meta.sourceHits = uniqueHits(hits)
      const node = project.nodes.find((n) => n.id === `class:${clsId}`)
      if (node) node.data.implemented = meta.sourceHits.length > 0
      if (meta.sourceHits.length === 0) gapCount += 1
      project.details[`class:${clsId}`] = meta
    }

    for (const [tblId, meta] of project.tableMeta) {
      const hits = []
      for (const { file, text } of contentByFile) {
        if (text.includes(tblId)) hits.push({ id: tblId, file })
        if (text.includes(`@Table`) && text.includes(tblId.replace(/^TBL-/, ''))) {
          hits.push({ id: tblId, file })
        }
      }
      meta.sourceHits = uniqueHits(hits)
      const node = project.nodes.find((n) => n.id === `table:${tblId}`)
      if (node) node.data.implemented = meta.sourceHits.length > 0
      if (meta.sourceHits.length === 0) gapCount += 1
      project.details[`table:${tblId}`] = meta
    }
  }

  return { gapCount, scannedFileCount: contentByFile.length }
}

function uniqueHits(hits) {
  const seen = new Set()
  return hits.filter((h) => {
    const key = `${h.id}:${h.file}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

function buildEmptySnapshot() {
  return {
    generatedAt: new Date().toISOString(),
    empty: true,
    gapCount: 0,
    scannedFileCount: 0,
    projects: [],
    nodes: [
      {
        id: 'placeholder',
        type: 'feature',
        position: { x: 200, y: 160 },
        data: {
          kind: 'Feature',
          label: 'まだ docs/design がありません',
          subLabel: '次: design-doc スキルで設計書を置く',
          reqCount: 0,
          implemented: false,
          placeholder: true,
        },
      },
    ],
    edges: [],
    details: {
      placeholder: {
        id: 'placeholder',
        name: '空状態',
        reqs: [],
        screens: [],
        wires: [],
        apis: [],
        sourceHits: [],
      },
    },
  }
}

function main() {
  const projects = listDesignProjects()
  if (!projects.length) {
    ensureDir(OUT_FILE)
    fs.writeFileSync(OUT_FILE, JSON.stringify(buildEmptySnapshot(), null, 2))
    console.log(`Wrote empty snapshot to ${OUT_FILE}`)
    return
  }

  const indexed = projects.map(indexProject)
  const scan = scanSources(indexed)

  const nodes = []
  const edges = []
  const details = {}
  const projectSummaries = []

  indexed.forEach((p, pi) => {
    const xOffset = pi * 980
    for (const n of p.nodes) {
      nodes.push({
        ...n,
        position: { x: n.position.x + xOffset, y: n.position.y },
      })
    }
    edges.push(...p.edges)
    Object.assign(details, p.details)
    projectSummaries.push({
      id: p.projectId,
      title: p.title,
      status: p.status,
      featureCount: p.featureMeta.size,
      classCount: p.classMeta.size,
      tableCount: p.tableMeta.size,
    })
  })

  // dedupe edges
  const edgeSeen = new Set()
  const uniqueEdges = edges.filter((e) => {
    if (edgeSeen.has(e.id)) return false
    edgeSeen.add(e.id)
    return true
  })

  const snapshot = {
    generatedAt: new Date().toISOString(),
    empty: false,
    gapCount: scan.gapCount,
    scannedFileCount: scan.scannedFileCount,
    projects: projectSummaries,
    nodes,
    edges: uniqueEdges,
    details,
  }

  ensureDir(OUT_FILE)
  fs.writeFileSync(OUT_FILE, JSON.stringify(snapshot, null, 2))
  console.log(
    `Wrote snapshot: ${nodes.length} nodes, ${uniqueEdges.length} edges, gaps=${scan.gapCount} -> ${OUT_FILE}`,
  )
}

main()
