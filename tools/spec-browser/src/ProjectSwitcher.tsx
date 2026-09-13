import type { ProjectSummary } from './types'

type Props = {
  projects: ProjectSummary[]
  value: string | null
  onChange: (projectId: string) => void
}

export function ProjectSwitcher({ projects, value, onChange }: Props) {
  if (!projects.length) return null
  return (
    <label className="project-switcher">
      <span className="sr-only">設計プロジェクト</span>
      <select
        value={value ?? projects[0]?.id ?? ''}
        onChange={(e) => onChange(e.target.value)}
        aria-label="設計プロジェクト"
      >
        {projects.map((p) => (
          <option key={p.id} value={p.id}>
            {p.title || p.id}
          </option>
        ))}
      </select>
    </label>
  )
}
