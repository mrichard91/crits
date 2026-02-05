import { useState } from 'react'
import { Hash, Copy, Check } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui'

interface HashEntry {
  label: string
  value: string
}

interface SampleHashCardProps {
  md5?: string
  sha1?: string
  sha256?: string
  ssdeep?: string
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <button
      onClick={handleCopy}
      className="p-1 rounded hover:bg-light-hover dark:hover:bg-dark-hover text-light-text-muted dark:text-dark-text-muted"
      title="Copy to clipboard"
    >
      {copied ? (
        <Check className="h-3.5 w-3.5 text-status-success" />
      ) : (
        <Copy className="h-3.5 w-3.5" />
      )}
    </button>
  )
}

export function SampleHashCard({ md5, sha1, sha256, ssdeep }: SampleHashCardProps) {
  const hashes: HashEntry[] = [
    { label: 'MD5', value: md5 ?? '' },
    { label: 'SHA1', value: sha1 ?? '' },
    { label: 'SHA256', value: sha256 ?? '' },
    { label: 'SSDeep', value: ssdeep ?? '' },
  ].filter((h) => h.value)

  if (hashes.length === 0) return null

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Hash className="h-5 w-5" />
          Hashes
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {hashes.map((h) => (
            <div key={h.label}>
              <div className="text-xs font-medium text-light-text-muted dark:text-dark-text-muted mb-0.5">
                {h.label}
              </div>
              <div className="flex items-center gap-1">
                <span className="font-mono text-sm break-all text-light-text dark:text-dark-text">
                  {h.value}
                </span>
                <CopyButton text={h.value} />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
